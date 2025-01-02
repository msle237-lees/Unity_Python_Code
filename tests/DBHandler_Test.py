import requests
import json

BASE_URL = "http://localhost:5001"  # URL of the Flask app

# Define the data payloads for POST requests for each endpoint
test_data = {
    "inputs": {
        "X": 0.0, "Y": 0.0, "Z": 0.0, "Yaw": 0.0, "Pitch": 0.0, "Roll": 0.0, "S1": 0.0, "S2": 0.0, "S3": 0.0
    },
    "motor": {
        "M1": 100, "M2": 110, "M3": 120, "M4": 130, "M5": 140, "M6": 150, "M7": 160, "M8": 170
    },
    "servo": {
        "S1": 50, "S2": 60, "S3": 70
    },
    "imu": {
        "Accelerometer_X": 0.1, "Accelerometer_Y": 0.2, "Accelerometer_Z": 0.3,
        "Gyroscope_X": 0.4, "Gyroscope_Y": 0.5, "Gyroscope_Z": 0.6,
        "Magnetometer_X": 0.7, "Magnetometer_Y": 0.8, "Magnetometer_Z": 0.9
    },
    "voltage_current": {
        "Voltage_B1": 3.3, "Voltage_B2": 3.4, "Voltage_B3": 3.5,
        "Current_B1": 1.2, "Current_B2": 1.3, "Current_B3": 1.4
    },
    "hydrophone": {
        "Hydrophone_Heading": "North"
    },
    "leak_detection": {
        "Leak_Detection": True
    },
    "depth_sensor": {
        "Depth": 100.5
    },
    "internal_temperature": {
        "Internal_Temperature": 25.0
    },
    "external_temperature": {
        "External_Temperature": 18.5
    },
    "internal_humidity": {
        "Internal_Humidity": 55.0
    },
    "internal_pressure": {
        "Internal_Pressure": 101.3
    },
    "external_pressure": {
        "External_Pressure": 102.5
    }
}

# Function to test POST request
def test_post(endpoint, data):
    url = f"{BASE_URL}/{endpoint}"
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print(f"[POST] {endpoint} - Success: {response.json()}")
    else:
        print(f"[POST] {endpoint} - Failed: {response.status_code}, {response.text}")

# Function to test GET request
def test_get(endpoint):
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url)
    if response.status_code == 200:
        print(f"[GET] {endpoint} - Success: {response.json()}")
    else:
        print(f"[GET] {endpoint} - Failed: {response.status_code}, {response.text}")

# Test all POST and GET endpoints
def run_tests():
    for endpoint, data in test_data.items():
        # Test POST method
        test_post(endpoint, data)

        # Test GET method
        test_get(endpoint)

if __name__ == "__main__":
    run_tests()
