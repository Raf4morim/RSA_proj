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
    Point(40.6255656, -8.7194227),  # ambulance
    Point(40.62554703079709,-8.719538349966417),  # violating car (10 meters behind the ambulance)
    Point(40.62630827310324, -8.714796648817527),  # car in front (400 meters ahead)
    Point(40.62500847351078, -8.722892171124881),  # car in back (300 meters behind the ambulance)
    Point(40.62630827310324, -8.714796648817527)   # car coming from opposite direction (400 meters ahead)
]

new_ambulance_start = Point(40.6255656, -8.7194227)  # New starting point for the ambulance
violating_car_distance = 0.01  # 10 meters behind the ambulance

# Calculate the new starting point for the violating car
new_violating_car_start = geodesic(kilometers=violating_car_distance).destination(new_ambulance_start, 258.1)  # Bearing is 180 + 78.1 = 258.1 degrees (opposite direction)
# Print the new starting point for the violating car
print(f"New starting point for the violating car: Latitude = {new_violating_car_start.latitude}, Longitude = {new_violating_car_start.longitude}")

# Calculate the new starting points for the last 3 cars
car_in_front_distance = 0.4  # 400 meters ahead of the ambulance
car_in_back_distance = 0.3   # 300 meters behind the ambulance
car_opposite_distance = 0.4  # 300 meters ahead of the ambulance

new_car_in_front_start = geodesic(kilometers=car_in_front_distance).destination(new_ambulance_start, 78.1)  # Bearing same as ambulance
new_car_in_back_start = geodesic(kilometers=car_in_back_distance).destination(new_ambulance_start, 258.1)  # Bearing opposite to ambulance
new_car_opposite_start = geodesic(kilometers=car_opposite_distance).destination(new_ambulance_start, 78.1)  # Bearing opposite to ambulance

# Print the new starting points for the last 3 cars
print(f"{new_car_in_front_start.latitude}, {new_car_in_front_start.longitude}")
print(f"{new_car_opposite_start.latitude}, {new_car_opposite_start.longitude}")

bearings = [78.1, 78.1, 78.1, 78.1, 258.1]

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