"""
Evaluate a trained PPO model on the custom AUV Gym environment.
Logs output to JSON for comparison with expert paths.
"""

import os
import json
import torch
import argparse
import numpy as np
from stable_baselines3 import PPO
from EnvPackage import EnvPackage
from datetime import datetime


def make_env(flask_ip="localhost", flask_port=5000, unity_ip="localhost", unity_port=9999, expert_path_file="modules/expert_paths/path_2.json"):
    """
    Create the AUV environment instance (not vectorized).
    """
    return EnvPackage(dbIP=flask_ip, dbPort=flask_port, unityIP=unity_ip, unityPort=unity_port, expert_path_file=expert_path_file)


def evaluate_model(model_path: str, save_path: str, episodes: int = 1, steps_per_episode: int = 1024,
                  flask_ip="localhost", flask_port=5000, unity_ip="localhost", unity_port=9999,
                  expert_path_file="modules/expert_paths/path_2.json"):
    """
    Evaluate the PPO model and log observations/actions.

    @param model_path: Path to the trained PPO model file.
    @param save_path: Path to the output JSON log file.
    @param episodes: Number of evaluation episodes.
    @param steps_per_episode: Max timesteps per episode.
    @param flask_ip: Flask API IP address.
    @param flask_port: Flask API port.
    @param unity_ip: Unity simulation IP address.
    @param unity_port: Unity simulation port.
    @param expert_path_file: Path to expert demonstration file.
    """
    device = "cpu"
    print(f"[INFO] Using device: {device.upper()} (forced CPU mode)")

    env = make_env(flask_ip, flask_port, unity_ip, unity_port, expert_path_file)
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Evaluate AUV control policy")
    parser.add_argument("--episodes", type=int, default=1, help="Number of evaluation episodes")
    parser.add_argument("--steps_per_episode", type=int, default=1024, help="Max timesteps per evaluation episode")
    parser.add_argument("--model_path", type=str, default="logs/run_20250709_135310/ppo_auv_model.zip", help="Path to the trained model")
    parser.add_argument("--expert_path_file", type=str, default="modules/expert_paths/path_2.json", help="Path to expert demonstration file")
    parser.add_argument("--flask_ip", type=str, default="localhost", help="Flask API IP address")
    parser.add_argument("--flask_port", type=int, default=5000, help="Flask API port")
    parser.add_argument("--unity_ip", type=str, default="localhost", help="Unity simulation IP address")
    parser.add_argument("--unity_port", type=int, default=9999, help="Unity simulation port")
    args = parser.parse_args()

    output_dir = "evaluation_results"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"eval_{timestamp}.json")

    evaluate_model(
        model_path=args.model_path,
        save_path=output_file,
        episodes=args.episodes,
        steps_per_episode=args.steps_per_episode,
        flask_ip=args.flask_ip,
        flask_port=args.flask_port,
        unity_ip=args.unity_ip,
        unity_port=args.unity_port,
        expert_path_file=args.expert_path_file
    )
