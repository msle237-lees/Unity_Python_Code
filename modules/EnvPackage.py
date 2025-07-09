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
                 expert_path_file: str = "expert_paths/expert_path.json"):
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
            low=-1.0,
            high=1.0,
            shape=(12,),
            dtype=np.float32
        )

        self.action_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(10,),
            dtype=np.float32
        )

        # Load expert path
        if os.path.exists(expert_path_file):
            with open(expert_path_file, "r") as f:
                self.expert_path = json.load(f)
        else:
            raise FileNotFoundError(f"Expert path file not found: {expert_path_file}")
        self.step_index = 0

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
        super().reset(seed=seed)
        if seed is not None:
            self.seed(seed)

        self.step_index = 0

        zero_input = self.CurrentSubInputs(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self._setSubInputs(self.inputsURL, zero_input)

        pos = self._getSubPos(self.posURL)
        rot = self._getSubRot(self.rotURL)
        vel = self._getSubVel(self.velURL)

        observation = np.array(self.getObservation(pos, rot, vel), dtype=np.float32)

        return observation, {}

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        rescaled_arm = (action[9] + 1) / 2
        inputs = self.CurrentSubInputs(*action[:9], rescaled_arm)
        self._setSubInputs(self.inputsURL, inputs)

        pos = self._getSubPos(self.posURL)
        rot = self._getSubRot(self.rotURL)
        vel = self._getSubVel(self.velURL)

        observation = np.array(self.getObservation(pos, rot, vel), dtype=np.float32)

        # --- Expert imitation reward logic ---
        if self.step_index < len(self.expert_path):
            expert = self.expert_path[self.step_index]
            expert_pos = np.array([expert["X"], expert["Y"], expert["Z"]])
        else:
            expert_pos = np.array([pos.x, pos.y, pos.z])  # No reward after expert ends

        current_pos = np.array([pos.x, pos.y, pos.z])
        distance = np.linalg.norm(current_pos - expert_pos)

        reward = -distance
        if distance < 0.25:
            reward += 1.0

        terminated = distance > 10.0
        truncated = self.step_index >= len(self.expert_path) - 1

        self.step_index += 1

        info = {"distance_to_expert": distance}

        return observation, reward, terminated, truncated, info

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
