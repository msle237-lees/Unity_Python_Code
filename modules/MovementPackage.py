import numpy as np
import requests
import logging
import time
import sys
import os


class MovementPackage:
    def __init__(self, host : str = 'localhost', port : int = 5001, verbose : bool = False):
        # Initialize the MovementPackage with host, port, and verbosity level
        self.host = host
        self.port = port
        self.verbose = verbose

        # Set up logging
        logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.debug(f"MovementPackage initialized with host: {host}, port: {port}, verbose: {verbose}")

        # Initialize the base URL for the API
        self.inputs_url = f'http://{self.host}:{self.port}/inputs'
        self.motor_url = f'http://{self.host}:{self.port}/motor'
        self.servo_url = f'http://{self.host}:{self.port}/servo'

        self.logger.debug(f"Inputs URL: {self.inputs_url}")
        self.logger.debug(f"Outputs URL: {self.outputs_url}")

        # Initialize the input, motor, and servo data dictionaries derived from the DBHandler class
        self.input_data = {
            'X': 0.0,
            'Y': 0.0,
            'Z': 0.0,
            'Roll': 0.0,
            'Pitch': 0.0,
            'Yaw': 0.0,
            'S1': 0.0,
            'S2': 0.0,
            'S3': 0.0,
            'Arm': 0.0,
            'Hover': 0.0
        }
        self.motor_data = {
            'M1': 127,
            'M2': 127,
            'M3': 127,
            'M4': 127,
            'M5': 127,
            'M6': 127,
            'M7': 127,
            'M8': 127
        }
        self.servo_data = {
            'S1': 0,
            'S2': 0,
            'S3': 0
        }
        self.logger.debug("MovementPackage initialized with default input, motor, and servo data.")

        # Configure the mapping for horizontal and vertical motors
        # -1 indicates reverse direction, 1 indicates forward direction
        # The horizontal mapping is used for the X, Y, and Yaw axes 
        # The vertical mapping is used for the Z, Pitch, and Roll axes
        self.horizontalMapping = np.array([
            [1, 1, 1, 1],       # X
            [-1, -1, 1, 1],     # Y
            [-1, 1, -1, 1]      # Yaw
        ])
        
        self.verticalMapping = np.array([
            [1, 1, 1, 1],       # Z
            [-1, -1, 1, 1],     # Pitch
            [-1, 1, -1, 1]      # Roll
        ])

        # Initialize the mapping ranges for the motors
        self.in_min = -1.0
        self.in_max = 1.0
        self.out_min = 0
        self.out_max = 255

    def get_input_data(self) -> dict:
        # Fetch input data from the server
        try:
            response = requests.get(self.inputs_url)
            response.raise_for_status()  # Raise an error for bad responses
            self.input_data = response.json()
            self.logger.debug(f"Input data fetched: {self.input_data}")
        except requests.RequestException as e:
            self.logger.error(f"Error fetching input data: {e}")
            return None
        return self.input_data

    def mapping(self, x : float) -> int:
        return int((x - self.in_min) * (self.out_max - self.out_min) / (self.in_max - self.in_min) + self.out_min)
    
    def calculate_motor_speeds(self) -> dict:
        # The input data is expected to be a dictionary with keys 'X', 'Y', 'Z', 'Roll', 'Pitch', 'Yaw', S1, S2, S3, Arm, Hover
        # The motor data is expected to be a dictionary with keys 'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8'
        # This function calculates the motor speeds based on the input data and the horizontal and vertical mappings
        pass

    def calculate_servo_angles(self) -> dict:
        # The input data is expected to be a dictionary with keys 'X', 'Y', 'Z', 'Roll', 'Pitch', 'Yaw', S1, S2, S3, Arm, Hover
        # The servo data is expected to be a dictionary with keys 'S1', 'S2', 'S3'
        # This function calculates the servo angles
        if self.input_data['Arm'] == 1:
            self.servo_data['S1'] = self.mapping(self.input_data['S1'])
            self.servo_data['S2'] = self.mapping(self.input_data['S2'])
            self.servo_data['S3'] = self.mapping(self.input_data['S3'])
        else:
            self.servo_data['S1'] = 0
            self.servo_data['S2'] = 0
            self.servo_data['S3'] = 0

    def send_motor_data(self) -> None:
        # Send the motor data to the server
        try:
            response = requests.post(self.motor_url, json=self.motor_data)
            response.raise_for_status()  # Raise an error for bad responses
            self.logger.debug(f"Motor data sent: {self.motor_data}")
        except requests.RequestException as e:
            self.logger.error(f"Error sending motor data: {e}")

    def send_servo_data(self) -> None:
        # Send the servo data to the server
        try:
            response = requests.post(self.servo_url, json=self.servo_data)
            response.raise_for_status()  # Raise an error for bad responses
            self.logger.debug(f"Servo data sent: {self.servo_data}")
        except requests.RequestException as e:
            self.logger.error(f"Error sending servo data: {e}")