"""
Evaluate a trained PPO model on the custom AUV Gym environment.
Logs output to JSON for comparison with expert paths.
"""

import os
import json
import torch
import numpy as np
from stable_baselines3 import PPO
from EnvPackage import EnvPackage
from datetime import datetime


def make_env():
    """
    Create the AUV environment instance (not vectorized).
    """
    return EnvPackage(dbIP="localhost", dbPort=5000, unityIP="localhost", unityPort=9999)


def evaluate_model(model_path: str, save_path: str, episodes: int = 1, steps_per_episode: int = 1024):
    """
    Evaluate the PPO model and log observations/actions.

    @param model_path: Path to the trained PPO model file.
    @param save_path: Path to the output JSON log file.
    @param episodes: Number of evaluation episodes.
    @param steps_per_episode: Max timesteps per episode.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[INFO] Using device: {device.upper()}")

    env = make_env()
    model = PPO.load(model_path, device=device)
    print(f"[INFO] Loaded model from: {model_path}")

    all_logs = []

    for ep in range(episodes):
        print(f"[DEBUG] About to reset environment for episode {ep + 1}")
        obs, _ = env.reset()
        episode_log = []
        print(f"[DEBUG] Episode {ep + 1} starting with observation: {obs[:3]}")  # Show position

        for step in range(steps_per_episode):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)

            episode_log.append({
                "timestep": step,
                "observation": obs.tolist(),
                "action": action.tolist(),
                "reward": float(reward),
                "terminated": terminated,
                "truncated": truncated,
                "info": info
            })

            if terminated or truncated:
                print(f"[INFO] Episode {ep + 1} ended early at step {step}")
                print(f"[DEBUG] Termination reason - terminated: {terminated}, truncated: {truncated}")
                print(f"[DEBUG] Final info: {info}")
                print(f"[DEBUG] Final reward: {reward}")
                break

        all_logs.append(episode_log)

    with open(save_path, "w") as f:
        json.dump(all_logs, f, indent=2)

    print(f"[INFO] Evaluation complete. Results saved to: {save_path}")


if __name__ == "__main__":
    model_file = "logs/run_20250709_135310/ppo_auv_model.zip"  # <-- Adjust this path as needed
    output_dir = "evaluation_results"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"eval_{timestamp}.json")

    evaluate_model(model_file, output_file, episodes=1, steps_per_episode=1024)
