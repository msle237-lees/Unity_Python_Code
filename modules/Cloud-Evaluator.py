"""
Cloud-Evaluator: Evaluates models on the cloud machine and returns performance scores.
Used in distributed training setup where multiple cluster machines send models to a central cloud evaluator.
"""

import os
import sys
import json
import argparse
import numpy as np
from datetime import datetime
from stable_baselines3 import PPO
from EnvPackage import EnvPackage


def evaluate_model_for_cloud(model_path: str, host: str = "localhost", port: int = 5000,
                           episodes: int = 10, steps_per_episode: int = 1024, machine_id: int = 0):
    """
    Evaluate a model and return performance score for cloud comparison.

    Parameters
    ----------
    model_path : str
        Path to the model to evaluate
    host : str
        Database host
    port : int
        Database port
    episodes : int
        Number of evaluation episodes
    steps_per_episode : int
        Maximum steps per episode
    machine_id : int
        ID of the machine that sent this model

    Returns
    -------
    dict
        Evaluation results with model path, score, and metadata
    """

    # Create environment for evaluation
    env = EnvPackage(
        dbIP=host,
        dbPort=port,
        unityIP="localhost",
        unityPort=9999,
        expert_path_file="modules/expert_paths/path_2.json"
    )

    # Load the model
    try:
        model = PPO.load(model_path, device="cpu")
    except Exception as e:
        return {
            "model_path": model_path,
            "machine_id": machine_id,
            "score": -1000.0,  # Very low score for failed models
            "error": str(e),
            "episodes_completed": 0,
            "evaluation_time": datetime.now().isoformat()
        }

    # Run evaluation episodes
    total_reward = 0.0
    total_steps = 0
    episodes_completed = 0
    episode_rewards = []

    for episode in range(episodes):
        try:
            obs, _ = env.reset()
            episode_reward = 0.0
            episode_steps = 0

            for _ in range(steps_per_episode):
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, _ = env.step(action)

                episode_reward += reward
                episode_steps += 1

                if terminated or truncated:
                    break

            total_reward += episode_reward
            total_steps += episode_steps
            episodes_completed += 1
            episode_rewards.append(episode_reward)

        except Exception as e:
            # If an episode fails, continue with others
            print(f"Episode {episode} failed: {e}")
            continue

    # Calculate performance metrics
    if episodes_completed > 0:
        mean_reward = total_reward / episodes_completed
        mean_steps = total_steps / episodes_completed
        std_reward = np.std(episode_rewards) if len(episode_rewards) > 1 else 0.0

        # Calculate a composite score (higher is better)
        # Reward is primary factor, consistency (low std) is secondary
        score = mean_reward - (std_reward * 0.1)  # Penalize inconsistency slightly
    else:
        mean_reward = -1000.0
        mean_steps = 0
        std_reward = 0.0
        score = -1000.0

    # Cleanup
    env.close()

    # Return evaluation results
    results = {
        "model_path": model_path,
        "machine_id": machine_id,
        "score": float(score),
        "mean_reward": float(mean_reward),
        "std_reward": float(std_reward),
        "mean_steps": float(mean_steps),
        "episodes_completed": episodes_completed,
        "total_episodes": episodes,
        "episode_rewards": [float(r) for r in episode_rewards],
        "evaluation_time": datetime.now().isoformat()
    }

    return results


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Cloud model evaluator for distributed training")
    parser.add_argument("--host", type=str, default="localhost", help="Database host")
    parser.add_argument("--port", type=int, default=5000, help="Database port")
    parser.add_argument("--model_path", type=str, required=True, help="Path to model to evaluate")
    parser.add_argument("--machine_id", type=int, default=0, help="ID of machine that sent the model")
    parser.add_argument("--episodes", type=int, default=10, help="Number of evaluation episodes")
    parser.add_argument("--steps_per_episode", type=int, default=1024, help="Max steps per episode")
    parser.add_argument("--output_file", type=str, help="Optional file to save results")

    args = parser.parse_args()

    # Validate model path
    if not os.path.exists(args.model_path):
        print(f"Error: Model file not found: {args.model_path}")
        return

    # Run evaluation
    print(f"Evaluating model: {args.model_path}")
    print(f"Machine ID: {args.machine_id}")
    print(f"Episodes: {args.episodes}")

    results = evaluate_model_for_cloud(
        model_path=args.model_path,
        host=args.host,
        port=args.port,
        episodes=args.episodes,
        steps_per_episode=args.steps_per_episode,
        machine_id=args.machine_id
    )

    # Print results to stdout (for start.py to capture)
    print(json.dumps(results))

    # Optionally save to file
    if args.output_file:
        with open(args.output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {args.output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()