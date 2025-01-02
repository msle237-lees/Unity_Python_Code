import requests
import numpy as np
from datetime import datetime, timezone
import argparse  # For command line arguments when running the script
import logging
import os

# Import the PID controller class
from support.PID import PIDController6DOF

# Ensure the logs directory exists
os.makedirs('../logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    filename='../logs/MovementPackage.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Map class to translate Raw values to motor values
def map_value(value, in_min, in_max, out_min, out_max):
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

class MovementPackage:
    def __init__(self, ip, port, deadzone=0.2, max_motor_value=1, min_motor_value=-1):
        # Base URL for the API
        BASE_URL = f"http://{ip}:{port}"
        self.INPUTS = BASE_URL + "/inputs"
        self.MOTORS = BASE_URL + "/motors"
        self.SERVOS = BASE_URL + "/servos"

        self.horizontal_motor_mapping = np.array([
            [1, 1, 1, 1],      # X
            [-1, -1, -1, -1],  # Y
            [1, -1, 1, -1]     # Yaw
        ])

        self.vertical_motor_mapping = np.array([
            [1, 1, 1, 1],      # Z
            [-1, -1, -1, -1],  # Pitch
            [1, -1, 1, -1]     # Roll
        ])

        self.motor_data = np.full(8, 127, dtype=int)  # 8 motors initialized to 127
        self.servo_data = np.full(3, 127, dtype=int)  # 3 servos initialized to 127

        self.deadzone = deadzone
        self.max_motor_value = max_motor_value
        self.min_motor_value = min_motor_value

        # Initialize PID controller
        self.pid = PIDController6DOF(kp=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
                                      ki=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                      kd=[0.1, 0.1, 0.1, 0.1, 0.1, 0.1])

        logging.info("MovementPackage initialized")

    def dict_to_array(self, data, keys):
        """Convert a dictionary to a NumPy array based on given keys."""
        return np.array([data[key] for key in keys])

    def array_to_dict(self, array, keys):
        """Convert a NumPy array to a dictionary using given keys."""
        return {key: value for key, value in zip(keys, array)}

    def get_inputs(self):
        url = self.INPUTS
        try:
            response = requests.get(url)
            if response.status_code == 200:
                logging.info(f"[GET] Inputs - Success: {response.json()}")
                return response.json()
            else:
                logging.error(f"[GET] Inputs - Failed: {response.status_code}, {response.text}")
        except requests.RequestException as e:
            logging.error(f"[GET] Inputs - Exception: {e}")
        return None

    def parse_inputs(self, data):
        try:
            # Convert DOF data to NumPy arrays
            horizontal_data = self.dict_to_array(data, ["X", "Y", "Yaw"])
            vertical_data = self.dict_to_array(data, ["Z", "Pitch", "Roll"])

            # Apply PID controller to DOF values
            current_time = datetime.now(timezone.utc).timestamp()
            pid_outputs = self.pid.compute(np.concatenate((horizontal_data, vertical_data)), current_time)

            # Map DOF values to motor outputs
            horizontal_motors = np.dot(self.horizontal_motor_mapping.T, pid_outputs[:3])
            vertical_motors = np.dot(self.vertical_motor_mapping.T, pid_outputs[3:])

            # Combine motor outputs and scale
            motor_values = horizontal_motors + vertical_motors
            self.motor_data = self.array_to_dict(np.clip(map_value(motor_values, -1, 1, 0, 256), 0, 256), [f"M{i+1}" for i in range(8)])

            # Map servo data
            self.servo_data = self.array_to_dict(
                np.clip(map_value(self.dict_to_array(data, ["S1", "S2", "S3"]), -1, 1, 0, 256), 0, 256),
                ["S1", "S2", "S3"]
            )

            logging.info("Inputs parsed successfully with PID adjustment")
        except Exception as e:
            logging.error(f"Error parsing inputs: {e}")

    def post_motors(self):
        url = self.MOTORS
        try:
            response = requests.post(url, json=self.motor_data)
            if response.status_code == 200:
                logging.info(f"[POST] Motors - Success: {response.json()}")
            else:
                logging.error(f"[POST] Motors - Failed: {response.status_code}, {response.text}")
        except requests.RequestException as e:
            logging.error(f"[POST] Motors - Exception: {e}")

    def post_servos(self):
        url = self.SERVOS
        try:
            response = requests.post(url, json=self.servo_data)
            if response.status_code == 200:
                logging.info(f"[POST] Servos - Success: {response.json()}")
            else:
                logging.error(f"[POST] Servos - Failed: {response.status_code}, {response.text}")
        except requests.RequestException as e:
            logging.error(f"[POST] Servos - Exception: {e}")

    def run(self):
        logging.info("Running MovementPackage")
        inputs = self.get_inputs()
        if inputs:
            self.parse_inputs(inputs)
            self.post_motors()
            self.post_servos()
        else:
            logging.warning("No inputs received")
