import requests
import pygame
import time
import json
import os

def truncate_small_values(data, threshold=1e-3):
    return {k: (0.0 if abs(v) < threshold else v) for k, v in data.items()}

def apply_deadzone(value, deadzone=0.1):
    return 0.0 if abs(value) < deadzone else value

class Controller:
    def __init__(self):
        self.joystick = None
        while self.joystick is None:
            try:
                pygame.init()
                pygame.joystick.init()
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
            except pygame.error:
                print("No joystick found. Please connect a joystick and try again.")
                time.sleep(1)
                continue

        self.output_data = {
            "X": 0.0,
            "Y": 0.0,
            "Z": 0.0,
            "Roll": 0.0,
            "Pitch": 0.0,
            "Yaw": 0.0,
            "S1": 0.0,
            "S2": 0.0,
            "S3": 0.0,
            "Arm": 0.0
        }

    def get_raw_data(self):
        pygame.event.pump()
        axes = [round(self.joystick.get_axis(i), 2) for i in range(self.joystick.get_numaxes())]
        buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]
        hats = [self.joystick.get_hat(i) for i in range(self.joystick.get_numhats())]
        return axes, buttons, hats

    def print_raw_data(self):
        axes, buttons, hats = self.get_raw_data()
        print(f"Axes: {axes}, Buttons: {buttons}, Hats: {hats}", end="\r")

    def parse_config(self, config_file):
        if not os.path.exists(config_file):
            print(f"Config file {config_file} not found.")
            return
        with open(config_file, 'r') as file:
            config = json.load(file)

        print("Which controller do you want to use?")
        for i, key in enumerate(config.keys()):
            print(f"{i}: {key}")
        choice = int(input("Enter the number of your choice: "))
        if choice < 0 or choice >= len(config):
            print("Invalid choice. Exiting.")
            return
        selected_joystick = list(config.keys())[choice]
        print(f"Selected joystick: {config[selected_joystick]['name']}")
        return config[selected_joystick]

    def parse_output_data(self, config: dict):
        axes, buttons, hats = self.get_raw_data()
        self.output_data["Arm"] = float(buttons[config["button"]["Arm"]["button"]])

        if self.output_data["Arm"] == 1.0:
            self.output_data["X"] = apply_deadzone(axes[config["axis"]["X"]])
            self.output_data["Y"] = apply_deadzone(axes[config["axis"]["Y"]])
            self.output_data["Z"] = apply_deadzone(axes[config["axis"]["Z"]])
            self.output_data["Yaw"] = apply_deadzone(axes[config["axis"]["Yaw"]])
            self.output_data["S3"] = apply_deadzone(axes[config["axis"]["S3"]])

            if buttons[config["button"]["S1_Increase"]["button"]]:
                self.output_data["S1"] = min(self.output_data["S1"] + 0.1, 1.0)
            if buttons[config["button"]["S1_Decrease"]["button"]]:
                self.output_data["S1"] = max(self.output_data["S1"] - 0.1, -1.0)
            if buttons[config["button"]["S2_Increase"]["button"]]:
                self.output_data["S2"] = min(self.output_data["S2"] + 0.1, 1.0)
            if buttons[config["button"]["S2_Decrease"]["button"]]:
                self.output_data["S2"] = max(self.output_data["S2"] - 0.1, -1.0)
        else:
            self.output_data.update({
                "X": 0.0,
                "Y": 0.0,
                "Z": 0.0,
                "Yaw": 0.0,
                "S1": 0.0,
                "S2": 0.0,
                "S3": 0.0
            })

        print(f"Output Data: {self.output_data}", end="\r")

    def send_data(self):
        """
        @brief Sends the output data to the DBPackage via HTTP POST requests.
        @return None
        """
        payload = truncate_small_values(self.output_data)
        response = requests.post("http://localhost:5000/inputs", json=payload)
        if response.status_code == 201:
            print("Data sent successfully.")
        else:
            print(f"Failed to send data. Status code: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    controller = Controller()
    try:
        joystick_config = controller.parse_config("configs/controller.json")
        while True:
            controller.parse_output_data(joystick_config)
            controller.send_data()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting...")
        pygame.quit()
