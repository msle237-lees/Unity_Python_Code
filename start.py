import argparse
import os
import sys
import subprocess
import time

def main():
    parser = argparse.ArgumentParser(description="Run the Unity game and Flask server.")
    parser.add_argument('--ip', type=str, default='0.0.0.0', help='IP address to bind to (default: 0.0.0.0)')
    parser.add_argument('--unity_ip', type=str, default='localhost', help='IP address for Unity communication (default: localhost)')
    parser.add_argument('--unity_port', type=int, default=9999, help='Port for Unity communication (default: 9999)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--output', type=str, default="expert_paths/path_1.json")
    parser.add_argument('--start_hardware', action='store_true', help='Flag to start the hardware interface')
    parser.add_argument('--start_ai', action='store_true', help='Flag to start the AI package')
    parser.add_argument('--train', action='store_true', help='Flag to start the training process')
    args = parser.parse_args()

    subprocesses = [
        ['python', 'modules/DBPackage.py', '--host', args.ip, '--port', str(args.port)],
        ['python', 'modules/AIPackage.py', '--host', args.ip, '--port', str(args.port)],
        ['python', 'modules/trainer.py'],
        ['python', 'modules/HardwareInterface.py', '--unity_ip', args.unity_ip, '--unity_port', str(args.unity_port)    ],
        ['python', 'modules/Virtual_Cameras.py']
    ]
    
    subprocess.Popen(subprocesses[0])

    time.sleep(10)

    if args.start_hardware:
        subprocess.Popen(subprocesses[3])
        time.sleep(5)
    if args.start_ai:
        subprocess.Popen(subprocesses[1])
    if args.train:
        subprocess.Popen(subprocesses[2])
        time.sleep(5)

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
            for proc in subprocesses:
                try:
                    proc.terminate()
                except Exception as e:
                    print(f"Error terminating process: {e}")
            sys.exit(0)

if __name__ == "__main__":
    main()
