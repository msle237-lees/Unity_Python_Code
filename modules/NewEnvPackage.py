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
    
    def __init__(self, db_url : str = f'http://localhost:', dbPort : int = 5000, expert_path_file : str = os.path.join(os.path.dirname(__file__), "expert_paths/path_1.json")):
        self.db_url = db_url + str(dbPort) + "/action"
        self.expert_path_file = expert_path_file

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
        
        # Load expert path
        if os.path.exists(expert_path_file):
            with open(expert_path_file, "r") as f:
                self.expert_path = json.load(f)
        else:
            raise FileNotFoundError(f"Expert path file not found: {expert_path_file}")
        self.step_index = 0

    def send_action(self, action : int) -> None:
        """
        Send an action to the db server.
        """
        response = requests.post(self.db_url + "/action", json={"action": action})
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

    def calculate_reward(self, agent_action: int) -> float:
        """
        Compare the agent's action to the expert action and return a reward.

        @param agent_action: Action taken by the agent (int)
        @return: reward (float)
        """
        expert_action = self.get_expert_action()

        if agent_action == expert_action:
            reward = 1.0  # Max reward for matching expert
        else:
            # Normalize the penalty based on the action distance
            distance = abs(agent_action - expert_action)
            max_distance = self.action_space.n - 1
            reward = 1.0 - (distance / max_distance)

        # Advance expert index
        self.step_index += 1
        if self.step_index >= len(self.expert_path):
            self.step_index = len(self.expert_path) - 1  # Clamp to end

        return reward

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
        Execute one step in the environment.
        @param action: Discrete action index chosen by the agent
        @return: observation, reward, terminated, truncated, info
        """
        self.send_action(action)
        observation = self.get_observation()
        reward = self.calculate_reward(action)
        # Only send action to DB if reward exceeds threshold
        REWARD_THRESHOLD = 0.9  # tweak based on your reward scale

        if reward >= REWARD_THRESHOLD:
            self.send_action(action)

        terminated = self.get_terminated()
        truncated = False  # You can implement truncation logic if needed
        info = {}

        return observation, reward, terminated, truncated, info
