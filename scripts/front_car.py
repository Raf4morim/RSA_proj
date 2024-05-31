import sqlite3 as sql
import json
import paho.mqtt.client as mqtt
import math
import threading
from time import sleep
import csv
import sys
import os
from flask_socketio import SocketIO

sys.path.append('..')
from app import notify_car_reaction

# Ler coordenadas do ficheiro CSV
def read_coordinates(csv_file):
    coordinates = []
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            coordinates.append((float(row['latitude']), float(row['longitude'])))
    return coordinates

def update_frontCarMessage(swerve_type, ip):
    db = sql.connect('../obu.db')
    cursor = db.cursor()
    cursor.execute("UPDATE swerve SET swerve_type = ? WHERE ip = ?", (swerve_type, ip))
    db.commit()
    db.close()

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

    #print('Angle diff: ' + str(angle_diff))
    #print('Bearing to ambulance: ' + str(bearing_to_ambulance))
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


# Function to update coordinates in the database
def update_coordinates(ip, latitude, longitude):
    db = sql.connect('../obu.db')
    cursor = db.cursor()
    cursor.execute("UPDATE obu SET lat = ?, long = ? WHERE ip = ?", (latitude, longitude, ip))
    db.commit()
    db.close()

def on_message(client, userdata, msg):
    global amb_lat, amb_lon, amb_heading, car_lat, car_lon, car_heading
    message = msg.payload.decode('utf-8')
    obj = json.loads(message)
    if "latitude" in obj and "longitude" in obj and "heading" in obj:
        if obj["stationID"] == 3:
            #print("Received CAM from station 3")
            car_lat = obj["latitude"]
            car_lon = obj["longitude"]
            car_heading = obj["heading"]
            update_coordinates("192.168.98.30", car_lat, car_lon)

    if "specialVehicle" in obj and "emergencyContainer" in obj["specialVehicle"]:
        if obj["specialVehicle"]["emergencyContainer"]["lightBarSirenInUse"]["lightBarActivated"] == True:
            #print("Received CAM from emergency container with light bar siren in use")
            amb_lat = obj["latitude"]
            amb_lon = obj["longitude"]
            amb_heading = obj["heading"]
            update_coordinates("192.168.98.20", amb_lat, amb_lon)

    if "fields" in obj and "denm" in obj["fields"]:
        if obj["fields"]["denm"]["situation"]["eventType"]["causeCode"] == 95:
            if amb_lat is not None and amb_lon is not None and amb_heading is not None and car_lat is not None and car_lon is not None and car_heading is not None:
                position = determine_position(amb_lat, amb_lon, car_lat, car_lon, car_heading)
                if position in ["Car on the same lane but in front", "Car on the opposite lane in front"]:
                    #print('CAR SHOULD REACT')
                    update_frontCarMessage("Car 3 in front of ambulance swerve", "192.168.98.30")
                    notify_car_reaction()
                else:
                    update_frontCarMessage("Not in front", "192.168.98.30")
                    
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
