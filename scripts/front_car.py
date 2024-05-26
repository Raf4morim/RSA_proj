import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
import csv
import math

open("front_car_log.txt", "w").close()
other_cars_log_file = open("front_car_log.txt", "a")

def log_to_file(log_file, message):
    log_file.write(message + '\n')
    log_file.flush()  # Ensure that the message is written immediately

# Ler coordenadas do ficheiro CSV
def read_coordinates(csv_file):
    coordinates = []
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            coordinates.append((float(row['latitude']), float(row['longitude'])))
    return coordinates

# TODO - Modify to have all 4 possible cases of coordinates
front_car_coordinates = read_coordinates('carInFrontCoordinates.csv')
# front_car_coordinates = read_coordinates('carInBack.csv')
#front_car_coordinates = read_coordinates('carOppositeCoordinates.csv')
idx = 0
amb_lat, amb_lon, amb_heading = None, None, None
car_lat, car_lon, car_heading = None, None, None

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

# Determine the car's position relative to the ambulance
def determine_position(ambulance_lat, ambulance_lon, car_lat, car_lon, car_heading):
    bearing_to_ambulance = calculate_bearing(car_lat, car_lon, ambulance_lat, ambulance_lon)
    angle_diff = (bearing_to_ambulance - car_heading + 360) % 360
    distance = haversine_distance(car_lat, car_lon, ambulance_lat, ambulance_lon)

    #print('Heading: ' + str(car_heading))
    if distance < 0.1:  # Ignore if the distance is less than 100 meters to avoid close proximity errors
        return None

    print('Angle diff: ' + str(angle_diff))
    print('Bearing to ambulance: ' + str(bearing_to_ambulance))
    if angle_diff <= 90 or angle_diff >= 270:
        if bearing_to_ambulance <= 90 or bearing_to_ambulance >= 270:
            return "Car on the same lane but behind the ambulance"
        else:
            return "Car on the opposite lane in front"
    else:
        if bearing_to_ambulance <= 90 or bearing_to_ambulance >= 270:
            return "Car on the opposite lane but already past the ambulance"
        else:
            return "Car on the same lane but in front"
        

# Determine if the other car is in front of the ambulance
def is_behind(car_lat, car_lon, car_heading, other_car_lat, other_car_lon):
    bearing_to_other = calculate_bearing(car_lat, car_lon, other_car_lat, other_car_lon)
    #print('Bearing to car: ' + str(bearing_to_car))
    angle_diff = (bearing_to_other - car_heading + 360) % 360
    # Consider the car in front if it is within ±90 degrees of the ambulance's heading
    return 90 < angle_diff < 270

def on_connect(client, userdata, flags, rc, properties):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/in/cam")
    client.subscribe("vanetza/out/cam")
    client.subscribe("vanetza/out/denm")
    
def on_message(client, userdata, msg):
    global amb_lat, amb_lon, amb_heading, car_lat, car_lon, car_heading
    #log_message = 'Received DENM alert to swerve away!'
    #log_to_file(other_cars_log_file, log_message)

    # Receive CAMs and DENMs from the ambulance 
    # 1. If special vehicle is emergency container with light bar siren in use, then extract coordinates and heading
    # 2. Check with DENMs if the event type has cause code 95
    # 3. If cause code is 95, realize algorithm with previous coordinates and heading to determine if the car has to swerve away

    message = msg.payload.decode('utf-8')
    obj = json.loads(message)

    if "latitude" in obj and "longitude" in obj and "heading" in obj:
        if obj["stationID"] == 3:
            print("Received CAM from station 3")
            car_lat = obj["latitude"]
            car_lon = obj["longitude"]
            car_heading = obj["heading"]

    # Start by analysing CAMs
    if "specialVehicle" in obj and "emergencyContainer" in obj["specialVehicle"]:
        if obj["specialVehicle"]["emergencyContainer"]["lightBarSirenInUse"]["lightBarActivated"] == True:
            print("Received CAM from emergency container with light bar siren in use")
            amb_lat = obj["latitude"]
            amb_lon = obj["longitude"]
            amb_heading = obj["heading"]


    if "fields" in obj and "denm" in obj["fields"]:
        #print("Received DENM")
        if obj["fields"]["denm"]["situation"]["eventType"]["causeCode"] == 95:
            #log_message = 'Received DENM alert to swerve away!'
            #log_to_file(other_cars_log_file, log_message)

            if amb_lat is not None and amb_lon is not None and amb_heading is not None and car_lat is not None and car_lon is not None and car_heading is not None:
                #distance = haversine_distance(amb_lat, amb_lon, car_lat, car_lon)
                #print('Distance: ' + str(distance) + ' km')
                position = determine_position(amb_lat, amb_lon, car_lat, car_lon, car_heading)
                log_message = f'Position: {position}'
                log_to_file(other_cars_log_file, log_message)
                if position in ["Car on the same lane but in front", "Car on the opposite lane in front"]:
                    log_message = 'Car should react!'
                    log_to_file(other_cars_log_file, log_message)

# Generate CAMs with coordinates in violatingCarCoordinates.csv
def generate():
    global idx
    if idx >= len(front_car_coordinates):
        idx = 0 # Reset index

    latitude, longitude = front_car_coordinates[idx]
    idx += 1

    f = open('in_cam.json')
    m = json.load(f)
    m["latitude"] = latitude
    m["longitude"] = longitude
    m["stationID"] = 3
    #m["heading"] = 180

    log_message = 'Publishing CAM with coordinates: ' + str(latitude) + ', ' + str(longitude)
    log_to_file(other_cars_log_file, log_message)

    m = json.dumps(m)
    client.publish("vanetza/in/cam",m)
    f.close()
    sleep(0.5)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect("192.168.98.30", 1883, 60)

threading.Thread(target=client.loop_forever).start()

while(True):
    generate()