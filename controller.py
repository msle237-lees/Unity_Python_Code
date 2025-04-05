import numpy as np
import requests
import logging
import pygame
import json
import argparse
import sys

class Controller:
    def __init__(self, args: argparse.Namespace):
        pygame.init()
        pygame.joystick.init()
        while pygame.joystick.get_count() == 0:
            print("Waiting for joystick connection...")
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        self.args = args
        self.logger = self.configure_logging()
        self.url = f"http://{args.ip}:{args.port}/inputs"

        # Load full configuration
        full_config = self.load_config(args.config)
        
        # Determine which controller configuration to use
        self.controller_type = args.controller or full_config.get("default_controller", "AUV_Flight_Controller")
        if self.controller_type not in full_config["controllers"]:
            print(f"Error: Controller type '{self.controller_type}' not found in configuration.")
            sys.exit(1)
        
        self.config = full_config["controllers"][self.controller_type]
        
        self.out_data = {key: 0 for key in self.config["output_mapping"].keys()}
        
        self.in_min = self.config["in_min"]
        self.in_max = self.config["in_max"]
        self.out_min = self.config["out_min"]
        self.out_max = self.config["out_max"]
    
    def load_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading configuration file: {e}")
            sys.exit(1)
    
    def get_data(self) -> dict:
        return {
            "axes": [self.joystick.get_axis(i) for i in range(self.joystick.get_numaxes())],
            "buttons": [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())],
            "hats": [self.joystick.get_hat(i) for i in range(self.joystick.get_numhats())]
        }
    
    def parse_data(self, data) -> tuple:
        axes = [round(a, 3) if abs(a) >= 0.1 else 0 for a in data["axes"]]
        buttons = [b for b in data["buttons"]]
        return axes, buttons
    
    def calculate_data(self, data) -> None:
        axes, buttons = data
        axes = [self.calculate_mapping(a) for a in axes]

        for key, mapping in self.config["output_mapping"].items():
            if mapping["type"] == "axis":
                self.out_data[key] = round(axes[mapping["index"]], 3)
            elif mapping["type"] == "button":
                self.out_data[key] = int(buttons[mapping["index"]])
    
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
            print(log_entry.ljust(80), end="\r")
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
    parser.add_argument("--config", type=str, default="configs\controller_config.json", help="Path to the controller config JSON file")
    parser.add_argument("--controller", type=str, help="Specify which controller profile to use", default="AUV_Flight_Controller")
    args = parser.parse_args()
    
    controller = Controller(args)
    controller.run()
