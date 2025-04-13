import argparse
import os
import sys
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Run the Unity game and Flask server.")
    parser.add_argument('--ip', type=str, default='127.0.0.1', help='IP address to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--start-hardware', action='store_true', help='Flag to start the hardware interface')
    parser.add_argument('--start-ai', action='store_true', help='Flag to start the AI package')
    args = parser.parse_args()

    