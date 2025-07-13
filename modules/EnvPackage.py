from dataclasses import dataclass
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import requests
from typing import Tuple, Dict, Any, Optional
import json
import os


class EnvPackage(gym.Env):
    """
    Gym-compatible environment wrapper for a Unity-based AUV simulation backend.
    """

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

    @dataclass
    class PastSubInputs:
        x: float
        y: float
        z: float
        roll: float
        pitch: float
        yaw: float
        s1: float
        s2: float
        s3: float
        arm: float

    @dataclass
    class CurrentSubInputs:
        x: float
        y: float
        z: float
        roll: float
        pitch: float
        yaw: float
        s1: float
        s2: float
        s3: float
        arm: float

    def __init__(self, dbIP: str = 'localhost', dbPort: int = 5000, unityIP: str = 'localhost', unityPort: int = 9999,
                 expert_path_file: str = os.path.join(os.path.dirname(__file__), "expert_paths/path_1.json")):
        """
        Initialize the AUV environment.

        @param dbIP The IP address of the backend data server.
        @param dbPort The port used for backend data.
        @param unityIP The IP address of the Unity simulation server.
        @param unityPort The port used by Unity.
        @param expert_path_file Path to JSON file with expert trajectory
        """
        self.dbURL = f"http://{dbIP}:{dbPort}"
        self.unityURL = f"http://{unityIP}:{unityPort}"

        self.posURL = f"{self.dbURL}/position"
        self.rotURL = f"{self.dbURL}/rotation"
        self.velURL = f"{self.dbURL}/velocity"
        self.inputsURL = f"{self.dbURL}/inputs"

        self.observation_space = spaces.Box(
            low=-2.0,
            high=2.0,
            shape=(12,),
            dtype=np.float32
        )

        # Define simplified discrete action space
        # 8 directions: Forward, Back, Left, Right, Up, Down, Yaw Right, Yaw Left
        # 5 force levels: 0, 25, 50, 75, 100
        # Total: 8 * 5 = 40 possible actions
        self.num_directions = 8
        self.num_force_levels = 5
        self.action_space = spaces.Discrete(self.num_directions * self.num_force_levels)

        # Define the mapping
        self.directions = [
            "Forward",    # 0: +Y movement
            "Back",       # 1: -Y movement
            "Left",       # 2: -X movement
            "Right",      # 3: +X movement
            "Up",         # 4: +Z movement
            "Down",       # 5: -Z movement
            "Yaw Right",  # 6: +Yaw rotation
            "Yaw Left"    # 7: -Yaw rotation
        ]

        self.force_levels = [0, 25, 50, 75, 100]

        # Load expert path
        if os.path.exists(expert_path_file):
            with open(expert_path_file, "r") as f:
                self.expert_path = json.load(f)
        else:
            raise FileNotFoundError(f"Expert path file not found: {expert_path_file}")
        self.step_index = 0

    def decode_action(self, action: int) -> Tuple[str, int]:
        """Convert discrete action to direction and force level.

        Parameters
        ----------
        action : int
            Discrete action index (0-39)

        Returns
        -------
        tuple
            (direction_name, force_level)
        """
        direction_idx = action // self.num_force_levels
        force_idx = action % self.num_force_levels

        direction = self.directions[direction_idx]
        force = self.force_levels[force_idx]

        return direction, force

    def action_to_continuous(self, action: int) -> np.ndarray:
        """Convert discrete action to continuous control inputs.

        Parameters
        ----------
        action : int
            Discrete action index (0-39)

        Returns
        -------
        np.ndarray
            Continuous control vector [X, Y, Z, Roll, Pitch, Yaw, S1, S2, S3, Arm]
        """
        direction, force = self.decode_action(action)

        # Normalize force to [-1, 1] range (100 -> 1.0, 0 -> 0.0)
        normalized_force = force / 100.0

        # Initialize all controls to zero
        controls = np.zeros(10, dtype=np.float32)

        # Map direction to control axes
        if direction == "Forward":
            controls[1] = normalized_force    # +Y
        elif direction == "Back":
            controls[1] = -normalized_force   # -Y
        elif direction == "Left":
            controls[0] = -normalized_force   # -X
        elif direction == "Right":
            controls[0] = normalized_force    # +X
        elif direction == "Up":
            controls[2] = normalized_force    # +Z
        elif direction == "Down":
            controls[2] = -normalized_force   # -Z
        elif direction == "Yaw Right":
            controls[5] = normalized_force    # +Yaw
        elif direction == "Yaw Left":
            controls[5] = -normalized_force   # -Yaw

        # Always keep arm engaged
        controls[9] = 1.0  # Arm

        return controls

    def continuous_to_action(self, continuous_controls: np.ndarray) -> int:
        """Convert continuous control inputs to closest discrete action.

        Parameters
        ----------
        continuous_controls : np.ndarray
            Continuous control vector [X, Y, Z, Roll, Pitch, Yaw, S1, S2, S3, Arm]

        Returns
        -------
        int
            Closest discrete action index
        """
        # Find the dominant control axis
        control_magnitudes = np.abs(continuous_controls[:6])  # X, Y, Z, Roll, Pitch, Yaw
        max_idx = np.argmax(control_magnitudes)
        max_value = continuous_controls[max_idx]

        # Map control axis to direction
        if max_idx == 0:  # X axis
            direction_idx = 3 if max_value > 0 else 2  # Right or Left
        elif max_idx == 1:  # Y axis
            direction_idx = 0 if max_value > 0 else 1  # Forward or Back
        elif max_idx == 2:  # Z axis
            direction_idx = 4 if max_value > 0 else 5  # Up or Down
        elif max_idx == 5:  # Yaw axis
            direction_idx = 6 if max_value > 0 else 7  # Yaw Right or Yaw Left
        else:
            # Roll/Pitch not supported in simplified control scheme
            direction_idx = 0  # Default to Forward

        # Convert magnitude to force level
        magnitude = abs(max_value)
        if magnitude < 0.1:
            force_idx = 0  # 0%
        elif magnitude < 0.3:
            force_idx = 1  # 25%
        elif magnitude < 0.6:
            force_idx = 2  # 50%
        elif magnitude < 0.8:
            force_idx = 3  # 75%
        else:
            force_idx = 4  # 100%

        return direction_idx * self.num_force_levels + force_idx

    def _getSubPos(self, url: str) -> SubPos:
        response = requests.get(url)
        response.raise_for_status()
        data = {k.lower(): v for k, v in response.json().items()}
        keys = {"x", "y", "z"}
        filtered_data = {k: data.get(k, 0.0) for k in keys}
        return self.SubPos(**filtered_data)

    def _getSubRot(self, url: str) -> SubRot:
        response = requests.get(url)
        response.raise_for_status()
        data = {k.lower(): v for k, v in response.json().items()}
        keys = {"roll", "pitch", "yaw"}
        filtered_data = {k: data.get(k, 0.0) for k in keys}
        return self.SubRot(**filtered_data)

    def _getSubVel(self, url: str) -> SubVel:
        response = requests.get(url)
        response.raise_for_status()
        data = {k.lower(): v for k, v in response.json().items()}
        keys = {"x", "y", "z", "roll", "pitch", "yaw"}
        filtered_data = {k: data.get(k, 0.0) for k in keys}
        return self.SubVel(**filtered_data)

    def _setSubInputs(self, url: str, inputs: CurrentSubInputs) -> None:
        payload = {k.capitalize(): float(v) for k, v in inputs.__dict__.items()}
        response = requests.post(url, json=payload)
        if response.status_code != 201:
            raise Exception(f"Failed to set submarine inputs: {response.text}")

    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        print("[DEBUG] Environment reset() called")
        super().reset(seed=seed)
        if seed is not None:
            self.seed(seed)

        self.step_index = 0

        # Send reset command (arm = 0 triggers Unity reset)
        reset_input = self.CurrentSubInputs(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self._setSubInputs(self.inputsURL, reset_input)

        # Wait for Unity to complete the reset
        import time
        time.sleep(0.5)  # Give Unity time to reset position

        # Set arm = 1 to arm the submarine after reset
        armed_input = self.CurrentSubInputs(0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
        self._setSubInputs(self.inputsURL, armed_input)

        # Small delay to ensure the armed state is processed
        time.sleep(0.1)

        pos = self._getSubPos(self.posURL)
        rot = self._getSubRot(self.rotURL)
        vel = self._getSubVel(self.velURL)

        # Debug: Print reset position
        print(f"[DEBUG] Reset complete - Position: ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})")
        if len(self.expert_path) > 0:
            expert_start = self.expert_path[0]
            expert_pos = np.array([expert_start["X"], expert_start["Y"], expert_start["Z"]])
            current_pos = np.array([pos.x, pos.y, pos.z])
            initial_distance = np.linalg.norm(current_pos - expert_pos)
            print(f"[DEBUG] Initial distance to expert: {initial_distance:.2f}")

        observation = np.array(self.getObservation(pos, rot, vel), dtype=np.float32)

        return observation, {}

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.

        @param action Discrete action index (0-39) representing direction and force.
        @return Tuple containing: observation, reward, terminated, truncated, info
        """
        # Convert discrete action to continuous control vector
        continuous_action = self.action_to_continuous(action)

        # Rescale 'arm' from [-1, 1] to [0, 1] (though it's already 1.0)
        rescaled_arm = (continuous_action[9] + 1) / 2
        inputs = self.CurrentSubInputs(*continuous_action[:9], rescaled_arm)
        self._setSubInputs(self.inputsURL, inputs)

        # Get updated state from Unity
        pos = self._getSubPos(self.posURL)
        rot = self._getSubRot(self.rotURL)
        vel = self._getSubVel(self.velURL)

        observation = np.array(self.getObservation(pos, rot, vel), dtype=np.float32)

        # --- Expert imitation reward logic based on discrete action comparison ---
        if self.step_index < len(self.expert_path):
            expert_record = self.expert_path[self.step_index]

            # Get the expert's discrete action
            expert_action = expert_record.get("discrete_action", 0)

            # For backward compatibility, also get continuous inputs if available
            if "original_inputs" in expert_record:
                original_inputs = expert_record["original_inputs"]
                human_inputs = np.array([
                    original_inputs.get("X", 0.0),
                    original_inputs.get("Y", 0.0),
                    original_inputs.get("Z", 0.0),
                    original_inputs.get("Roll", 0.0),
                    original_inputs.get("Pitch", 0.0),
                    original_inputs.get("Yaw", 0.0),
                    original_inputs.get("S1", 0.0),
                    original_inputs.get("S2", 0.0),
                    original_inputs.get("S3", 0.0),
                    original_inputs.get("Arm", 1.0)
                ], dtype=np.float32)

                # Normalize human inputs to [-1, 1] range
                normalized_human_inputs = np.array([
                    human_inputs[0] / 128.0,   # X
                    human_inputs[1] / 128.0,   # Y
                    human_inputs[2] / 128.0,   # Z
                    human_inputs[3] / 128.0,   # Roll
                    human_inputs[4] / 128.0,   # Pitch
                    human_inputs[5] / 128.0,   # Yaw
                    human_inputs[6] / 128.0,   # S1
                    human_inputs[7] / 128.0,   # S2
                    human_inputs[8] / 128.0,   # S3
                    human_inputs[9] * 2.0 - 1.0  # Arm: convert [0,1] to [-1,1]
                ], dtype=np.float32)

                # Clip to valid action range
                normalized_human_inputs = np.clip(normalized_human_inputs, -1.0, 1.0)
            else:
                # Convert expert discrete action to continuous for comparison
                normalized_human_inputs = self.action_to_continuous(expert_action)

        else:
            # Fallback when no expert data available
            expert_action = 0  # Default action
            normalized_human_inputs = np.zeros(10, dtype=np.float32)
            normalized_human_inputs[9] = 1.0  # Keep arm engaged

        # Calculate difference between AI actions and human pilot inputs (continuous)
        input_difference = np.linalg.norm(continuous_action - normalized_human_inputs)

        # Individual component differences for detailed analysis
        component_diffs = np.abs(continuous_action - normalized_human_inputs)

        # Primary reward: negative input difference (encourages matching human pilot)
        reward = -input_difference * 5.0  # Scale factor for meaningful rewards

        # Bonus rewards for close matching
        if input_difference < 0.1:
            reward += 10.0  # Very close match
        elif input_difference < 0.2:
            reward += 5.0   # Good match
        elif input_difference < 0.5:
            reward += 2.0   # Reasonable match

        # Special bonus for matching the most important controls
        s3_diff = component_diffs[8]  # S3 difference
        arm_diff = component_diffs[9]  # Arm difference

        if s3_diff < 0.05:  # Very close S3 match
            reward += 3.0
        if arm_diff < 0.05:  # Very close Arm match
            reward += 2.0

        # Primary reward for exact discrete action match
        if action == expert_action:
            reward += 20.0  # Big bonus for exact action match

        # Secondary reward for similar actions (same direction, different force)
        ai_direction = action // self.num_force_levels
        expert_direction = expert_action // self.num_force_levels
        if ai_direction == expert_direction:
            reward += 5.0  # Bonus for correct direction

        # Episode end conditions based on input divergence
        max_input_difference = 2.0  # Allow some deviation but not too much
        terminated = bool(input_difference > max_input_difference)
        truncated = bool(self.step_index >= len(self.expert_path) - 1)  # end of demo

        # Debug: Print step information for first few steps
        if self.step_index < 5:
            direction, force = self.decode_action(action)
            expert_direction, expert_force = self.decode_action(expert_action)

            # print(f"[DEBUG] Step {self.step_index}: input_diff={input_difference:.3f}, "
            #       f"reward={reward:.2f}, terminated={terminated}, truncated={truncated}")
            # print(f"[DEBUG] AI action:     {action} -> {direction} at {force}% force")
            # print(f"[DEBUG] Expert action: {expert_action} -> {expert_direction} at {expert_force}% force")
            # print(f"[DEBUG] Action match:  {'✓' if action == expert_action else '✗'}")
            # print(f"[DEBUG] Direction match: {'✓' if ai_direction == expert_direction else '✗'}")
            # print(f"[DEBUG] Component diffs: S3={s3_diff:.3f}, Arm={arm_diff:.3f}")

        self.step_index += 1

        info = {
            "input_difference": input_difference,
            "s3_difference": s3_diff,
            "arm_difference": arm_diff,
            "max_input_difference": max_input_difference,
            "component_differences": component_diffs.tolist()
        }

        return observation, float(reward), terminated, truncated, info

    def getObservation(self, pos: SubPos, rot: SubRot, vel: SubVel) -> list:
        return [
            pos.x / 100.0, pos.y / 100.0, pos.z / 100.0,
            rot.roll / 180.0, rot.pitch / 180.0, rot.yaw / 180.0,
            vel.x / 10.0, vel.y / 10.0, vel.z / 10.0,
            vel.roll / 180.0, vel.pitch / 180.0, vel.yaw / 180.0
        ]

    def close(self) -> None:
        pass

    def seed(self, seed: Optional[int] = None) -> None:
        np.random.seed(seed)
