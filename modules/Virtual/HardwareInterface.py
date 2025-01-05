import os
import json
import logging
import argparse
import requests
import pyautogui
import numpy as np
from datetime import datetime, timezone

# Ensure the logs directory exists
os.makedirs('../logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    filename='../logs/HardwareInterface.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class HardwareInterface:
    def __init__(self, ip, port):
        self.BASE_URL = f"http://{ip}:{port}"
        self.outputs = self.BASE_URL + "/outputs"

        self.motor_values = np.array(127 for _ in range(8))
        self.servo_values = np.array(127 for _ in range(3))
        self.input_values = np.array(0 for _ in range(9))

        self.control_keys = {
            'X+': 'w', 'X-': 's',
            'Z+': 'a', 'Z-': 'd',
            'Yaw+': 'q', 'Yaw-': 'e',
            'Vertical+': 'z', 'Vertical-': 'x',
            'Torpedo1': 'c', 'Torpedo2': 'v',
            'ClawOpen': 't', 'ClawClose': 'space'
        }

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

    def get_data(self):
        try:
            response = requests.get(self.outputs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error getting data: {e}")
            return None

    def parse_inputs(self):
        data = self.get_data()
        if data is None:
            return

        # Parse the data into motor and servo values arrays based on the keys
        for key, value in data.items():
            # dict values to lists
            if key.startswith('M') and key[1:].isdigit():
                index = int(key[1:]) - 1
                if 0 <= index < len(self.motor_values):
                    self.motor_values[index] = value
            elif key.startswith('S') and key[1:].isdigit():
                index = int(key[1:]) - 1
                if 0 <= index < len(self.servo_values):
                    self.servo_values[index] = value

        # Convert motor values to 6 DOF values
        horizontal_motor_values = self.motor_values[:4]
        vertical_motor_values = self.motor_values[4:]

        # Horizontal movement corresponds to X, Y, and Yaw
        horizontal_values = np.dot(self.horizontal_motor_mapping, horizontal_motor_values)
        # Vertical movement corresponds to Z, Pitch, and Roll
        vertical_values = np.dot(self.vertical_motor_mapping, vertical_motor_values)

        # Combine the horizontal and vertical values
        self.input_values = np.concatenate((horizontal_values, vertical_values))

    def control(self):
        # Get the latest data
        self.parse_inputs()

        # Control the robot
        # X, Y, Z, Pitch, Roll, Yaw
        # 'X+': 'w', 'X-': 's',
        # 'Z+': 'a', 'Z-': 'd',
        # 'Yaw+': 'q', 'Yaw-': 'e',
        # 'Vertical+': 'z', 'Vertical-': 'x',
        # 'Torpedo1': 'c', 'Torpedo2': 'v',
        # 'ClawOpen': 't', 'ClawClose': 'space'
        # X = X+, X-
        # Y = Z+, Z-
        # Z = Vertical+, Vertical-
        # Yaw = Yaw+, Yaw-
        # S1 = Torpedo1
        # S2 = Torpedo2
        # S3 = ClawOpen, ClawClose

        # X
        if self.input_values[0] > 127:
            pyautogui.press(self.control_keys['X+'])
        elif self.input_values[0] < 127:
            pyautogui.press(self.control_keys['X-'])

        # Y
        if self.input_values[1] > 127:
            pyautogui.press(self.control_keys['Z+'])
        elif self.input_values[1] < 127:
            pyautogui.press(self.control_keys['Z-'])

        # Z
        if self.input_values[2] > 127:
            pyautogui.press(self.control_keys['Vertical+'])
        elif self.input_values[2] < 127:
            pyautogui.press(self.control_keys['Vertical-'])

        # Yaw
        if self.input_values[5] > 127:
            pyautogui.press(self.control_keys['Yaw+'])
        elif self.input_values[5] < 127:
            pyautogui.press(self.control_keys['Yaw-'])

        # Torpedo1
        if self.servo_values[0] > 127:
            pyautogui.press(self.control_keys['Torpedo1'])

        # Torpedo2
        if self.servo_values[1] > 127:
            pyautogui.press(self.control_keys['Torpedo2'])
        
        # Claw
        if self.servo_values[2] > 127:
            pyautogui.press(self.control_keys['ClawOpen'])
        else:
            pyautogui.press(self.control_keys['ClawClose'])
