import time
import requests
import argparse
from dataclasses import dataclass
from peaceful_pie.unity_comms import UnityComms

# These dataclasses are used to represent the submarine's position, rotation, and velocity.
# They are supposed to match the structure of the data returned by Unity.
@dataclass
class SubPos:
    x: float
    y: float
    z: float

@dataclass
class SubRot:
    roll: float
    pitch: float
    yaw: float

@dataclass
class SubVel:
    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float


class unityInterface:
    def __init__(self, unity_port: int, inputs_url: str, inputs_port: int) -> None:
        self.unity_comms = UnityComms(port=unity_port)
        self.url = f'http://{inputs_url}:{inputs_port}/inputs'

    def get_submarine_position(self) -> SubPos:
        """Get the submarine position from Unity."""
        res: SubPos = self.unity_comms.getSubPos(ResultClass=SubPos)
        return res

    def get_submarine_rotation(self) -> SubRot:
        """Get the submarine rotation from Unity."""
        res: SubRot = self.unity_comms.getSubRot(ResultClass=SubRot)
        return res
    
    def get_submarine_velocity(self) -> SubVel:
        """Get the submarine velocity from Unity."""
        res: SubVel = self.unity_comms.getSubMeasuredVel(ResultClass=SubVel)
        return res
    
    def set_submarine_velocity(self, velocity: SubVel) -> None:
        """Set the submarine velocity in Unity."""
        self.unity_comms.setSubSetVel(subSetVel=velocity)

    def restart_sub_position(self) -> None:
        """Restart the submarine position in Unity."""
        self.unity_comms.restartPosition()

    def get_data(self) -> SubVel:
        """Get the input data from the RL server."""
        """This method should be used during testing to get the input data from the RL server."""
        """It fetches the data from the specified URL and converts it into a SubVel dataclass instance."""
        response = requests.get(self.url)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and data:
                data = data[-1]
            if isinstance(data, dict):
                # Convert keys to lowercase, exclude the 'datetime' and 'id' keys, and convert the remaining dictionary to a dataclass instance
                data = {k.lower(): v for k, v in data.items() if k.lower() not in ['datetime', 'id']}
                return SubVel(**data)
        return None
    
    def run(self) -> None:
        while True:
            # Get the submarine position, rotation, and velocity from Unity
            sub_pos = self.get_submarine_position()
            sub_rot = self.get_submarine_rotation()
            sub_vel = self.get_submarine_velocity()

            # Print the submarine's position, rotation, and velocity
            print(f"Position: {sub_pos}, Rotation: {sub_rot}, Velocity: {sub_vel}")

            # Get the input data from the RL server
            input_data = self.get_data()
            if input_data:
                # Set the submarine's velocity in Unity
                self.set_submarine_velocity(input_data)

            time.sleep(0.1) # Sleep for a short duration to avoid overwhelming the server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unity Interface")
    parser.add_argument("--unity_port", type=int, default=9999, help="Port for Unity communication")
    parser.add_argument("--inputs_url", type=str, default="localhost", help="URL for RL server")
    parser.add_argument("--inputs_port", type=int, default=5001, help="Port for RL server")
    args = parser.parse_args()

    unity_interface = unityInterface(args.unity_port, args.inputs_url, args.inputs_port)
    
    unity_interface.run()