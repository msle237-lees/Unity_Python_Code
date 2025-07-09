"""
Train an AUV control policy using PPO with a custom Gym environment, utilizing GPU (CUDA) for acceleration.
"""

import os
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
    Custom MLP Policy with a larger network architecture to improve GPU utilization.
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
    env = EnvPackage(dbIP="localhost", dbPort=5000, unityIP="localhost", unityPort=9999)
    return env


def main():
    # Check for CUDA support
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[INFO] Using device: {device.upper()}")

    # Validate custom environment
    print("[INFO] Validating custom Gym environment...")
    check_env(make_env(), warn=True)

    # Create vectorized environment
    env = DummyVecEnv([make_env])

    # Logging directory
    log_dir = os.path.join("logs", datetime.now().strftime("run_%Y%m%d_%H%M%S"))
    os.makedirs(log_dir, exist_ok=True)
    print(f"[INFO] Logging to {log_dir}")

    # Initialize PPO model
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
        learning_rate=2.5e-4,
        clip_range=0.2,
    )

    # Train model
    total_timesteps = 1_000_000
    print(f"[INFO] Beginning training for {total_timesteps} timesteps...")
    model.learn(total_timesteps=total_timesteps)

    # Save trained model
    model_path = os.path.join(log_dir, "ppo_auv_model.zip")
    model.save(model_path)
    print(f"[INFO] Model saved to {model_path}")

    # Cleanup
    env.close()


if __name__ == "__main__":
    main()
