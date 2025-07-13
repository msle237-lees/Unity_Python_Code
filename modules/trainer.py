"""
Train an AUV control policy using PPO with a custom Gym environment, running on CPU.
Supports continuing training from existing model checkpoints.
"""

import os
import argparse
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.policies import ActorCriticPolicy
from stable_baselines3.common.torch_layers import MlpExtractor
from EnvPackage import EnvPackage


class CustomMLPPolicy(ActorCriticPolicy):
    """
    Custom MLP Policy with a larger network architecture for improved performance.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            net_arch=dict(pi=[512, 256, 128], vf=[512, 256, 128]),
            activation_fn=torch.nn.ReLU
        )

def make_env(flask_ip="localhost", flask_port=5000, unity_ip="localhost", unity_port=9999, expert_path_file="modules/expert_paths/path_2.json"):
    """
    Create a wrapped environment instance.
    """
    def _init():
        env = EnvPackage(
            dbIP=flask_ip,
            dbPort=flask_port,
            unityIP=unity_ip,
            unityPort=unity_port,
            expert_path_file=expert_path_file
        )
        return env
    return _init


def find_latest_model():
    """Find the most recent model checkpoint."""
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        return None

    # Get all run directories
    run_dirs = [d for d in os.listdir(logs_dir) if d.startswith("run_")]
    if not run_dirs:
        return None

    # Sort by timestamp (newest first)
    run_dirs.sort(reverse=True)

    # Look for model file in the most recent run
    for run_dir in run_dirs:
        model_path = os.path.join(logs_dir, run_dir, "ppo_auv_model.zip")
        if os.path.exists(model_path):
            return model_path

    return None


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Train AUV control policy with PPO")
    parser.add_argument("--continue_from", type=str, default='logs/run_20250709_135310/ppo_auv_model.zip', help="Path to existing model to continue training from")
    parser.add_argument("--timesteps", type=int, default=1_000_000, help="Number of training timesteps")
    parser.add_argument("--fresh", type=str, default="False", help="Force fresh training (ignore existing models)")
    parser.add_argument("--episodes", type=int, default=1, help="Number of evaluation episodes")
    parser.add_argument("--steps_per_episode", type=int, default=1024, help="Max timesteps per evaluation episode")
    parser.add_argument("--evaluate", type=str, default="False", help="Flag to evaluate a trained model")
    parser.add_argument("--model_path", type=str, default="logs/runs", help="Path to save the trained model")
    parser.add_argument("--expert_path_file", type=str, default="modules/expert_paths/path_2.json", help="Path to expert demonstration file")
    parser.add_argument("--flask_ip", type=str, default="localhost", help="Flask API IP address")
    parser.add_argument("--flask_port", type=int, default=5000, help="Flask API port")
    parser.add_argument("--unity_ip", type=str, default="localhost", help="Unity simulation IP address")
    parser.add_argument("--unity_port", type=int, default=9999, help="Unity simulation port")
    args = parser.parse_args()

    # Convert string boolean arguments to actual booleans
    args.fresh = args.fresh.lower() == "true"
    args.evaluate = args.evaluate.lower() == "true"

    # Force CPU usage instead of GPU
    device = "cpu"
    print(f"[INFO] Using device: {device.upper()} (forced CPU mode)")

    # Validate custom environment
    print("[INFO] Validating custom Gym environment...")
    check_env(make_env(args.flask_ip, args.flask_port, args.unity_ip, args.unity_port, args.expert_path_file)(), warn=True)

    # Create vectorized environment
    env = DummyVecEnv([make_env(args.flask_ip, args.flask_port, args.unity_ip, args.unity_port, args.expert_path_file)])

    # Determine which model to load
    existing_model_path = None

    if args.fresh:
        print("[INFO] Fresh training requested, ignoring existing models...")
    elif args.continue_from:
        if os.path.exists(args.continue_from):
            existing_model_path = args.continue_from
            print(f"[INFO] Using specified model: {existing_model_path}")
        else:
            print(f"[ERROR] Specified model not found: {args.continue_from}")
            print("[INFO] Falling back to latest model search...")
            existing_model_path = find_latest_model()
    else:
        existing_model_path = find_latest_model()

    if existing_model_path:
        print(f"[INFO] Found existing model: {existing_model_path}")
        print("[INFO] Loading model to continue training...")

        # Load existing model
        model = PPO.load(existing_model_path, env=env, device=device)

        # Update tensorboard log directory for continued training
        log_dir = args.model_path
        model.tensorboard_log = log_dir
        os.makedirs(log_dir, exist_ok=True)
        print(f"[INFO] Continuing training, logging to {log_dir}")

    else:
        print("[INFO] No existing model found, starting fresh training...")

        # Logging directory
        log_dir = args.model_path
        os.makedirs(log_dir, exist_ok=True)
        print(f"[INFO] Logging to {log_dir}")

        # Initialize new PPO model
        model = PPO(
            policy=CustomMLPPolicy,
            env=env,
            device=device,
            verbose=1,
            tensorboard_log=log_dir,
            n_steps=5120,
            batch_size=512,
            gae_lambda=0.95,
            gamma=0.99,
            ent_coef=0.01,
            learning_rate=5e-4,
            clip_range=0.2,
        )

    # Train model
    total_timesteps = args.timesteps
    if existing_model_path:
        print(f"[INFO] Continuing training for {total_timesteps} additional timesteps...")
    else:
        print(f"[INFO] Beginning fresh training for {total_timesteps} timesteps...")

    model.learn(total_timesteps=total_timesteps)

    # Save trained model
    model_path = os.path.join(log_dir, "ppo_auv_model.zip")
    model.save(model_path)
    print(f"[INFO] Model saved to {model_path}")

    if existing_model_path:
        print(f"[INFO] Training continued from: {existing_model_path}")
        print(f"[INFO] New model saved to: {model_path}")

    # Cleanup
    env.close()


if __name__ == "__main__":
    main()
