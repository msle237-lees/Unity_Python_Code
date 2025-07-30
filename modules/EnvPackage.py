from dataclasses import dataclass
import gymnasium as gym
from gymnasium import spaces
from gymnasium.envs.registration import register
from typing import Tuple, Dict, Any, Optional
import numpy as np
import requests
import json
import os


class EnvPackage(gym.Env):
    """
    Gym-compatible environment wrapper for a Unity-based AUV simulation backend.

    @breif Used to interface with the Unity backend.
    
    Notes:
    - The EnvPackage only interacts with the db server.
    - The only way to interact with the hardware is through the db server.
    """

    @dataclass
    class SubAcceleration:
        x: float
        y: float
        z: float

    @dataclass
    class SubAngularAcceleration:
        roll: float
        pitch: float
        yaw: float
    
    def __init__(self, db_url : str = f'http://localhost:', dbPort : int = 5000):
        self.db_url = db_url + str(dbPort)
        self.expertPathURL = db_url + str(dbPort) + "/expert_path"
        self.expert_path = requests.get(self.expertPathURL).json()
        if not self.expert_path:
            raise ValueError("No expert path data found at the specified URL.")

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
        
        self.step_index = 0

    def send_action(self, action : int) -> None:
        """
        Send an action to the db server.
        """
        response = requests.post(self.db_url + "/post_action", json={"action": action})
        if response.status_code != 200:
            raise Exception(f"Failed to send action to db server: {response.status_code} {response.text}")

    def get_observation(self) -> np.ndarray:
        """
        Get the current observation from the db server.
        """
        response = requests.get(self.db_url)
        if response.status_code != 200:
            raise Exception(f"Failed to get observation from db server: {response.status_code} {response.text}")
        return np.array(response.json()["observation"])

    def get_expert_action(self, step_index : int) -> int:
        """
        Get the expert action from the expert path.
        """
        if self.expert_path is not None:
            return self.expert_path[step_index]
        else:
            return self.action_space.sample()

    def calculate_reward(self, agent_action: int, current_observation: np.ndarray) -> float:
        """
        Calculate the total reward based on:
        - action similarity to expert action
        - state similarity to expert's pose (position and orientation)

        @param agent_action: Discrete action taken by the agent
        @param current_observation: Sensor reading after action (7D: X, Y, Z, Roll, Pitch, Yaw, Arm)
        @return: Combined reward
        """
        expert_step = self.expert_path[self.step_index]

        # --- Action similarity reward ---
        expert_direction = expert_step["direction"]
        expert_force = expert_step["force_level"]
        expert_action = self.encode_action(expert_direction, expert_force)

        if agent_action == expert_action:
            action_reward = 1.0
        else:
            distance = abs(agent_action - expert_action)
            action_reward = 1.0 - (distance / (self.action_space.n - 1))  # Normalize [0, 1]

        # --- Sensor/state similarity reward ---
        expert_pose = np.array([
            expert_step["X"],
            expert_step["Y"],
            expert_step["Z"],
            expert_step["Roll"],
            expert_step["Pitch"],
            expert_step["Yaw"]
        ], dtype=np.float32)

        current_pose = current_observation[:6]  # exclude arm

        # Compute L2 distance (or use MSE if preferred)
        pose_error = np.linalg.norm(current_pose - expert_pose)
        max_error = 10.0  # Adjust based on sim range
        pose_reward = max(0.0, 1.0 - (pose_error / max_error))

        # --- Combine rewards ---
        total_reward = 0.5 * action_reward + 0.5 * pose_reward

        # Advance expert index
        self.step_index = min(self.step_index + 1, len(self.expert_path) - 1)
        return total_reward

    def runSimulation(self) -> None:
        """
        Run the simulation executable.
        """
        pass

    def get_terminated(self) -> bool:
        """
        Check if the environment has terminated.
        """
        pass
    
    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset the environment.
        """
        pass

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute one step of the environment.
        """
        self.send_action(action)
        observation = self.get_observation()
        reward = self.calculate_reward(action, observation)
        terminated = self.get_terminated()
        truncated = False
        info = {}
        return observation, reward, terminated, truncated, info
