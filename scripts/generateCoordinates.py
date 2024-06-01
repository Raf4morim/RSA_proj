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
    Point(40.750618005574566,-73.985428),  # car in front (200 meters ahead)
    Point(40.746989, -73.985428),  # car in back (300 meters behind the ambulance)
    Point(40.75241901058529, -73.985428)   # car coming from opposite direction (400 meters ahead)
]

bearings = [0, 0, 0, 0, 180]

speeds = [70, 70, 40, 70, 50]

num_points = 100  
messsage_interval = 0.5

# Generate coordinates 
emergency_vehicle_coordinates = generate_coordinates(starting_points[0], speeds[0], messsage_interval, num_points, bearings[0])
violating_car_coordinates = generate_coordinates(starting_points[1], speeds[1], messsage_interval, num_points, bearings[1])
car_in_front_coordinates = generate_coordinates(starting_points[2], speeds[2], messsage_interval, num_points, bearings[2])
car_in_back_coordinates = generate_coordinates(starting_points[3], speeds[3], messsage_interval, num_points, bearings[3])
car_opposite_coordinates = generate_coordinates(starting_points[4], speeds[4], messsage_interval, num_points, bearings[4])

new_ambulance_start = Point(40.748817, -73.985428)
new_car_in_front_start = geodesic(kilometers=0.4).destination(new_ambulance_start, 0)  # Bearing same as ambulance
print(f"New starting point for the car in front: Latitude = {new_car_in_front_start.latitude}, Longitude = {new_car_in_front_start.longitude}")
# Save coordinates to CSV files
files_and_coordinates = [
    ('emergencyVehicleCoordinates.csv', emergency_vehicle_coordinates, bearings[0]),
    ('violatingCarCoordinates.csv', violating_car_coordinates, bearings[1]),
    ('carInFrontCoordinates.csv', car_in_front_coordinates, bearings[2]),
    ('carInBack.csv', car_in_back_coordinates, bearings[3]),
    ('carOppositeCoordinates.csv', car_opposite_coordinates, bearings[4])
]

for file_name, coordinates, bearing in files_and_coordinates:
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["latitude", "longitude", "heading"])
        for point in coordinates:
            writer.writerow([point.latitude, point.longitude, bearing])