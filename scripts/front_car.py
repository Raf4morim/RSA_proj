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

front_car_coordinates = read_coordinates('carInFrontCoordinates.csv')
idx = 0

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
def is_behind(car_lat, car_lon, car_heading, other_car_lat, other_car_lon):
    bearing_to_other = calculate_bearing(car_lat, car_lon, other_car_lat, other_car_lon)
    #print('Bearing to car: ' + str(bearing_to_car))
    angle_diff = (bearing_to_other - car_heading + 360) % 360
    # Consider the car in front if it is within ±90 degrees of the ambulance's heading
    return 90 < angle_diff < 270

def on_connect(client, userdata, flags, rc, properties):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/denm")

def on_message(client, userdata, msg):
    #log_message = 'Received DENM alert to swerve away!'
    #log_to_file(other_cars_log_file, log_message)

    message = msg.payload.decode('utf-8')
    obj = json.loads(message)

    # if the car is in front of the ambulance must check

    if obj["fields"]["denm"]["situation"]["eventType"]["causeCode"] == 95:
        log_message = 'Received DENM alert to swerve away!'
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
