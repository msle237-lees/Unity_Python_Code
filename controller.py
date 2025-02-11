import numpy as np
import requests
import logging
import pygame
import json
import argparse
import sys

# This controller class only works with the AUV flight controller found at the link below. You can change the Calculate_Data function to work with any other flight controller.
# Change the axis' and buttons to match the controller you are using. You can find the axis' and buttons of your controller by using the -i flag with a True value. 
# This will log the raw input data from the controller. 

class Controller:
    def __init__(self, args: argparse.Namespace):
        pygame.init()
        pygame.joystick.init()
        while pygame.joystick.get_count() == 0:
            print("Waiting for joystick connection...")
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        self.out_data = {
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

        self.logger = self.configure_logging()

        self.args = args

        self.in_min = -0.666
        self.in_max = 0.666
        self.out_min = -1
        self.out_max = 1

        self.url = f"http://{args.ip}:{args.port}/inputs"

    def get_data(self) -> dict:
        data = {
            "axes": [self.joystick.get_axis(i) for i in range(self.joystick.get_numaxes())],
            "buttons": [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())],
            "hats": [self.joystick.get_hat(i) for i in range(self.joystick.get_numhats())]
        }
        return data
    
    def parse_data(self, data) -> tuple:
        for a in data["axes"]:
            if a < 0.1 and a > -0.1:
                a = 0
        for b in data["buttons"]:
            if b < 0.1 and b > -0.1:
                b = 0
        axes = [round(a, 3) for a in data["axes"]]
        buttons = [round(b, 3) for b in data["buttons"]]
        return axes, buttons
    
    def calculate_data(self, data) -> tuple:
        axes, buttons = data

        axes = [self.calculate_mapping(a) for a in axes]
        
        if buttons[0]:
            self.out_data["Arm"] = 0
        else:
            self.out_data["Arm"] = 1

        if buttons[11]:
            self.out_data["Hover"] = 0
        else:
            self.out_data["Hover"] = 1

        self.out_data["Y"] = round(axes[3], 3)
        self.out_data["X"] = round(axes[4], 3)
        self.out_data["Z"] = round(axes[1],3)
        self.out_data["Yaw"] = round(axes[0],3)

        self.out_data["Roll"] = 0
        self.out_data["Pitch"] = 0
        
    def calculate_mapping(self, value: float) -> float:
        return (value - self.in_min) * (self.out_max - self.out_min) / (self.in_max - self.in_min) + self.out_min
    
    def send_data(self):
        try:
            response = requests.post(self.url, data=json.dumps(self.out_data))
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(e)
            sys.exit()

    def configure_logging(self):
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        handler = logging.FileHandler('logs/controller.log')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def log_data(self, data):
        formatted_data = " | ".join(f"{key}: {value:6.2f}" for key, value in self.out_data.items())

        if self.args.input:
            log_entry = f"{data}"
        elif self.args.output:
            log_entry = f"{formatted_data}"
        else:
            log_entry = f"{data} | {formatted_data}"

        if self.args.verbose:
            print(log_entry.ljust(80), end="\r")  # Adjust 80 to the desired fixed width
        else:
            self.logger.info(log_entry)

    def run(self):
        while True:
            try:
                for _ in pygame.event.get():
                    data = self.get_data()
                    data = self.parse_data(data)
                    self.calculate_data(data)
                    # self.send_data()
                    self.log_data(data)
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Controller for the drone")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("-i", "--input", type=bool, help="Log only raw input data")
    parser.add_argument("-o", "--output", type=bool, help="Log only processed output")
    parser.add_argument("--ip", type=str, default="localhost", help="IP address of the server to send data to")
    parser.add_argument("--port", type=int, default=5001, help="Port of the server to send data to")
    args = parser.parse_args()
    controller = Controller(args)
    controller.run()