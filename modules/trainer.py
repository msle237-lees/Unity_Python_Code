import os
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.logger import configure
from EnvPackage import AUVEnv  # Make sure auv_env.py contains your AUVEnv class

# === Configuration ===
position_url = "http://localhost:5000/position"
rotation_url = "http://localhost:5000/rotation"
velocity_url = "http://localhost:5000/velocity"
inputs_url = "http://localhost:5000/inputs"

log_dir = "ppo_logs"
model_path = "auv_ppo_model"
summary_csv = "episode_summary.csv"
train_timesteps = 100_000
eval_episodes = 10

os.makedirs(log_dir, exist_ok=True)

# === Create environment ===
env = AUVEnv(position_url, rotation_url, velocity_url, inputs_url)

# === Setup Stable Baselines Logger ===
logger = configure(folder=log_dir, format_strings=["stdout", "csv", "tensorboard"])

# === Initialize PPO agent ===
model = PPO("MlpPolicy", env, verbose=1)
model.set_logger(logger)

# === Train the model ===
print(f"[INFO] Training model for {train_timesteps} timesteps...")
model.learn(total_timesteps=train_timesteps)
model.save(model_path)
print(f"[INFO] Model saved to {model_path}")

# === Evaluate and log results ===
print(f"[INFO] Running evaluation over {eval_episodes} episodes...")
with open(summary_csv, "w") as f:
    f.write("episode,total_reward,steps\n")
    for episode in range(eval_episodes):
        obs, _ = env.reset()
        done = False
        total_reward = 0
        steps = 0

        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, _, _ = env.step(action)
            total_reward += reward
            steps += 1

        f.write(f"{episode},{total_reward:.2f},{steps}\n")
        print(f"[Episode {episode}] Reward: {total_reward:.2f}, Steps: {steps}")

print(f"[INFO] Evaluation results saved to {summary_csv}")
