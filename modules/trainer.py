"""
Train an AUV control policy using PPO with a custom Gym environment, running on CPU.
Supports continuing training from existing model checkpoints.
"""

import os
import argparse
import numpy as np
import torch
from datetime import datetime
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.policies import ActorCriticPolicy
from stable_baselines3.common.torch_layers import MlpExtractor
from EnvPackage import EnvPackage  # Adjust if in a different module


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

def make_env():
    """
    Create a wrapped environment instance.
    """
    env = EnvPackage(
        dbIP="localhost",
        dbPort=5000,
        unityIP="localhost",
        unityPort=9999,
        expert_path_file="modules/expert_paths/path_2.json"
    )
    return env


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
    parser.add_argument("--fresh", action="store_true", help="Force fresh training (ignore existing models)")
    args = parser.parse_args()

    # Force CPU usage instead of GPU
    device = "cpu"

    # Validate custom environment
    check_env(make_env(), warn=True)

    # Create vectorized environment
    env = DummyVecEnv([make_env])

    # Determine which model to load
    existing_model_path = None

    if args.fresh:
        pass  # Ignore existing models
    elif args.continue_from:
        if os.path.exists(args.continue_from):
            existing_model_path = args.continue_from
        else:
            existing_model_path = find_latest_model()
    else:
        existing_model_path = find_latest_model()

    if existing_model_path:
        # Load existing model
        model = PPO.load(existing_model_path, env=env, device=device)

        # Update tensorboard log directory for continued training
        log_dir = os.path.join("logs", datetime.now().strftime("run_%Y%m%d_%H%M%S_continued"))
        model.tensorboard_log = log_dir
        os.makedirs(log_dir, exist_ok=True)

    else:
        # Logging directory
        log_dir = os.path.join("logs", datetime.now().strftime("run_%Y%m%d_%H%M%S"))
        os.makedirs(log_dir, exist_ok=True)

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
    model.learn(total_timesteps=total_timesteps)

    # Save trained model
    model_path = os.path.join(log_dir, "ppo_auv_model.zip")
    model.save(model_path)

    # Cleanup
    env.close()


if __name__ == "__main__":
    main()
