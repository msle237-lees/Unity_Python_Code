from typing import Optional
import numpy as np
import gymnasium as gym
from dataclasses import dataclass
import requests
import os
import json
import logging
from datetime import datetime


class HelperFunctions:
    def get_updates(self, url: str) -> dict:
        request = requests.get(url=url)
        if request.status_code == 200:  # expected from Unity interface
            return request.json()
        else:
            return {
                "datetime": datetime.now().isoformat(),
                "X": 0.0,
                "Y": 0.0,
                "Z": 0.0,
                "Roll": 0.0,
                "Pitch": 0.0,
                "Yaw": 0.0,
                "Vx": 0.0,
                "Vy": 0.0,
                "Vz": 0.0,
                "S1": 0.0,
                "S2": 0.0,
                "S3": 0.0,
                "Arm": 0.0
            }
            # raise Exception(f"Error: {request.status_code} - {request.text}")

    def set_updates(self, url: str, data: dict) -> json:
        request = requests.post(url=url, json=data)
        if request.status_code == 201:
            return request.json()
        else:
            raise Exception(f"Error: {request.status_code} - {request.text}")


class LoggerHelper:
    @staticmethod
    def setup_logger(name: str, log_dir: str = "logs", log_level=logging.INFO, to_file=True) -> logging.Logger:
        """
        Sets up a logger that outputs to both console and a timestamped file.
        """
        os.makedirs(log_dir, exist_ok=True)
        logger = logging.getLogger(name)
        logger.setLevel(log_level)

        if logger.hasHandlers():
            logger.handlers.clear()

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler
        if to_file:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            log_filename = os.path.join(log_dir, f"{name}_{timestamp}.log")
            fh = logging.FileHandler(log_filename)
            fh.setLevel(log_level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        return logger


@dataclass
class AUVState:
    X: float
    Y: float
    Z: float
    Roll: float
    Pitch: float
    Yaw: float
    S1: float
    S2: float
    S3: float
    Arm: float

    def to_dict(self):
        return {
            "X": self.X, "Y": self.Y, "Z": self.Z,
            "Roll": self.Roll, "Pitch": self.Pitch, "Yaw": self.Yaw,
            "S1": self.S1, "S2": self.S2, "S3": self.S3,
            "Arm": self.Arm
        }

    @staticmethod
    def from_dict(data: dict):
        return AUVState(
            X=data["X"], Y=data["Y"], Z=data["Z"],
            Roll=data["Roll"], Pitch=data["Pitch"], Yaw=data["Yaw"],
            S1=data["S1"], S2=data["S2"], S3=data["S3"],
            Arm=data["Arm"]
        )


class AUVEnv(gym.Env):
    def __init__(self, position_url, rotation_url, velocity_url, inputs_url):
        self.logger = LoggerHelper.setup_logger("AUVEnv")
        self.logger.info("Initializing AUVEnv...")

        self.position_url = position_url
        self.rotation_url = rotation_url
        self.velocity_url = velocity_url
        self.inputs_url = inputs_url

        self.expert_path = self.load_expert_path()
        self.max_steps = len(self.expert_path)
        self.step_idx = 0

        self.helper = HelperFunctions()
        self.state = AUVState(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(9,), dtype=np.float32)
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32)

        self.reward = 0
        self.done = False
        self.info = {}

        self.logger.info("AUVEnv initialized.")

    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None):
        super().reset(seed=seed)
        self.logger.info("Environment reset.")
        self.done = False
        self.step_idx = 0
        self.state = self._get_current_state()
        return self._get_observation(), self.info

    def step(self, action):
        action = np.clip(action, -1.0, 1.0)

        command = {
            "X": float(action[0]),
            "Y": float(action[1]),
            "Z": float(action[2]),
            "Roll": float(action[3]),
            "Pitch": float(action[4]),
            "Yaw": float(action[5]),
            "S1": float(action[6]),
            "S2": float(action[7]),
            "S3": float(action[8]),
            "Arm": 0
        }

        self.logger.debug(f"Sending action: {command}")
        self.helper.set_updates(self.inputs_url, command)

        self.state = self._get_current_state()
        self.reward = self._calculate_reward()

        self.logger.debug(f"Step {self.step_idx} | Reward: {self.reward:.3f} | State: {self.state}")

        self.step_idx += 1
        terminated = self.step_idx >= self.max_steps
        truncated = False

        return self._get_observation(), self.reward, terminated, truncated, self.info

    def _calculate_reward(self):
        current_pos = np.array([self.state.X, self.state.Y, self.state.Z])
        current_rot = np.array([self.state.Roll, self.state.Pitch, self.state.Yaw])
        current_vel = np.array([self.state.S1, self.state.S2, self.state.S3])

        closest = None
        min_dist = float('inf')

        for waypoint in self.expert_path:
            if any(waypoint.get(k) is None for k in ("X", "Y", "Z", "Roll", "Pitch", "Yaw", "vel_x", "vel_y", "vel_z")):
                continue

            target_pos = np.array([waypoint["X"], waypoint["Y"], waypoint["Z"]])
            dist = np.linalg.norm(current_pos - target_pos)
            if dist < min_dist:
                min_dist = dist
                closest = waypoint

        if closest:
            rot_err = np.linalg.norm(current_rot - np.array([
                closest["Roll"], closest["Pitch"], closest["Yaw"]
            ]))
            vel_err = np.linalg.norm(current_vel - np.array([
                closest["vel_x"], closest["vel_y"], closest["vel_z"]
            ]))
        else:
            rot_err = 0.0
            vel_err = 0.0

        return -min_dist - 0.1 * rot_err - 0.05 * vel_err

    def _get_current_state(self) -> AUVState:
        pos = self.helper.get_updates(self.position_url)
        rot = self.helper.get_updates(self.rotation_url)
        vel = self.helper.get_updates(self.velocity_url)
        inp = self.helper.get_updates(self.inputs_url)

        return AUVState(
            X=pos.get("X", 0.0),
            Y=pos.get("Y", 0.0),
            Z=pos.get("Z", 0.0),
            Roll=rot.get("Roll", 0.0),
            Pitch=rot.get("Pitch", 0.0),
            Yaw=rot.get("Yaw", 0.0),
            S1=inp.get("S1", 0.0),
            S2=inp.get("S2", 0.0),
            S3=inp.get("S3", 0.0),
            Arm=inp.get("Arm", 0.0)
        )

    def _get_observation(self):
        return np.array([
            self.state.X, self.state.Y, self.state.Z,
            self.state.Roll, self.state.Pitch, self.state.Yaw,
            self.state.S1, self.state.S2, self.state.S3,
            self.state.Arm
        ], dtype=np.float32)

    def get_expert_action(self) -> np.ndarray:
        """
        Return the expert action from the expert path at the current step index.
        """
        if self.step_idx < len(self.expert_path):
            wp = self.expert_path[self.step_idx]
            return np.array([
                wp.get("out_X", 0.0), wp.get("out_Y", 0.0), wp.get("out_Z", 0.0),
                wp.get("out_Roll", 0.0), wp.get("out_Pitch", 0.0), wp.get("out_Yaw", 0.0),
                wp.get("S1", 0.0), wp.get("S2", 0.0), wp.get("S3", 0.0)
            ], dtype=np.float32)
        else:
            return np.zeros(9, dtype=np.float32)

    def load_expert_path(self):
        path = os.path.join(os.path.dirname(__file__), "expert_paths/path_1.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                self.logger.info(f"Loaded expert path with {len(data)} waypoints.")
                return data
        else:
            self.logger.error(f"Expert path file not found: {path}")
            raise FileNotFoundError(f"Expert path file not found: {path}")
