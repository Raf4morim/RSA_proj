import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
import csv
import math

# Ler coordenadas do ficheiro CSV
def read_coordinates(csv_file):
    coordinates = []
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            coordinates.append((float(row['latitude']), float(row['longitude'])))
    return coordinates

emergency_vehicle_coordinates = read_coordinates('emergencyVehicleCoordinates.csv')
idx = 0
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


def on_connect(client, userdata, flags, rc, properties):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/cam")

# Obter coordenadas nas mensagens CAM
def on_message(client, userdata, msg):
    global idx, violation_count

    message = msg.payload.decode('utf-8')
    #print('Topic: ' + msg.topic)
    #print('Message' + message)
    obj = json.loads(message)

    other_car_lat = obj["latitude"]
    other_car_lon = obj["longitude"]

    print('Received CAM with coordinates: ' + str(other_car_lat) + ', ' + str(other_car_lon))

    # Obter coordenadas do veículo de emergência (como se fosse por GPS)
    if idx >= len(emergency_vehicle_coordinates):
        idx = 0 # Reset index

    ambulance_lat, ambulance_lon = emergency_vehicle_coordinates[idx]
    idx += 1

    # Comparar coordenadas recebidas com coordenadas do ficheiro CSV
    distance = haversine_distance(other_car_lat, other_car_lon, ambulance_lat, ambulance_lon)
    print('Distance: ' + str(distance) + ' km')

    if distance < distance_threshold:
        violation_count += 1
    else:
        violation_count = 0
    
    if violation_count >= 10:
        # TODO - Modify DENM message

        print('Violation detected! Sending DENM...')
        f = open('in_denm.json')
        violation_alert = json.load(f)
        violation_alert["latitude"] = other_car_lat
        violation_alert["longitude"] = other_car_lon
        violation_alert = json.dumps(violation_alert)
        client.publish("vanetza/in/denm", violation_alert)
        f.close()
        violation_count = 0

    f = open('in_denm.json')
    




client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect("192.168.98.20", 1883, 60)

threading.Thread(target=client.loop_forever).start()



