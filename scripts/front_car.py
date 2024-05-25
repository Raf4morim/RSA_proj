import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
import csv

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


def on_connect(client, userdata, flags, rc, properties):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/denm")


def on_message(client, userdata, msg):
    print('Received DENM alert to swerve away!')

    message = msg.payload.decode('utf-8')
    


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

    print('Publishing CAM with coordinates: ' + str(latitude) + ', ' + str(longitude))

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
