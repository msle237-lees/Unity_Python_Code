"""Utility to record expert demonstration paths from the running AUV system."""

import argparse
import json
import os
import time
from typing import Any, Dict, List, Optional

import requests


def _fetch(url: str) -> Optional[Dict[str, Any]]:
    """Fetch JSON data from the given URL.

    Parameters
    ----------
    url:
        Endpoint to request.

    Returns
    -------
    dict | None
        Parsed JSON response if the request succeeds, otherwise ``None``.
    """
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return res.json()
        print(f"[WARN] Failed request to {url}: {res.status_code}")
    except requests.exceptions.RequestException as exc:
        print(f"[ERROR] Request to {url} failed: {exc}")
    return None


def record_expert_path(host: str, port: int, out_file: str, interval: float = 0.1) -> None:
    """Record state and control outputs and save them to a JSON file.

    The function continuously polls the DBPackage endpoints for position,
    rotation, velocity and input command data.  Each sample is appended to an
    in-memory list until ``Arm`` in the input data becomes ``0`` which signals
    that the current episode has ended.  At that point the collected path is
    written to ``out_file`` and the list is cleared ready for the next episode.

    Parameters
    ----------
    host, port:
        Address of the running DBPackage service.
    out_file:
        Path to the JSON file where captured data should be stored.
    interval:
        Sampling interval in seconds.
    """
    base = f"http://{host}:{port}"
    pos_url = f"{base}/position"
    rot_url = f"{base}/rotation"
    vel_url = f"{base}/velocity"
    inp_url = f"{base}/inputs"

    path: List[Dict[str, Any]] = []
    print("[INFO] Recording expert path. Press Ctrl+C to stop.")

    try:
        while True:
            pos = _fetch(pos_url)
            rot = _fetch(rot_url)
            vel = _fetch(vel_url)
            inp = _fetch(inp_url)

            if None in (pos, rot, vel, inp):
                time.sleep(interval)
                continue

            step = {
                "X": pos.get("X", 0.0),
                "Y": pos.get("Y", 0.0),
                "Z": pos.get("Z", 0.0),
                "Roll": rot.get("Roll", 0.0),
                "Pitch": rot.get("Pitch", 0.0),
                "Yaw": rot.get("Yaw", 0.0),
                "vel_x": vel.get("Vx", 0.0),
                "vel_y": vel.get("Vy", 0.0),
                "vel_z": vel.get("Vz", 0.0),
                "out_X": inp.get("X", 0.0),
                "out_Y": inp.get("Y", 0.0),
                "out_Z": inp.get("Z", 0.0),
                "out_Roll": inp.get("Roll", 0.0),
                "out_Pitch": inp.get("Pitch", 0.0),
                "out_Yaw": inp.get("Yaw", 0.0),
                "S1": inp.get("S1", 0.0),
                "S2": inp.get("S2", 0.0),
                "S3": inp.get("S3", 0.0),
                "Arm": inp.get("Arm", 0.0),
            }
            path.append(step)

            if inp.get("Arm", 0) == 0 and len(path) > 0:
                print("[INFO] Arm is 0 - resetting path capture and saving data.")
                _save_path(out_file, path)
                path.clear()

            time.sleep(interval)
    except KeyboardInterrupt:
        if path:
            _save_path(out_file, path)
        print("\n[INFO] Recording stopped.")


def _save_path(file_path: str, data: List[Dict[str, Any]]) -> None:
    """Write a collected path to disk."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"[INFO] Saved {len(data)} entries to {file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create expert demonstration paths.")
    parser.add_argument("--host", type=str, default="localhost", help="DBPackage host")
    parser.add_argument("--port", type=int, default=5000, help="DBPackage port")
    parser.add_argument("--output", type=str, default="expert_paths/path_1.json", help="Output JSON file")
    parser.add_argument("--interval", type=float, default=0.1, help="Sampling interval in seconds")
    args = parser.parse_args()

    record_expert_path(args.host, args.port, args.output, args.interval)
