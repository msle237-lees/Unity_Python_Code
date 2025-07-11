import argparse
import requests
import pygame
import time
import json
import os

def truncate_small_values(data, threshold=1e-3):
    return {k: (0.0 if abs(v) < threshold else v) for k, v in data.items()}

def apply_deadzone(value, deadzone=0.1):
    return 0.0 if abs(value) < deadzone else value

def map_axis(value, in_min=-1.0, in_max=1.0, out_min=-1.0, out_max=1.0):
    """
    Maps an axis value from input range to output range.
    """
    return round(((value - in_min) * (out_max - out_min) / (in_max - in_min)) + out_min, 2)

class Controller:
    def __init__(self, ip="localhost", port=5000):
        # Configurable output range for all axes
        self.axis_min = -10.0
        self.axis_max = 10.0
        self.increment_step = 0.1  # Step size for S1/S2 buttons
        self.db_url = f"http://{ip}:{port}/inputs"

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
            # Apply deadzone and mapping to all axes
            self.output_data["X"] = map_axis(apply_deadzone(axes[config["axis"]["X"]]), -1.0, 1.0, self.axis_min, self.axis_max)
            self.output_data["Y"] = map_axis(apply_deadzone(axes[config["axis"]["Y"]]), -1.0, 1.0, self.axis_min, self.axis_max)
            self.output_data["Z"] = map_axis(apply_deadzone(axes[config["axis"]["Z"]]), -1.0, 1.0, self.axis_min, self.axis_max)
            self.output_data["Yaw"] = map_axis(apply_deadzone(axes[config["axis"]["Yaw"]]), -1.0, 1.0, self.axis_min, self.axis_max)
            self.output_data["S3"] = map_axis(apply_deadzone(axes[config["axis"]["S3"]]), -1.0, 1.0, self.axis_min, self.axis_max)

            # Adjust S1 and S2 via button step
            if buttons[config["button"]["S1_Increase"]["button"]]:
                self.output_data["S1"] = min(self.output_data["S1"] + self.increment_step, self.axis_max)
            if buttons[config["button"]["S1_Decrease"]["button"]]:
                self.output_data["S1"] = max(self.output_data["S1"] - self.increment_step, self.axis_min)
            if buttons[config["button"]["S2_Increase"]["button"]]:
                self.output_data["S2"] = min(self.output_data["S2"] + self.increment_step, self.axis_max)
            if buttons[config["button"]["S2_Decrease"]["button"]]:
                self.output_data["S2"] = max(self.output_data["S2"] - self.increment_step, self.axis_min)
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

    def send_data(self):
        """
        @brief Sends the output data to the DBPackage via HTTP POST requests.
        @return None
        """
        payload = truncate_small_values(self.output_data)
        response = requests.post(self.db_url, json=payload)
        if response.status_code == 201:
            print("Data sent successfully.")
        else:
            print(f"Failed to send data. Status code: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Controller for AUV")
    parser.add_argument("--ip", type=str, default="100.64.24.56", help="IP address for DBPackage")
    parser.add_argument("--port", type=int, default=5000, help="Port for DBPackage")
    parser.add_argument("--just-print", action="store_true", help="Just print the output data, don't send to DBPackage")
    parser.add_argument("--print-raw", action="store_true", help="Print the raw joystick data")
    parser.add_argument("--print-output", action="store_true", help="Print the output data")
    parser.add_argument("--print-both", action="store_true", help="Print both raw and output data")
    parser.add_argument("--no-print", action="store_true", help="Don't print anything")
    parser.add_argument("--print-interval", type=float, default=0.1, help="Interval for printing data (in seconds)")
    args = parser.parse_args()
    controller = Controller(args.ip, args.port)
    try:
        joystick_config = controller.parse_config("configs/controller.json")
        while True:
            controller.parse_output_data(joystick_config)

            # Handle printing options
            if args.print_raw or args.print_both:
                controller.print_raw_data()
            if args.print_output or args.print_both:
                print(f"Output Data: {controller.output_data}")
            if not args.no_print and not args.print_raw and not args.print_output and not args.print_both:
                # Default behavior - print output data
                print(f"Output Data: {controller.output_data}", end="\r")

            # Send data unless just-print is specified
            if not args.just_print:
                controller.send_data()

            time.sleep(args.print_interval)
    except KeyboardInterrupt:
        print("\nExiting...")
        pygame.quit()
