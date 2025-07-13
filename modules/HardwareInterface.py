import time
import requests
import argparse
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
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


class UnityInterface:
    def __init__(self, unity_ip: str = 'localhost', unity_port: int = 9999,
                 inputs_url: str = 'localhost', inputs_port: int = 5000) -> None:
        """
        Initialize the Unity interface.

        Parameters
        ----------
        unity_ip : str
            IP address of the Unity simulation
        unity_port : int
            Port for Unity communication
        inputs_url : str
            IP address of the database/inputs server
        inputs_port : int
            Port for database/inputs server
        """
        self.unity_ip = unity_ip
        self.unity_port = unity_port
        self.inputs_url = inputs_url
        self.inputs_port = inputs_port

        # Initialize Unity communications
        self.unity_comms = UnityComms(port=unity_port, ip=unity_ip)

        # Database API endpoints
        self.url = f'http://{inputs_url}:{inputs_port}/inputs'
        self.pos_url = f'http://{inputs_url}:{inputs_port}/position'
        self.rot_url = f'http://{inputs_url}:{inputs_port}/rotation'
        self.vel_url = f'http://{inputs_url}:{inputs_port}/velocity'

        print(f"[INFO] Unity Interface initialized:")
        print(f"  Unity: {unity_ip}:{unity_port}")
        print(f"  Database: {inputs_url}:{inputs_port}")

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
        """
            Set the submarine velocity in Unity.
            X = F (-1) / B (1)
            Y = U (1) / D (-1)
            Z = R (1) / L (-1)
            Roll = R / L
            Pitch = F / B
            Yaw = R / L
        """
        velocity.x = velocity.x * -1
        self.unity_comms.setSubSetVel(subSetVel=velocity)

    def restart_sub_position(self, data) -> None:
        """Restart the submarine position in Unity."""
        if data['arm']:
            pass
        else:
            self.unity_comms.restartPosition()

    def get_data(self) -> Optional[SubVel]:
        """Get the input data from the RL server."""
        try:
            response = requests.get(self.url, timeout=1.0)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and data:
                    data = data[-1]
                if isinstance(data, dict):
                    # Convert keys to lowercase, exclude the 'datetime' and 'id' keys
                    data = {k.lower(): v for k, v in data.items() if k.lower() not in ['datetime', 'id', 's1', 's2', 's3']}
                    self.restart_sub_position(data)
                    if 'arm' in data:
                        del data['arm']
                    return SubVel(**data)
        except requests.exceptions.RequestException as e:
            print(f"[WARNING] Failed to get input data: {e}")
        except Exception as e:
            print(f"[ERROR] Error processing input data: {e}")
        return None
    
    def post_data(self, subvel: SubVel, subpos: SubPos, subrot: SubRot) -> None:
        """
        Post the submarine's position, rotation, and velocity to the DBPackage.

        Parameters
        ----------
        subvel : SubVel
            The submarine's velocity
        subpos : SubPos
            The submarine's position
        subrot : SubRot
            The submarine's rotation
        """
        current_time = datetime.now().isoformat()

        # Post position data
        pos_data = {
            'datetime': current_time,
            'X': subpos.x,
            'Y': subpos.y,
            'Z': subpos.z
        }
        try:
            response = requests.post(self.pos_url, json=pos_data, timeout=1.0)
            if response.status_code != 201:
                print(f"[WARNING] Failed to send position data. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[WARNING] Position data request failed: {e}")

        # Post rotation data
        rot_data = {
            'datetime': current_time,
            'Roll': subrot.roll,
            'Pitch': subrot.pitch,
            'Yaw': subrot.yaw
        }
        try:
            response = requests.post(self.rot_url, json=rot_data, timeout=1.0)
            if response.status_code != 201:
                print(f"[WARNING] Failed to send rotation data. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[WARNING] Rotation data request failed: {e}")

        # Post velocity data
        vel_data = {
            'datetime': current_time,
            'Vx': subvel.x,
            'Vy': subvel.y,
            'Vz': subvel.z,
            'Roll': subvel.roll,
            'Pitch': subvel.pitch,
            'Yaw': subvel.yaw
        }
        try:
            response = requests.post(self.vel_url, json=vel_data, timeout=1.0)
            if response.status_code != 201:
                print(f"[WARNING] Failed to send velocity data. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[WARNING] Velocity data request failed: {e}")
    
    def run(self) -> None:
        """Main loop for the Unity interface."""
        print(f"[INFO] Starting Unity Interface main loop...")
        print(f"[INFO] Unity: {self.unity_ip}:{self.unity_port}")
        print(f"[INFO] Database: {self.inputs_url}:{self.inputs_port}")

        loop_count = 0
        try:
            while True:
                try:
                    # Get the submarine position, rotation, and velocity from Unity
                    sub_pos = self.get_submarine_position()
                    sub_rot = self.get_submarine_rotation()
                    sub_vel = self.get_submarine_velocity()

                    # Get the input data from the RL server
                    input_data = self.get_data()
                    if input_data:
                        # Set the submarine's velocity in Unity
                        self.set_submarine_velocity(input_data)

                    # Post the submarine's position, rotation, and velocity to the DBPackage
                    self.post_data(sub_vel, sub_pos, sub_rot)

                    # Print status every 50 loops to reduce spam
                    loop_count += 1
                    if loop_count % 50 == 0:
                        print(f"[INFO] Loop {loop_count}: Pos: ({sub_pos.x:.2f}, {sub_pos.y:.2f}, {sub_pos.z:.2f}), "
                              f"Inputs: {'Active' if input_data else 'None'}")

                    time.sleep(0.1)  # Sleep for a short duration to avoid overwhelming the server

                except KeyboardInterrupt:
                    print(f"\n[INFO] Received interrupt signal, shutting down...")
                    break
                except Exception as e:
                    print(f"[ERROR] Error in main loop: {e}")
                    time.sleep(1.0)  # Wait longer on error

        except Exception as e:
            print(f"[FATAL] Fatal error in Unity Interface: {e}")
        finally:
            print(f"[INFO] Unity Interface shutting down after {loop_count} loops")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unity Hardware Interface for AUV Training")
    parser.add_argument("--unity_ip", type=str, default="localhost", help="IP address for Unity communication")
    parser.add_argument("--unity_port", type=int, default=9999, help="Port for Unity communication")
    parser.add_argument("--inputs_url", type=str, default="localhost", help="IP address for database/inputs server")
    parser.add_argument("--inputs_port", type=int, default=5000, help="Port for database/inputs server")
    args = parser.parse_args()

    print(f"[INFO] Starting Unity Hardware Interface")
    print(f"[INFO] Arguments: {args}")

    try:
        unity_interface = UnityInterface(
            unity_ip=args.unity_ip,
            unity_port=args.unity_port,
            inputs_url=args.inputs_url,
            inputs_port=args.inputs_port
        )

        unity_interface.run()

    except Exception as e:
        print(f"[FATAL] Failed to start Unity Interface: {e}")
        exit(1)
    unity_interface = UnityInterface(unity_port=args.unity_port, inputs_url=args.inputs_url, inputs_port=args.inputs_port)
    
    unity_interface.run()