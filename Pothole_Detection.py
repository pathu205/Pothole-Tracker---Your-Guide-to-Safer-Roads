import math
import time
import cv2
import numpy as np
import pandas as pd
import cx_Oracle
import serial
import datetime
import requests
import socket
from ultralytics import YOLO
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize GPS/GSM modem
RPI_IP = "192.168.147.152"  # Replace with your Raspberry Pi's IP
PORT = 5000  # Same port as the server

# Load Firebase credentials
cred = credentials.Certificate("C:\\Users\\prita\\Downloads\\serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Get Firestore database instance
db = firestore.client()
# Load the YOLO model
model = YOLO("C:\\Users\\prita\\OneDrive\\Desktop\\pthhole_tracker\\COMPONENT TESTER CODES\\roombest.pt")
class_names = model.names

# Camera parameters
focal_length = 3.12  
sensor_width = 3.67  
image_width_pixels = 1664
fov_horizontal = 60  

# Calculate FOV in radians
fov_horizontal_rad = math.radians(fov_horizontal)

# Initialize camera
cap = cv2.VideoCapture("C:\\Users\\prita\\OneDrive\\Desktop\\pthhole_tracker\\COMPONENT TESTER CODES\\recording_fortesting.mp4")  

# Parameters
tracked_potholes = []
threshold_distance = 50  
pothole_data = []
total_potholes = 0  
frames_processed = 0  
MPU_SERVER_URL = f"http://{RPI_IP}:{PORT}/sensor_data"   

def classify_pothole_size(area):
    if area < 8000:
        return "Small"
    elif 8000 <= area < 18000:
        return "Medium"
    else:
        return "Large"

def get_gps_location():
    try:
        url = f"http://{RPI_IP}:{PORT}/gps_data"  # Flask endpoint
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if "latitude" in data and "longitude" in data:
                return data["latitude"], data["longitude"]
    except Exception as e:
        print("Error fetching GPS data:", e)
    return None, None
# Function to get the next ID
def get_next_pothole_id():
    docs = db.collection("potholes_database").order_by("id", direction=firestore.Query.DESCENDING).limit(1).stream()
    for doc in docs:
        return doc.to_dict().get("id", 0) + 1  # Increment last ID by 1
    return 1  # Start with ID 1 if no records exist
# Function to store pothole data in Firebase
def store_in_database(latitude, longitude, size_class):
    next_id = get_next_pothole_id()  # Get the next available ID
    pothole_data = {
        "id":  next_id,
        "latitude": latitude,
        "longitude": longitude,
        "detected": firestore.SERVER_TIMESTAMP,  # Auto-set timestamp
        "size": size_class
    }

    # Add data to Firestore
    db.collection("potholes_database").add(pothole_data)
    print(f"Pothole data stored successfully! Assigned ID: {next_id}")

def is_new_pothole(center, tracked_potholes, threshold):
    # Iterate through each tracked pothole
    for tracked in tracked_potholes:
        # Calculate the distance between the center and the tracked pothole
        distance = np.linalg.norm(np.array(center) - np.array(tracked))
        # If the distance is less than the threshold, return False
        if distance < threshold:
            return False  
    # If no tracked pothole is within the threshold, return True
    return True

def get_distance_from_camera(pothole_width_pixels, pothole_real_width):
    return (focal_length * pothole_real_width) / pothole_width_pixels

def get_camera_orientation():
    try:
        response = requests.get(MPU_SERVER_URL)
        if response.status_code == 200:
            data = response.json()
            return data.get("pitch", 0), data.get("roll", 0), data.get("yaw", 0)
    except requests.RequestException as e:
        print("Error fetching MPU data:", e)
    return 0, 0, 0  

def adjust_gps_coordinates(latitude, longitude, distance, pitch, yaw):
    lat_rad = math.radians(float(latitude))
    lon_rad = math.radians(float(longitude))
    delta_lat = (distance * math.cos(pitch)) / 111320
    delta_lon = (distance * math.cos(pitch) * math.cos(yaw)) / (40008000 * math.cos(lat_rad) / 360)
    return math.degrees(lat_rad + delta_lat), math.degrees(lon_rad + delta_lon)

count = 0  
while True:
    ret, img = cap.read()
    if not ret:
        break
    count += 1
    frames_processed += 1
    if count % 3 != 0:  
        continue

    img = cv2.resize(img, (1020, 500))
    results = model.predict(img)

    for r in results:
        boxes = r.boxes  
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            width = x2 - x1
            area = width * (y2 - y1)
            size_class = classify_pothole_size(area)
            center = ((x1 + x2) // 2, (y1 + y2) // 2)
            
            if is_new_pothole(center, tracked_potholes, threshold_distance):
                tracked_potholes.append(center)
                pothole_width_pixels = width
                pothole_real_width = 0.2  
                distance = get_distance_from_camera(pothole_width_pixels, pothole_real_width)
                pitch, roll, yaw = get_camera_orientation()
                latitude, longitude = get_gps_location()
                if latitude and longitude:
                    adjusted_lat, adjusted_lon = adjust_gps_coordinates(latitude, longitude, distance, pitch, yaw)
                    store_in_database(adjusted_lat, adjusted_lon, size_class)
                    total_potholes += 1
                    print(f"Pothole ID: {total_potholes}, Size: {size_class}, Location: ({adjusted_lat}, {adjusted_lon})")

            color = (0, 255, 0) if size_class == "Small" else (0, 165, 255) if size_class == "Medium" else (0, 0, 255)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, size_class, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    cv2.putText(img, f"Frames: {frames_processed}, Potholes: {total_potholes}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.imshow('Pothole Detection', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
#connection.close()
print(f'Total potholes detected: {total_potholes}')
print(f'Total frames processed: {frames_processed}')
