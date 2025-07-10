"""
Evaluate a trained PPO model on the custom AUV Gym environment.
Logs output to JSON for comparison with expert paths.
"""

import os
import json
import torch
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from EnvPackage import EnvPackage  # Your custom Unity environment
from datetime import datetime


def make_env():
    """
    Create the wrapped environment instance.
    """
    return EnvPackage(dbIP="localhost", dbPort=5000, unityIP="localhost", unityPort=9999)


def evaluate_model(model_path: str, save_path: str, episodes: int = 1, steps_per_episode: int = 1024):
    """
    Evaluate the PPO model and log observations/actions.

    @param model_path Path to the saved model.
    @param save_path Output JSON file to store the evaluation trace.
    @param episodes Number of evaluation episodes to run.
    @param steps_per_episode Number of timesteps per episode.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[INFO] Using device: {device.upper()}")

    env = DummyVecEnv([make_env])
    model = PPO.load(model_path, env=env, device=device)
    print(f"[INFO] Loaded model from: {model_path}")

    all_logs = []

    for ep in range(episodes):
        obs = env.reset()
        episode_log = []

        for step in range(steps_per_episode):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)

            # Flatten obs to 1D list
            obs_list = obs[0].tolist() if isinstance(obs, np.ndarray) else obs
            action_list = action[0].tolist() if isinstance(action, np.ndarray) else action

            episode_log.append({
                "timestep": step,
                "observation": obs_list,
                "action": action_list,
                "reward": float(reward[0]),
                "terminated": bool(terminated[0]),
                "truncated": bool(truncated[0])
            })

            if terminated[0] or truncated[0]:
                print(f"[INFO] Episode {ep+1} ended early at step {step}")
                break

        all_logs.append(episode_log)

    with open(save_path, "w") as f:
        json.dump(all_logs, f, indent=2)

    print(f"[INFO] Evaluation complete. Results saved to: {save_path}")


if __name__ == "__main__":
    model_file = "logs/run_20250709_135310/ppo_auv_model.zip"  # Change to your latest run
    output_file = f"evaluation_results/eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    os.makedirs("evaluation_results", exist_ok=True)
    evaluate_model(model_file, output_file, episodes=1, steps_per_episode=1024)
