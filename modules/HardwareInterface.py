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
    def __init__(self, unity_port: str = 9999, inputs_url: str = '127.0.0.1', inputs_port: int = 9999) -> None:
        self.unity_comms = UnityComms(port=unity_port)
        self.url = f'http://{inputs_url}:{inputs_port}/inputs'
        self.pos_url = f'http://{inputs_url}:{inputs_port}/position'
        self.rot_url = f'http://{inputs_url}:{inputs_port}/rotation'
        self.vel_url = f'http://{inputs_url}:{inputs_port}/velocity'

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

    def restart_sub_position(self, data) -> None:
        """Restart the submarine position in Unity."""
        if data['arm']:
            pass
        else:
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
                print(data.keys())
            if isinstance(data, dict):
                # Convert keys to lowercase, exclude the 'datetime' and 'id' keys, and convert the remaining dictionary to a dataclass instance
                data = {k.lower(): v for k, v in data.items() if k.lower() not in ['datetime', 'id', 's1', 's2', 's3']}
                self.restart_sub_position(data)
                del data['arm']
                return SubVel(**data)
        return None
    
    def post_data(self, subvel : SubVel, subpos : SubPos, subrot : SubRot) -> None:
        """
        @brief Post the submarine's position, rotation, and velocity to the DBPackage.
        @param subvel: The submarine's velocity.
        @param subpos: The submarine's position.
        @param subrot: The submarine's rotation.
        @return None
        """
        pos_data = {
            'datetime': time.strftime('%Y-%m-%d %H:%M:%S'),
            'X': subpos.x,
            'Y': subpos.y,
            'Z': subpos.z
        }
        post_request = requests.post(self.pos_url, json=pos_data)
        if post_request.status_code == 201:
            # print("Position data sent successfully.")
            pass
        else:
            print(f"Failed to send position data. Status code: {post_request.status_code}")
        rot_data = {
            'datetime': time.strftime('%Y-%m-%d %H:%M:%S'),
            'Roll': subrot.roll,
            'Pitch': subrot.pitch,
            'Yaw': subrot.yaw
        }
        post_request = requests.post(self.rot_url, json=rot_data)
        if post_request.status_code == 201:
            # print("Rotation data sent successfully.")
            pass
        else:
            print(f"Failed to send rotation data. Status code: {post_request.status_code}")
        vel_data = {
            'datetime': time.strftime('%Y-%m-%d %H:%M:%S'),
            'Vx': subvel.x,
            'Vy': subvel.y,
            'Vz': subvel.z,
            'Roll': subvel.roll,
            'Pitch': subvel.pitch,
            'Yaw': subvel.yaw
        }
        post_request = requests.post(self.vel_url, json=vel_data)
        if post_request.status_code == 201:
            # print("Velocity data sent successfully.")
            pass
        else:
            print(f"Failed to send velocity data. Status code: {post_request.status_code}")
        # print(f"Data sent successfully: {data}")
    
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

            # Post the submarine's position, rotation, and velocity to the DBPackage
            self.post_data(sub_vel, sub_pos, sub_rot)

            time.sleep(0.1) # Sleep for a short duration to avoid overwhelming the server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unity Interface")
    parser.add_argument("--unity_port", type=int, default=9999, help="Port for Unity communication")
    parser.add_argument("--inputs_url", type=str, default="localhost", help="URL for RL server")
    parser.add_argument("--inputs_port", type=int, default=5000, help="Port for RL server")
    args = parser.parse_args()

    unity_interface = unityInterface(args.unity_port, args.inputs_url, args.inputs_port)
    
    unity_interface.run()