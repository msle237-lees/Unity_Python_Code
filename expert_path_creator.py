"""Utility to fetch human pilot input data and convert to discrete action format."""

import argparse
import json
import os
from typing import List, Dict, Optional
import requests
import numpy as np


class DiscreteActionConverter:
    """Converts continuous human inputs to discrete actions."""

    def __init__(self):
        # Define the discrete action space (same as in EnvPackage.py)
        self.directions = [
            "Forward",    # 0: +Y movement
            "Back",       # 1: -Y movement
            "Left",       # 2: -X movement
            "Right",      # 3: +X movement
            "Up",         # 4: +Z movement
            "Down",       # 5: -Z movement
            "Yaw Right",  # 6: +Yaw rotation
            "Yaw Left"    # 7: -Yaw rotation
        ]

        self.force_levels = [0, 25, 50, 75, 100]
        self.num_directions = 8
        self.num_force_levels = 5

    def continuous_to_action(self, human_inputs: Dict) -> int:
        """Convert human pilot inputs to discrete action index.

        Parameters
        ----------
        human_inputs : dict
            Raw human inputs from database

        Returns
        -------
        int
            Discrete action index (0-39)
        """
        # Extract and normalize human inputs to [-1, 1] range
        continuous_controls = np.array([
            human_inputs.get("X", 0.0) / 128.0,      # X
            human_inputs.get("Y", 0.0) / 128.0,      # Y
            human_inputs.get("Z", 0.0) / 128.0,      # Z
            human_inputs.get("Roll", 0.0) / 128.0,   # Roll
            human_inputs.get("Pitch", 0.0) / 128.0,  # Pitch
            human_inputs.get("Yaw", 0.0) / 128.0,    # Yaw
            human_inputs.get("S1", 0.0) / 128.0,     # S1
            human_inputs.get("S2", 0.0) / 128.0,     # S2
            human_inputs.get("S3", 0.0) / 128.0,     # S3
            human_inputs.get("Arm", 1.0)             # Arm (already 0-1)
        ], dtype=np.float32)

        # Clip to valid range
        continuous_controls = np.clip(continuous_controls, -1.0, 1.0)

        # Find the dominant control axis (X, Y, Z, Roll, Pitch, Yaw)
        control_magnitudes = np.abs(continuous_controls[:6])
        max_idx = np.argmax(control_magnitudes)
        max_value = continuous_controls[max_idx]

        # Map control axis to direction
        if max_idx == 0:  # X axis
            direction_idx = 3 if max_value > 0 else 2  # Right or Left
        elif max_idx == 1:  # Y axis
            direction_idx = 0 if max_value > 0 else 1  # Forward or Back
        elif max_idx == 2:  # Z axis
            direction_idx = 4 if max_value > 0 else 5  # Up or Down
        elif max_idx == 5:  # Yaw axis
            direction_idx = 6 if max_value > 0 else 7  # Yaw Right or Yaw Left
        else:
            # Roll/Pitch not supported in simplified control scheme
            direction_idx = 0  # Default to Forward

        # Convert magnitude to force level
        magnitude = abs(max_value)
        if magnitude < 0.1:
            force_idx = 0  # 0%
        elif magnitude < 0.3:
            force_idx = 1  # 25%
        elif magnitude < 0.6:
            force_idx = 2  # 50%
        elif magnitude < 0.8:
            force_idx = 3  # 75%
        else:
            force_idx = 4  # 100%

        return direction_idx * self.num_force_levels + force_idx

    def decode_action(self, action: int) -> tuple:
        """Convert discrete action to direction and force level."""
        direction_idx = action // self.num_force_levels
        force_idx = action % self.num_force_levels

        direction = self.directions[direction_idx]
        force = self.force_levels[force_idx]

        return direction, force


def _fetch_inputs_only(url: str) -> Optional[List[Dict]]:
    """Fetch only input data from the API.

    Parameters
    ----------
    url : str
        Full URL to the /inputs endpoint.

    Returns
    -------
    list of dict or None
        Parsed input data if successful, else None.
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # If it's a single input record, wrap in list
            if isinstance(data, dict):
                return [data]
            return data
        print(f"[WARN] Failed request to {url}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request to {url} failed: {e}")
    return None


def _fetch_all_inputs(host: str, port: int) -> Optional[List[Dict]]:
    """Fetch all input records from the database.

    Parameters
    ----------
    host : str
        API host.
    port : int
        API port.

    Returns
    -------
    list of dict or None
        All input records if successful, else None.
    """
    url = f"http://{host}:{port}/get_inputs_only"
    return _fetch_inputs_only(url)


def save_expert_actions(action_data: List[Dict], out_file: str) -> None:
    """Save the discrete action data to a JSON file.

    Parameters
    ----------
    action_data : list of dict
        Discrete action entries.
    out_file : str
        Output file location.
    """
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(action_data, f, indent=4)
    print(f"[INFO] Saved {len(action_data)} discrete actions to {out_file}")


def process_and_save_expert_actions(host: str, port: int, out_file: str) -> None:
    """Fetch human pilot input data and convert to discrete actions.

    Parameters
    ----------
    host : str
        API host.
    port : int
        API port.
    out_file : str
        Output file location.
    """
    data = _fetch_all_inputs(host, port)

    if not data:
        print("[ERROR] No input data received.")
        return

    # Filter out steps where Arm is 0 or None (when pilot wasn't actively controlling)
    filtered_inputs = [step for step in data if step.get("Arm") not in (0, None)]

    print(f"[INFO] Fetched {len(data)} total input records")
    print(f"[INFO] Filtered to {len(filtered_inputs)} records where Arm is engaged")

    if not filtered_inputs:
        print("[ERROR] No valid input records found.")
        return

    # Convert to discrete actions
    converter = DiscreteActionConverter()
    expert_actions = []

    for i, input_record in enumerate(filtered_inputs):
        # Convert continuous inputs to discrete action
        discrete_action = converter.continuous_to_action(input_record)
        direction, force = converter.decode_action(discrete_action)

        # Create new record with discrete action and metadata
        action_record = {
            "timestep": i,
            "datetime": input_record.get("datetime"),
            "discrete_action": discrete_action,
            "direction": direction,
            "force_percent": force,
            "original_inputs": {
                "X": input_record.get("X", 0.0),
                "Y": input_record.get("Y", 0.0),
                "Z": input_record.get("Z", 0.0),
                "Roll": input_record.get("Roll", 0.0),
                "Pitch": input_record.get("Pitch", 0.0),
                "Yaw": input_record.get("Yaw", 0.0),
                "S1": input_record.get("S1", 0.0),
                "S2": input_record.get("S2", 0.0),
                "S3": input_record.get("S3", 0.0),
                "Arm": input_record.get("Arm", 1.0)
            }
        }
        expert_actions.append(action_record)

    print(f"[INFO] Converted to {len(expert_actions)} discrete actions")

    # Show some statistics
    action_counts = {}
    for record in expert_actions:
        action = record["discrete_action"]
        direction = record["direction"]
        force = record["force_percent"]
        key = f"{direction} {force}%"
        action_counts[key] = action_counts.get(key, 0) + 1

    print(f"[INFO] Action distribution:")
    for action_type, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        percentage = (count / len(expert_actions)) * 100
        print(f"  {action_type}: {count} times ({percentage:.1f}%)")

    if expert_actions:
        print(f"[INFO] Sample action record: {expert_actions[0]}")

    save_expert_actions(expert_actions, out_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert human pilot inputs to discrete actions for training.")
    parser.add_argument("--host", type=str, default="localhost", help="API host")
    parser.add_argument("--port", type=int, default=5000, help="API port")
    parser.add_argument("--output", type=str, default="expert_paths/discrete_actions.json", help="Output file path")
    args = parser.parse_args()

    process_and_save_expert_actions(args.host, args.port, args.output)
