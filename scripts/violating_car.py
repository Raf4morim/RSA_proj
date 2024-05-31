import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
import csv
import sqlite3 as sql

# Function to update coordinates in the database
def update_coordinates(id, latitude, longitude):
    db = sql.connect('../obu.db')
    cursor = db.cursor()
    cursor.execute("UPDATE obu SET lat = ?, long = ? WHERE stationID = ?", (latitude, longitude, id))
    db.commit()
    db.close()

# Ler coordenadas do ficheiro CSV
def read_coordinates(csv_file):
    coordinates = []
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            coordinates.append((float(row['latitude']), float(row['longitude'])))
    return coordinates

violating_car_coordinates = read_coordinates('violatingCarCoordinates.csv')
idx = 0

# Get coordinates and car goes behind ambulance
# Publishes CAMs and subscribes to DENMs
def on_connect(client, userdata, flags, rc, properties):
    print("Connected with result code "+str(rc))
    #client.subscribe("vanetza/out/cam")
    client.subscribe("vanetza/out/denm")
    client.subscribe("vanetza/in/cam")
    # ...


# É chamada automaticamente sempre que recebe uma mensagem nos tópicos subscritos em cima
def on_message(client, userdata, msg):
    message = msg.payload.decode('utf-8')
    obj = json.loads(message)

    if "latitude" in obj and "longitude" in obj and "heading" in obj:
        car_lat = obj["latitude"]
        car_lon = obj["longitude"]
        car_stationID = obj["stationID"]
        update_coordinates(car_stationID, car_lat, car_lon)

    if "fields" in obj and "denm" in obj["fields"]:
        if obj["fields"]["denm"]["situation"]["eventType"]["causeCode"] == 99:
            print('CAR VIOLATION ALERT RECEIVED! DENM')
    
    # print('Topic: ' + msg.topic)
    # print('Message' + message)

    # obj = json.loads(message)

    # lat = obj["latitude"]
    # lon = obj["longitude"]

    # print('Latitude: ' + str(lat))
    # print('Longitude: ' + str(lon))


# Generate CAMs with coordinates in violatingCarCoordinates.csv
def generate():
    global idx
    if idx >= len(violating_car_coordinates):
        idx = 0 # Reset index

    latitude, longitude = violating_car_coordinates[idx]
    idx += 1

    f = open('in_cam.json')
    m = json.load(f)
    m["latitude"] = latitude
    m["longitude"] = longitude

    m = json.dumps(m)
    client.publish("vanetza/in/cam",m)
    f.close()
    sleep(0.5)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect("192.168.98.10", 1883, 60)

threading.Thread(target=client.loop_forever).start()

while(True):
    generate()
