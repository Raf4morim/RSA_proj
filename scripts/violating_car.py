import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
import csv

open("violating_car_log.txt", "w").close()
other_cars_log_file = open("violating_car_log.txt", "a")

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

violating_car_coordinates = read_coordinates('violatingCarCoordinates.csv')
idx = 0

# Get coordinates and car goes behind ambulance
# Publishes CAMs and subscribes to DENMs
def on_connect(client, userdata, flags, rc, properties):
    print("Connected with result code "+str(rc))
    #client.subscribe("vanetza/out/cam")
    client.subscribe("vanetza/out/denm")
    # ...


# É chamada automaticamente sempre que recebe uma mensagem nos tópicos subscritos em cima
def on_message(client, userdata, msg):
    message = msg.payload.decode('utf-8')
    obj = json.loads(message)

    if obj["fields"]["denm"]["situation"]["eventType"]["causeCode"] == 99:
        log_message = 'Received DENM alert because of violation!'
        log_to_file(other_cars_log_file, log_message)
    
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

    log_message = 'Publishing CAM with coordinates: ' + str(latitude) + ', ' + str(longitude)
    log_to_file(other_cars_log_file, log_message)

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
