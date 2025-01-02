import argparse
import requests
import json
import pyautogui
import logging
from datetime import datetime, timezone
import os

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

        self.motor_data = {"M1": 127, "M2": 127, "M3": 127, "M4": 127, 
                           "M5": 127, "M6": 127, "M7": 127, "M8": 127}

        self.servo_data = {"S1": 127, "S2": 127, "S3": 127}

        self.control_keys = {
            'X+': 'w', 'X-': 's',
            'Z+': 'a', 'Z-': 'd',
            'Yaw+': 'q', 'Yaw-': 'e',
            'Vertical+': 'z', 'Vertical-': 'x',
            'Torpedo1': 'c', 'Torpedo2': 'v',
            'ClawOpen': 't', 'ClawClose': 'space'
        }

        self.paused = False
        logging.info("HardwareInterface initialized")

    def get_data(self):
        url = self.outputs
        try:
            response = requests.get(url)
            if response.status_code == 200:
                logging.info(f"[GET] Outputs - Success: {response.json()}")
                return response.json()
            else:
                logging.error(f"[GET] Outputs - Failed: {response.status_code}, {response.text}")
        except requests.RequestException as e:
            logging.error(f"[GET] Outputs - Exception: {e}")
        return None
    
    def parse_data(self, data):
        # Have to calculate the DOF values from the motor data
        # and update the servo data
        pass