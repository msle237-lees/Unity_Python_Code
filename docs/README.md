# Project Overview

This repository contains scripts and modules used for controlling and training an autonomous underwater vehicle (AUV) in a Unity simulation environment.  The code is organized as a set of small utilities and service modules that communicate via HTTP requests and WebSockets.

The key components are:

- **start.py** – Helper script that launches the Flask API and optional hardware or AI interfaces.
- **controller.py** – Reads joystick input and sends commands to the API.
- **coor_fetcher.py** – Utility for printing mouse coordinates, used for calibrating virtual camera capture regions.
- **expert_path_creator.py** – Records positions, rotations and control outputs from the running system to create demonstration paths.
- **examples/joystick.py** – Pygame example for checking joystick events.
- **modules** – Collection of larger services:
  - `DBPackage.py` – Flask API that stores and serves position, rotation, velocity and input data using SQLite.
  - `HardwareInterface.py` – Communicates with Unity, posts state data to the API and applies velocity commands.
  - `EnvPackage.py` – Reinforcement‑learning environment that interfaces with the API and loads expert paths.
  - `Virtual_Cameras.py` – Captures sections of the Unity screen and streams them over HTTP.
  - `trainer.py` – Example training script using Stable‑Baselines3 PPO.
  - `support/` – Small helpers for serving webcam streams.
- **configs/controller.json** – Mapping of joystick axes and buttons used by `controller.py`.
- **expert_paths/** – Folder for JSON files recorded with `expert_path_creator.py`.

Each module contains inline documentation describing its purpose and how it interacts with the rest of the system.  See the individual files for detailed comments.