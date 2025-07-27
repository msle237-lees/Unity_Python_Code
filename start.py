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
    parser.add_argument('--output', type=str, default="expert_paths/path_2.json")
    parser.add_argument('--start_hardware', action='store_true', help='Flag to start the hardware interface')
    parser.add_argument('--start_ai', action='store_true', help='Flag to start the AI package')
    parser.add_argument('--train', action='store_true', help='Flag to start the training process')
    parser.add_argument('--evaluate', action='store_true', help='Flag to evaluate the model')
    parser.add_argument('--fresh', action='store_true', help='Flag to start fresh training (ignore existing models)')
    parser.add_argument('--get-expert-path', action='store_true', help='Flag to get the expert path')
    args = parser.parse_args()

    # Build trainer command with optional --fresh flag
    trainer_cmd = ['python', 'modules/trainer.py']
    if args.fresh:
        trainer_cmd.append('--fresh')

    subprocesses = [
        ['python', 'modules/DBPackage.py'],           # 0
        ['python', 'modules/AIPackage.py'],           # 1
        trainer_cmd,                                   # 2
        ['python', 'modules/EvalPackage.py'],         # 3
        ['python', 'modules/NewHardwareInterface.py'],   # 4
        ['python', 'expert_path_creator.py']          # 5
    ]

    # Always start the database first
    subprocess.Popen(subprocesses[0])
    time.sleep(10)

    if args.start_hardware:
        subprocess.Popen(subprocesses[4])
        time.sleep(5)
    if args.start_ai:
        subprocess.Popen(subprocesses[1])
    if args.train:
        subprocess.Popen(subprocesses[2])
        time.sleep(5)
    if args.evaluate:
        subprocess.Popen(subprocesses[3])
        time.sleep(5)
    if args.get_expert_path:
        subprocess.Popen(subprocesses[5])
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
                    # print(f"Error terminating process: {e}")
                    pass
            sys.exit(0)

if __name__ == "__main__":
    main()
