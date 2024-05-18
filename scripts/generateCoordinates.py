from geopy import Point
from geopy.distance import geodesic
import csv

# This script generates a list of coordinates for two cars to simulate a scenario where one car is behind the other.
# CAMs are published each 0.1 seconds (10 Hz) with the coordinates of the car in back;

# Function to generate a list of coordinates
def generate_coordinates(starting_point, distance, num_points, angle=0):
    points = [starting_point]
    for _ in range(num_points - 1):
        next_point = geodesic(kilometers=distance).destination(points[-1], angle)
        points.append(next_point)
    return points

# Define starting point and parameters
starting_point = Point(40.748817, -73.985428)  # Example: New York
distance_between_points = 0.01  # Distance in kilometers (10 meters for each step)
num_points = 10  # Number of points for the simulation

# Generate coordinates for the emergency vehicle
emergency_vehicle_coordinates = generate_coordinates(starting_point, distance_between_points, num_points)

# Generate coordinates for the violating car (5 meters behind the emergency vehicle)
violating_car_distance = 0.004  # Distance in kilometers (5 meters)
violating_car_coordinates = [
    geodesic(kilometers=violating_car_distance).destination(point, 180) for point in emergency_vehicle_coordinates
]

# Save emergency vehicle coordinates to CSV file
with open('emergencyVehicleCoordinates.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["latitude", "longitude"])
    for point in emergency_vehicle_coordinates:
        writer.writerow([point.latitude, point.longitude])

# Save violating car coordinates to CSV file
with open('violatingCarCoordinates.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["latitude", "longitude"])
    for point in violating_car_coordinates:
        writer.writerow([point.latitude, point.longitude])
