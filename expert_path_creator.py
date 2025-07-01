"""Utility to fetch merged expert path data from the server and save it as a JSON file."""

import argparse
import json
import os
from typing import List, Dict, Optional
import requests


def _fetch_expert_path(url: str) -> Optional[List[Dict]]:
    """Fetch full expert path data from the API.

    Parameters
    ----------
    url : str
        Full URL to the /get_expert_path endpoint.

    Returns
    -------
    list of dict or None
        Parsed path data if successful, else None.
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        print(f"[WARN] Failed request to {url}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request to {url} failed: {e}")
    return None


def save_expert_path(path_data: List[Dict], out_file: str) -> None:
    """Save the filtered expert path to a JSON file.

    Parameters
    ----------
    path_data : list of dict
        Filtered expert path entries.
    out_file : str
        Output file location.
    """
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(path_data, f, indent=4)
    print(f"[INFO] Saved {len(path_data)} entries to {out_file}")


def process_and_save_expert_path(host: str, port: int, out_file: str) -> None:
    """Fetch and save the expert path from the new unified endpoint.

    Parameters
    ----------
    host : str
        API host.
    port : int
        API port.
    out_file : str
        Output file location.
    """
    url = f"http://{host}:{port}/get_expert_path"
    data = _fetch_expert_path(url)

    if not data:
        print("[ERROR] No data received.")
        return

    # Filter out steps where Arm is 0 or None
    filtered_path = [step for step in data if step.get("Arm") not in (0, None)]
    save_expert_path(filtered_path, out_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and store expert path from /get_expert_path endpoint.")
    parser.add_argument("--host", type=str, default="localhost", help="API host")
    parser.add_argument("--port", type=int, default=5000, help="API port")
    parser.add_argument("--output", type=str, default="expert_paths/path_1.json", help="Output file path")
    args = parser.parse_args()

    process_and_save_expert_path(args.host, args.port, args.output)
