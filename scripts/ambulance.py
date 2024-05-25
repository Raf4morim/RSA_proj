import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
import csv
import math

open("ambulance_log.txt", "w").close()
ambulance_log_file = open("ambulance_log.txt", "a")

def log_to_file(log_file, message):
    log_file.write(message + '\n')
    log_file.flush()  # Ensure that the message is written immediately

# Read coordinates
def read_coordinates(csv_file):
    coordinates = []
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            coordinates.append((float(row['latitude']), float(row['longitude'])))
    return coordinates

emergency_vehicle_coordinates = read_coordinates('emergencyVehicleCoordinates.csv')
idx = 0

ambulance_coordinates = None
other_car_coordinates = None
previous_ambulance_coordinates = None
previous_ambulance_heading = 0
ambulance_heading = 0

violation_count = 0
distance_threshold = 0.005  # 5 meters


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



def on_connect(client, userdata, flags, rc, properties):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/cam") # Will receive CAMs from other cars
    client.subscribe("vanetza/in/cam") # Will receive own CAMs from the ambulance

# Obter coordenadas nas mensagens CAM
def on_message(client, userdata, msg):
    global ambulance_heading, ambulance_coordinates, other_car_coordinates, idx, violation_count, previous_ambulance_coordinates, previous_ambulance_heading

    message = msg.payload.decode('utf-8')
    obj = json.loads(message)

    lat = obj["latitude"]
    lon = obj["longitude"]
    stationID = obj["stationID"]

    #print('Received CAM from station ' + str(stationID) + ' with coordinates: ' + str(lat) + ', ' + str(lon))
    log_message = 'Received CAM from station ' + str(stationID) + ' with coordinates: ' + str(lat) + ', ' + str(lon)
    log_to_file(ambulance_log_file, log_message)

    # Station 2 is the ambulance
    if stationID == 2:
        ambulance_coordinates = (lat, lon)
        # Calculate bearing comparing current coordinates with previous coordinates
        if previous_ambulance_coordinates is not None:
            ambulance_heading = calculate_bearing(previous_ambulance_coordinates[0],previous_ambulance_coordinates[1],lat,lon)
            previous_ambulance_heading = ambulance_heading
        else:
            ambulance_heading = previous_ambulance_heading
        previous_ambulance_coordinates = (lat,lon)

    else:
        other_car_coordinates = (lat, lon)

        if ambulance_coordinates is not None and other_car_coordinates is not None:
            if is_in_front(ambulance_coordinates[0], ambulance_coordinates[1], ambulance_heading, other_car_coordinates[0], other_car_coordinates[1]):
                distance = haversine_distance(other_car_coordinates[0], other_car_coordinates[1], ambulance_coordinates[0], ambulance_coordinates[1])
                
                log_message = 'CAR IN FRONT Distance: ' + str(distance) + ' km'
                log_to_file(ambulance_log_file, log_message)

                if distance < 0.2: # 200 meters
                    log_message = 'Car in front is within 200 meters! Sending DENM...'
                    log_to_file(ambulance_log_file, log_message)
                    f = open('in_denm.json')
                    swerve_alert = json.load(f)
                    swerve_alert["latitude"] = ambulance_coordinates[0]
                    swerve_alert["longitude"] = ambulance_coordinates[1]
                    swerve_alert = json.dumps(swerve_alert)

                    # TODO - get station ID from the front cars
                    # TODO - if for this station ID, the alert has already been sent, don't send it again

                    client.publish("vanetza/in/denm",swerve_alert)
                    f.close()

            else:
                # Comparar coordenadas recebidas com coordenadas do ficheiro CSV
                distance = haversine_distance(other_car_coordinates[0], other_car_coordinates[1], ambulance_coordinates[0], ambulance_coordinates[1])
                
                log_message = 'CAR BEHIND Distance: ' + str(distance) + ' km'
                log_to_file(ambulance_log_file, log_message)

                if distance < distance_threshold:
                    violation_count += 1
                else:
                    violation_count = 0
                
                if violation_count >= 10:
                    # TODO - Modify DENM message

                    log_message = 'Violation detected; Car following! Sending DENM...'
                    log_to_file(ambulance_log_file, log_message)

                    f = open('in_denm.json')
                    violation_alert = json.load(f)
                    violation_alert["latitude"] = ambulance_coordinates[0]
                    violation_alert["longitude"] = ambulance_coordinates[1]
                    violation_alert = json.dumps(violation_alert)
                    client.publish("vanetza/in/denm", violation_alert)
                    f.close()
                    violation_count = 0

# Generate CAMs with coordinates in emergencyVehicleCoordinates.csv
def generate():
    global idx
    if idx >= len(emergency_vehicle_coordinates):
        idx = 0 # Reset index

    latitude, longitude = emergency_vehicle_coordinates[idx]
    idx += 1

    f = open('in_cam_ambulance.json')
    m = json.load(f)
    m["latitude"] = latitude
    m["longitude"] = longitude

    log_message = 'Ambulance publishing CAM with coordinates: ' + str(latitude) + ', ' + str(longitude)
    log_to_file(ambulance_log_file, log_message)

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