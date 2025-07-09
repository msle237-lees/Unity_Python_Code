from dataclasses import dataclass
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import requests
from typing import Tuple, Dict, Any, Optional

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

    def __init__(self, dbIP: str = 'localhost', dbPort: int = 5000, unityIP: str = 'localhost', unityPort: int = 9999):
        """
        Initialize the AUV environment.

        @param dbIP The IP address of the backend data server.
        @param dbPort The port used for backend data.
        @param unityIP The IP address of the Unity simulation server.
        @param unityPort The port used by Unity.
        """
        self.dbURL = f"http://{dbIP}:{dbPort}"
        self.unityURL = f"http://{unityIP}:{unityPort}"

        self.posURL = f"{self.dbURL}/position"
        self.rotURL = f"{self.dbURL}/rotation"
        self.velURL = f"{self.dbURL}/velocity"
        self.inputsURL = f"{self.dbURL}/inputs"

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(12,),
            dtype=np.float32
        )

        self.action_space = spaces.Box(
            low=np.array([-1]*9 + [0], dtype=np.float32),
            high=np.array([1]*9 + [1], dtype=np.float32),
            shape=(10,),
            dtype=np.float32
        )

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
        raw_data = response.json()
        data = {k.lower(): v for k, v in raw_data.items()}
        
        valid_keys = {"x", "y", "z", "roll", "pitch", "yaw"}
        filtered_data = {k: data.get(k, 0.0) for k in valid_keys}

        missing = valid_keys - filtered_data.keys()
        if missing:
            print(f"[WARN] Missing keys in velocity response: {missing}. Defaulting to 0.0")

        return self.SubVel(**filtered_data)
    
    def _setSubInputs(self, url: str, inputs: CurrentSubInputs) -> None:
        """
        Send control inputs to the simulation backend via HTTP POST.

        @param url The target endpoint URL.
        @param inputs The current control inputs to send.
        """
        # Capitalize keys and cast values to native float
        payload = {k.capitalize(): float(v) for k, v in inputs.__dict__.items()}
        
        response = requests.post(url, json=payload)
        if response.status_code != 201:
            raise Exception(f"Failed to set submarine inputs: {response.text}")

    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset the environment to the initial state.

        @param seed Random seed for reproducibility.
        @param options Additional reset options (unused).
        @return A tuple of (observation, info) as required by Gymnasium.
        """
        super().reset(seed=seed)
        if seed is not None:
            self.seed(seed)

        zero_input = self.CurrentSubInputs(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self._setSubInputs(self.inputsURL, zero_input)

        pos = self._getSubPos(self.posURL)
        rot = self._getSubRot(self.rotURL)
        vel = self._getSubVel(self.velURL)

        observation = np.array(self.getObservation(pos, rot, vel), dtype=np.float32)
        
        return observation, {}  # ✅ Return a tuple (obs, info)


    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.

        @param action The control input vector (10-dimensional).
        @return Tuple containing: observation, reward, terminated, truncated, info
        """
        inputs = self.CurrentSubInputs(*action)
        self._setSubInputs(self.inputsURL, inputs)

        pos = self._getSubPos(self.posURL)
        rot = self._getSubRot(self.rotURL)
        vel = self._getSubVel(self.velURL)

        observation = np.array(self.getObservation(pos, rot, vel), dtype=np.float32)

        # Placeholder reward/termination logic
        reward = 0.0
        terminated = False
        truncated = False
        info = {}

        return observation, reward, terminated, truncated, info

    def getObservation(self, pos: SubPos, rot: SubRot, vel: SubVel) -> list:
        """
        Convert submarine position, rotation, and velocity into a single observation list.

        @param pos SubPos dataclass
        @param rot SubRot dataclass
        @param vel SubVel dataclass
        @return List of 12 float values
        """
        return [
            pos.x, pos.y, pos.z,
            rot.roll, rot.pitch, rot.yaw,
            vel.x, vel.y, vel.z,
            vel.roll, vel.pitch, vel.yaw
        ]

    def close(self) -> None:
        """
        Cleanup resources (stub).
        """
        pass

    def seed(self, seed: Optional[int] = None) -> None:
        """
        Set the seed for the environment RNG.

        @param seed Random seed.
        """
        np.random.seed(seed)
