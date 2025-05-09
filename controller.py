import requests
import pygame
import time
import json
import os

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
            "X": 128,
            "Y": 128,
            "Z": 128,
            "Roll": 128,
            "Pitch": 128,
            "Yaw": 128,
            "S1": 128,
            "S2": 128,
            "S3": 128,
            "Arm": 0
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
        """
        @brief Parses the configuration file and loads the settings.
        @param config_file: Path to the configuration file.
        @return None

        @note Config file should be in JSON format like below:
        {
            "joystick_1": {
                "name": "Spektrum InterLink DX",
                "axis": {
                    "X": 4,
                    "Y": 3,
                    "Z": 1,
                    "Yaw": 0,
                    "S3": 7
                }, "button": {
                    "S1_Increase": {
                        "button": 1
                    }, "S1_Decrease": {
                        "button": 2
                    }, "S2_Increase": {
                        "button": 10
                    }, "S2_Decrease": {
                        "button": 9
                    }, "Arm": {
                        "button": 0
                    }
                }, "hat": {
                
                }
            }
        }
        """
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
        joystick_config = config[selected_joystick]
        return joystick_config
    def mapping(self, x : float, in_min : float, in_max : float, out_min : float, out_max : float):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    def parse_output_data(self, config : dict):
        """
        @brief Parses the output data from the joystick based on the configuration.
        @param config: The configuration dictionary.
        @return None
        """
        axes, buttons, hats = self.get_raw_data()
        if buttons[config["button"]["Arm"]["button"]]:
            self.output_data["Arm"] = 1
        else:
            self.output_data["Arm"] = 0
        if self.output_data["Arm"] == 1:
            self.output_data["X"] = int(self.mapping(axes[config["axis"]["X"]], -1, 1, 0, 255))
            self.output_data["Y"] = int(self.mapping(axes[config["axis"]["Y"]], -1, 1, 0, 255))
            self.output_data["Z"] = int(self.mapping(axes[config["axis"]["Z"]], -1, 1, 0, 255))
            self.output_data["Yaw"] = int(self.mapping(axes[config["axis"]["Yaw"]], -1, 1, 0, 255))
            self.output_data["S3"] = int(self.mapping(axes[config["axis"]["S3"]], -1, 1, 0, 255))
            
            if buttons[config["button"]["S1_Increase"]["button"]]:
                self.output_data["S1"] = min(self.output_data["S1"] + 10, 255)
            if buttons[config["button"]["S1_Decrease"]["button"]]:
                self.output_data["S1"] = max(self.output_data["S1"] - 10, 0)
            if buttons[config["button"]["S2_Increase"]["button"]]:
                self.output_data["S2"] = min(self.output_data["S2"] + 10, 255)
            if buttons[config["button"]["S2_Decrease"]["button"]]:
                self.output_data["S2"] = max(self.output_data["S2"] - 10, 0)
        else:
            self.output_data["X"] = 128
            self.output_data["Y"] = 128
            self.output_data["Z"] = 128
            self.output_data["Yaw"] = 128
            self.output_data["S1"] = 128
            self.output_data["S2"] = 128
            self.output_data["S3"] = 128        
        print(f"Output Data: {self.output_data}", end="\r")
    def send_data(self):
        """
        @brief Sends the output data to the DBPackage via http post requests.
        @return None
        """
        request = requests.post("http://localhost:5000/inputs", json=self.output_data)
        if request.status_code == 200:
            print("Data sent successfully.")
        else:
            print(f"Failed to send data. Status code: {request.status_code}")

if __name__ == "__main__":
    controller = Controller()
    try:
        joystick_config = controller.parse_config("configs/controller.json")
        while True:
            # controller.print_raw_data()
            controller.parse_output_data(joystick_config)
            controller.send_data()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting...")
        pygame.quit()