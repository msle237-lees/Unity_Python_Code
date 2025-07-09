"""
Train an AUV control policy using PPO with a custom Gym environment.
"""

import os
import gym
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import DummyVecEnv
from EnvPackage import EnvPackage  # Adjust if in a different module
from datetime import datetime


def make_env():
    """
    Create a wrapped environment instance.
    """
    env = EnvPackage(dbIP="localhost", dbPort=5000, unityIP="localhost", unityPort=9999)
    return env


def main():
    # Environment validation (optional, for debugging)
    print("[INFO] Validating custom Gym environment...")
    check_env(make_env(), warn=True)

    # Create a vectorized environment
    env = DummyVecEnv([make_env])

    # Set up logging directory
    log_dir = os.path.join("logs", datetime.now().strftime("run_%Y%m%d_%H%M%S"))
    os.makedirs(log_dir, exist_ok=True)

    print(f"[INFO] Logging to {log_dir}")

    # Create PPO model
    model = PPO(
        policy="MlpPolicy",
        env=env,
        verbose=1,
        tensorboard_log=log_dir,
        n_steps=5096,
        batch_size=64,
        gae_lambda=0.95,
        gamma=0.99,
        ent_coef=0.01,
        learning_rate=2.5e-4,
        clip_range=0.2,
    )

    # Train the model
    total_timesteps = 1_000_000
    print(f"[INFO] Beginning training for {total_timesteps} timesteps...")
    model.learn(total_timesteps=total_timesteps)

    # Save the model
    model_path = os.path.join(log_dir, "ppo_auv_model.zip")
    model.save(model_path)
    print(f"[INFO] Model saved to {model_path}")

    # Close the environment
    env.close()

if __name__ == "__main__":
    main()
