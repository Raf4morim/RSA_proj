from geopy import Point
from geopy.distance import geodesic
import csv

# This script generates a list of coordinates for two cars to simulate a scenario where one car is behind the other.
# CAMs are published each 0.5 seconds

def generate_coordinates(starting_point, speed, time_interval, num_points, bearing):
    distance = (speed * time_interval) / 3600 # Convert speed from km/h to distance in kilometers

    points = [starting_point]
    for _ in range(num_points - 1):
        # geodesic(distance).destination(point, bearing, distance=None)
        next_point = geodesic(kilometers=distance).destination(points[-1], bearing)
        points.append(next_point)
    return points

starting_points = [
    Point(40.748817, -73.985428),  # ambulance
    Point(40.74872694970647,-73.985428),  # violating car (10 meters behind the ambulance)
    Point(40.75241901058529,-73.985428),  # car in front (400 meters ahead)
    Point(40.746989, -73.985428),  # car in back (300 meters behind the ambulance)
    Point(40.751645, -73.985428)   # car coming from opposite direction (300 meters ahead)
]

bearings = [0, 0, 0, 0, 180]

speeds = [70, 70, 40, 70, 40]

num_points = 100  
messsage_interval = 0.5

# Generate coordinates 
emergency_vehicle_coordinates = generate_coordinates(starting_points[0], speeds[0], messsage_interval, num_points, bearings[0])
violating_car_coordinates = generate_coordinates(starting_points[1], speeds[1], messsage_interval, num_points, bearings[1])
car_in_front_coordinates = generate_coordinates(starting_points[2], speeds[2], messsage_interval, num_points, bearings[2])
car_in_back_coordinates = generate_coordinates(starting_points[3], speeds[3], messsage_interval, num_points, bearings[3])
car_opposite_coordinates = generate_coordinates(starting_points[4], speeds[4], messsage_interval, num_points, bearings[4])

# Save coordinates to CSV files
with open('emergencyVehicleCoordinates.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["latitude", "longitude"])
    for point in emergency_vehicle_coordinates:
        writer.writerow([point.latitude, point.longitude])

with open('carInFrontCoordinates.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["latitude", "longitude"])
    for point in car_in_front_coordinates:
        writer.writerow([point.latitude, point.longitude])

with open('violatingCarCoordinates.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["latitude", "longitude"])
    for point in violating_car_coordinates:
        writer.writerow([point.latitude, point.longitude])

with open('carInBack.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["latitude", "longitude"])
    for point in car_in_back_coordinates:
        writer.writerow([point.latitude, point.longitude])

with open('carOppositeCoordinates.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["latitude", "longitude"])
    for point in car_opposite_coordinates:
        writer.writerow([point.latitude, point.longitude])