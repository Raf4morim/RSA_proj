import json
import paho.mqtt.client as mqtt
import threading
import sqlite3 as sql
from time import sleep
import csv
import math
    
violation_count = {}

# Function to update coordinates in the database
def update_violations(violation_type, id):
    db = sql.connect('../obu.db')
    cursor = db.cursor()
    cursor.execute("UPDATE violations SET violation_type = ? WHERE stationID = ?", (violation_type, id))
    db.commit()
    db.close()

# Ler coordenadas do ficheiro CSV
def read_coordinates_and_heading(csv_file):
    coordinates = []
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            coordinates.append((float(row['latitude']), float(row['longitude']), float(row['heading'])))
    return coordinates

emergency_vehicle_coordinates = read_coordinates_and_heading('emergencyVehicleCoordinates.csv')
idx = 0

ambulance_coordinates = None
other_car_coordinates = None
previous_ambulance_coordinates = None
ambulance_heading = 0

# violation_count = 0
distance_threshold = 0.012  # 12 meters


def haversine_distance(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in kilometers. Use 3956 for miles. Determines return value units.
    r = 6371.0
    
    # Calculate the result
    distance = c * r
    return distance

def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    return bearing

# Determine if the other car is in front of the ambulance
def is_in_front(ambulance_lat, ambulance_lon, ambulance_heading, other_car_lat, other_car_lon):
    bearing_to_car = calculate_bearing(ambulance_lat, ambulance_lon, other_car_lat, other_car_lon)
    #print('Bearing to car: ' + str(bearing_to_car))
    angle_diff = (bearing_to_car - ambulance_heading + 360) % 360
    # Consider the car in front if it is within ±90 degrees of the ambulance's heading
    return angle_diff <= 90 or angle_diff >= 270

# Determine if the other car is behind of the ambulance
def is_behind(car_lat, car_lon, car_heading, other_car_lat, other_car_lon):
    bearing_to_other = calculate_bearing(car_lat, car_lon, other_car_lat, other_car_lon)
    #print('Bearing to car: ' + str(bearing_to_car))
    angle_diff = (bearing_to_other - car_heading + 360) % 360
    # Consider the car in front if it is within ±90 degrees of the ambulance's heading
    return 90 < angle_diff < 270

def on_connect(client, userdata, flags, rc, properties):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/cam") # Will receive CAMs from other cars
    client.subscribe("vanetza/in/cam") # Will receive own CAMs from the ambulance

# Obter coordenadas nas mensagens CAM
def on_message(client, userdata, msg):
    global ambulance_heading, ambulance_coordinates, other_car_coordinates, idx, violation_count, previous_ambulance_coordinates

    message = msg.payload.decode('utf-8')
    obj = json.loads(message)

    lat = obj["latitude"]
    lon = obj["longitude"]
    stationID = obj["stationID"]
    heading = obj["heading"]

    #print('Received CAM from station ' + str(stationID) + ' with coordinates: ' + str(lat) + ', ' + str(lon))


    # Station 2 is the ambulance
    if stationID == 2:
        ambulance_coordinates = (lat, lon)
        ambulance_heading = heading
    else:
        other_car_coordinates = (lat, lon)

        if ambulance_coordinates is not None and other_car_coordinates is not None:
            #if is_in_front(ambulance_coordinates[0], ambulance_coordinates[1], ambulance_heading, other_car_coordinates[0], other_car_coordinates[1]):
            #distance = haversine_distance(other_car_coordinates[0], other_car_coordinates[1], ambulance_coordinates[0], ambulance_coordinates[1])

            #if distance < 0.4: # 200 meters


            f = open('in_denm_ambulance.json')
            swerve_alert = json.load(f)
            swerve_alert["management"]["eventPosition"]["latitude"] = ambulance_coordinates[0]
            swerve_alert["management"]["eventPosition"]["longitude"] = ambulance_coordinates[1]
            swerve_alert = json.dumps(swerve_alert)

            # TODO - get station ID from the front cars
            # TODO - if for this station ID, the alert has already been sent, don't send it again

            client.publish("vanetza/in/denm",swerve_alert)
            f.close()

            if is_behind(ambulance_coordinates[0], ambulance_coordinates[1], ambulance_heading, other_car_coordinates[0], other_car_coordinates[1]):
                # Comparar coordenadas recebidas com coordenadas do ficheiro CSV
                distance = haversine_distance(other_car_coordinates[0], other_car_coordinates[1], ambulance_coordinates[0], ambulance_coordinates[1])

                if distance < distance_threshold:
                    if stationID not in violation_count:
                        violation_count[stationID] = 0
                    violation_count[stationID] += 1
                else:
                    if stationID in violation_count:
                        del violation_count[stationID]
                
                
                if stationID in violation_count:
                    print("vvvvvvv ",violation_count)
                    update_violations(None, stationID)
                    if violation_count[stationID] >= 20:
                        update_violations(f"Car {stationID} behind the ambulance", stationID)

                        f = open('in_denm_ambulance2.json')
                        violation_alert = json.load(f)
                        violation_alert["latitude"] = ambulance_coordinates[0]
                        violation_alert["longitude"] = ambulance_coordinates[1]
                        violation_alert = json.dumps(violation_alert)
                        client.publish("vanetza/in/denm", violation_alert)
                        f.close()
                        del violation_count[stationID]
                    
                

# Generate CAMs with coordinates in emergencyVehicleCoordinates.csv
def generate():
    global idx
    if idx >= len(emergency_vehicle_coordinates):
        idx = 0 # Reset index

    latitude, longitude, heading = emergency_vehicle_coordinates[idx]
    idx += 1

    f = open('in_cam_ambulance.json')
    m = json.load(f)
    m["latitude"] = latitude
    m["longitude"] = longitude
    m["heading"] = heading

    m = json.dumps(m)
    client.publish("vanetza/in/cam",m)
    f.close()
    sleep(0.5)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect("192.168.98.20", 1883, 60)

threading.Thread(target=client.loop_forever).start()

while True:
    generate()