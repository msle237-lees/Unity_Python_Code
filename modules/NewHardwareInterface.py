import time
import requests
import argparse
from dataclasses import dataclass
from peaceful_pie.unity_comms import UnityComms


class unityInterface:
    def __init__(self, unity_port: str = 9999, \
                    inputs_url: str = 'localhost', \
                        inputs_port: int = 5000, \
                            test : bool = False) -> None:
        """
        
        """
        if test:
            self.unityComms = None
            print("Running in test mode, UnityComms will not be initialized.")
        else:
            self.unityComms = UnityComms(port=unity_port)
        self.inputsURL = f'http://{inputs_url}:{inputs_port}/action'
        self.test = test

    def _restartSubPosition(self) -> None:
        """
        Restart the submarine position in Unity.
        """
        self.unityComms.restartSubPos()

    def _getDBInputs(self) -> dict:
        """
        Get the latest inputs from the database.
        """
        response = requests.get(self.inputsURL)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get inputs: {response.status_code} {response.text}")

    def _sendToUnity(self, data: dict) -> None:
        """
        Send data to Unity.
        """
        if not data:
            raise ValueError("Data to send to Unity cannot be empty.")

        # If the data is not empty, convert from direction and force levels 
        # to normal velocity vectors
        direction = data.get('direction')
        force_level = data.get('force_level', 0)

        # Support combinational control: direction can be a list or a string
        if isinstance(direction, str):
            directions = [direction]
        elif isinstance(direction, list):
            directions = direction
        else:
            raise ValueError("Direction must be a string or a list of strings.")

        velocity = {
            "x": 0,
            "y": 0,
            "z": 0,
            "roll": 0,
            "pitch": 0,
            "yaw": 0
        }

        for dir in directions:
            if dir == 'forward':
                velocity["x"] += force_level
            elif dir == 'backward':
                velocity["x"] -= force_level
            elif dir == 'up':
                velocity["y"] += force_level
            elif dir == 'down':
                velocity["y"] -= force_level
            elif dir == 'right':
                velocity["z"] += force_level
            elif dir == 'left':
                velocity["z"] -= force_level
            elif dir == 'yaw_right':
                velocity["yaw"] += force_level
            elif dir == 'yaw_left':
                velocity["yaw"] -= force_level

        # update the class variable with the new velocity
        self.velocity = velocity

        if self.test:
            print(f"Test mode: would send {data} to Unity as velocity {velocity}")
        else:
            self.unityComms.setSubMeasuredVel(velocity)

    def run(self) -> None:
        """
        Main loop to run the Unity interface.
        """
        if self.test:
            print("Test mode: Enter multiple directions separated by commas (e.g., forward,left,up)")
            while True:
                direction_input = input("Enter direction(s): ")
                directions = [d.strip() for d in direction_input.split(',') if d.strip()]
                force_level_input = input("Enter force level (0, 25, 50, 75, 100): ")
                try:
                    force_level = int(force_level_input)
                except ValueError:
                    print("Invalid force level. Please enter a number.")
                    continue
                valid_directions = {'forward', 'backward', 'left', 'right', 'up', 'down', 'yaw_right', 'yaw_left'}
                if not all(d in valid_directions for d in directions):
                    print(f"Invalid direction(s). Valid options: {', '.join(valid_directions)}")
                    continue
                if force_level not in [0, 25, 50, 75, 100]:
                    print("Invalid force level. Please try again.")
                    continue
                action = {
                    "direction": directions if len(directions) > 1 else directions[0],
                    "force_level": force_level
                }
                self._sendToUnity(action)
                time.sleep(1)
        else:
            while True:
                inputs = self._getDBInputs()
                if inputs['arm'] == 0:
                    self._restartSubPosition()
                else:
                    self._sendToUnity(inputs)
                time.sleep(0.1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unity Interface for AUV")
    parser.add_argument('--unity_port', type=int, default=9999, help='Port for Unity communication (default: 9999)')
    parser.add_argument('--inputs_url', type=str, default='localhost', help='URL for inputs server (default: localhost)')
    parser.add_argument('--inputs_port', type=int, default=5000, help='Port for inputs server (default: 5000)')
    parser.add_argument('--test', action='store_true', help='Run in test mode without UnityComms')
    args = parser.parse_args()

    interface = unityInterface(unity_port=args.unity_port, inputs_url=args.inputs_url, inputs_port=args.inputs_port, test=args.test)
    interface.run()
