import os
import json
import numpy as np
from EnvPackage import AUVEnv
from behavior_cloning import train_behavior_cloning_model, BCPolicy

# Config
dagger_iterations = 500
steps_per_iter = 1500
dataset_file = "dagger_dataset.json"
model_file = "bc_model.pth"

# Env setup
env = AUVEnv(
    "http://localhost:5000/position",
    "http://localhost:5000/rotation",
    "http://localhost:5000/velocity",
    "http://localhost:5000/inputs"
)

# Load or start dataset
if os.path.exists(dataset_file):
    with open(dataset_file, "r") as f:
        dataset = json.load(f)
else:
    dataset = []

# DAgger loop
for iteration in range(dagger_iterations):
    obs, _ = env.reset()
    done = False
    step_count = 0

    while not done and step_count < steps_per_iter:
        # If we have a model, use it; else take no-op
        if os.path.exists(model_file):
            policy = BCPolicy.load(model_file)
            action = policy.predict(obs)
        else:
            action = env.get_expert_action()

        # Record (obs, expert_act)
        expert_action = env.get_expert_action()
        dataset.append({
            "observation": obs.tolist(),
            "expert_action": expert_action.tolist()
        })

        # Step with model action (not expert)
        obs, reward, done, truncated, _ = env.step(action)
        step_count += 1

    # Save dataset and retrain
    with open(dataset_file, "w") as f:
        json.dump(dataset, f, indent=2)
    print(f"[DAgger] Iteration {iteration+1} collected. Retraining...")

    train_behavior_cloning_model(dataset_file, model_file)

print("[DAgger] Training complete.")
