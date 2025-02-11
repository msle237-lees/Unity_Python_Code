import numpy as np
from typing import Json, List
import requests
import logging
import sys
import os

class MovementPackage:
    def __init__(self, host : str = "localhost", port : int = 5001):
        self.host = host
        self.port = port

        self.url = f"http://{self.host}:{self.port}/inputs"

        self.data = {
            "X": 0,
            "Y": 0,
            "Z": 0,
            "Roll": 0,
            "Pitch": 0,
            "Yaw": 0,
            "S1": 0,
            "S2": 0,
            "S3": 0,
            "Arm": 0,
            "Hover": 0
        }

        self.motor_map = {
            "X" : [],
            "Y" : [],
            "Z" : [],
            "Roll" : [],
            "Pitch" : [],
            "Yaw" : []
        }

    def get_data(self) -> Json:
        return requests.get(self.url).json()

    