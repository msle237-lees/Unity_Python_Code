import argparse
import os
import sys
import subprocess
import time

def main():
    parser = argparse.ArgumentParser(description="Run the Unity game and Flask server.")
    parser.add_argument('--ip', type=str, default='127.0.0.1', help='IP address to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--start_hardware', action='store_true', help='Flag to start the hardware interface')
    parser.add_argument('--start_ai', action='store_true', help='Flag to start the AI package')
    args = parser.parse_args()

    subprocesses = [
        ['python', 'modules/DBPackage.py', '--host', args.ip, '--port', str(args.port)],
        ['python', 'modules/AIPackage.py', '--host', args.ip, '--port', str(args.port)],
        ['python', 'modules/HardwareInterface.py'],
        ['python', 'modules/Virtual_Cameras.py']
    ]

    if args.start_hardware:
        subprocess.Popen(subprocesses[2])
    if args.start_ai:
        subprocess.Popen(subprocesses[1])

    subprocess.Popen(subprocesses[0])
    # subprocess.Popen(subprocesses[3])

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()