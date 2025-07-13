from datetime import datetime
import subprocess
import argparse
import requests
import logging
import shutil
import socket
import json
import time
import sys
import os

# Function to log messages
def _log_message(directory, label, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = f"{directory}/{label}.log"
    with open(log_file, "a") as f:
        output = f"[{timestamp}] {message}\n"
        f.write(output)
        print(output, end='')
    logging.info(f"[{label}] {message}")

# Function to pause execution until user input
def pause():
    while not input("Press Enter to continue..."):
        pass

# Function to start a process
def _start_process(directory, command, label):
    """Start a subprocess with continuous output logging.
    
    Args:
        command (list): Command to execute as list of strings
        label (str): Label for logging identification
    """
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Log output in real-time
    for line in iter(process.stdout.readline, ''):
        _log_message(directory, label, line.strip())
    
    process.stdout.close()
    return process

# Function to terminate a process
def _terminate_process(process, label):
    try:
        process.terminate()
        _log_message(label, "Process terminated")
    except Exception as e:
        _log_message(label, f"Error terminating process: {e}")

def _interactive(args):
    for arg in arg:
        if input(f'Would you like to change {arg}? (y/n) (Current: {args[arg]}): ') == "y":
            args[arg] = input(f"Enter new value for {arg}: ")
    return args

def _get_sims():
    dir = os.path.join(os.path.dirname(__file__), "Sims")
    if not os.path.exists(dir):
        os.makedirs(dir)
        
    # Download and extract Linux simulator
    linux_url = "https://github.com/ksu-auv-team/Unity_Sim_2025/releases/download/v1.0.0/7-12-2025-Linux.zip"
    linux_zip = os.path.join(dir, "7-12-2025-Linux.zip")
    if not os.path.exists(os.path.join(dir, "7-12-2025-Linux")):
        print("Downloading Linux simulator...")
        response = requests.get(linux_url)
        with open(linux_zip, 'wb') as f:
            f.write(response.content)
        shutil.unpack_archive(linux_zip, dir)
        os.remove(linux_zip)
        
    # Download and extract Windows simulator
    windows_url = "https://github.com/ksu-auv-team/Unity_Sim_2025/releases/download/v1.0.0/7-12-2025-Windows.zip"
    windows_zip = os.path.join(dir, "7-12-2025-Windows.zip")
    if not os.path.exists(os.path.join(dir, "7-12-2025-Windows")):
        print("Downloading Windows simulator...")
        response = requests.get(windows_url)
        with open(windows_zip, 'wb') as f:
            f.write(response.content)
        shutil.unpack_archive(windows_zip, dir)
        os.remove(windows_zip)

def main():
    # Create the necessary directories if they don't exist
    for directory in ["logs", "evaluation_results", "expert_paths"]:
        directory_path = os.path.join(os.path.dirname(__file__), directory)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    log_labels = ["CM-DBPackage", "Trainer", "EvalPackage", "HardwareInterface", "ExpertPathCreator"]

    start_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    directory = f"logs/{start_time}"
    if not os.path.exists(directory):
        os.makedirs(directory)

    config_dir = os.path.join(os.path.dirname(__file__), "configs")
    default_config = """{
            "xbox_360": {
                "name": "Xbox 360 Controller",
                "deadzone": 0.1,
                "inverted": true,
                "axis": {
                    "X": 0,
                    "Y": 1,
                    "Z": 4,
                    "Yaw": 3,
                    "S3": 2
                },
                "button": {
                    "S1_Increase": {
                        "button": 5
                    },
                    "S1_Decrease": {
                        "button": 4
                    },
                    "S2_Increase": {
                        "button": 1
                    },
                    "S2_Decrease": {
                        "button": 0
                    },
                    "Arm": {
                        "button": 7
                    }
                },
                "hat": {
                }
            }
        }"""
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        with open(os.path.join(config_dir, "controller.json"), "w") as f:
            f.write(default_config)
    
    # Define subprocesses and their corresponding scripts
    subprocesses = {
        "CM-DBPackage": ["modules/CM-DBPackage.py"],
        "Trainer": ["modules/trainer.py"],
        "EvalPackage": ["modules/EvalPackage.py"],
        "HardwareInterface": ["modules/HardwareInterface.py"],
        "LinuxSimulator": ["Sims/7-12-2025-Linux/AUV_Sim.x86_64"],
        "WindowsSimulator": ["Sims/7-12-2025-Windows/0008-AUVSim_With_Python_Interface.exe"]
    }
    
    # Define command line arguments
    parser = argparse.ArgumentParser(description="Start the AUV AI Training system")
    
    # CM-DBPackage arguments
    parser.add_argument("--fip", "--flask_ip", type=str, default="0.0.0.0", help="IP address for Flask API")
    parser.add_argument("--fsport", "--flask_start_port", type=int, default=5000, help="Port for Flask API")
    
    # Unity interface arguments
    parser.add_argument("--usip", "--unity_ip", type=str, default="localhost", help="IP address for Unity communication")
    parser.add_argument("--usport", "--unity_start_port", type=int, default=9999, help="Port for Unity communication")
    
    # Expert path creator arguments
    parser.add_argument("--expert_path_file", type=str, default="expert_paths/path_2.json", help="File containing expert paths")
    
    # Hardware interface arguments
    parser.add_argument("--start_hardware", action="store_true", help="Flag to start the hardware interface")
    # Also uses --fip, --fsport, --usip, --usport
    
    # Training arguments
    parser.add_argument("--continue_from", type=str, default='logs/run_20250709_135310/ppo_auv_model.zip', help="Path to existing model to continue training from")
    parser.add_argument("--timesteps", type=int, default=1_000_000, help="Number of training timesteps")
    parser.add_argument("--fresh", action="store_true", help="Force fresh training (ignore existing models)")
    parser.add_argument("--processes", type=int, default=5, help="Number of processes to use for training")
    parser.add_argument("--episodes", type=int, default=1, help="Number of evaluation episodes")
    parser.add_argument("--steps_per_episode", type=int, default=1024, help="Max timesteps per evaluation episode")
    parser.add_argument("--evaluate", action="store_true", help="Flag to evaluate a trained model")
    parser.add_argument("--model_path", type=str, default=f"logs/runs/{start_time}", help="Path to the trained model for saving")
    # Also uses --expert_path_file, --fip, --fsport
    
    # Evaluation arguments (removing duplicates)
    parser.add_argument("--host", type=str, default="localhost", help="API host")
    parser.add_argument("--port", type=int, default=5000, help="API port")
    # Uses --fip, --fsport, --model_path, --expert_path_file, --processes

    # Hardware interface arguments (duplicate removed)
    
    # Linux simulator arguments
    parser.add_argument("--start_linux_simulator", action="store_true", help="Flag to start the Linux simulator")
    parser.add_argument("--linux_simulator_path", type=str, default="Sims/7-12-2025-Linux/AUV_Sim.x86_64", help="Path to the Linux simulator")
    parser.add_argument("--linux_simulator_args", type=str, default="-batchmode -nographics", help="Arguments for the Linux simulator")
    parser.add_argument("--linux_simulator_env", type=str, default="DISPLAY=:0", help="Environment variables for the Linux simulator")
    parser.add_argument("--linux_simulator_display_number", type=int, default=0, help="Display number for the Linux simulator")
    # Also uses --usip, --usport
    
    # Windows simulator arguments
    parser.add_argument("--start_windows_simulator", action="store_true", help="Flag to start the Windows simulator")
    parser.add_argument("--windows_simulator_path", type=str, default="Sims/7-12-2025-Windows/0008-AUVSim_With_Python_Interface.exe", help="Path to the Windows simulator")
    parser.add_argument("--windows_simulator_args", type=str, default="--batchmode -nographics", help="Arguments for the Windows simulator")
    parser.add_argument("--windows_simulator_env", type=str, default="", help="Environment variables for the Windows simulator")
    parser.add_argument("--windows_simulator_display_number", type=int, default=1, help="Display number for the Windows simulator")
    # Also uses --usip, --usport

    # Standard arguments
    
    # Debug
    parser.add_argument("--debug", action="store_true", help="Flag to enable debug mode")
    
    # Logging
    parser.add_argument("--log_level", type=str, default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    parser.add_argument("--log_dir", type=str, default=f"logs/{start_time}", help="Directory for log files")
    parser.add_argument("--log_labels", type=str, default=[label for label in subprocesses.keys()], help="Labels for log files")
    parser.add_argument("--log_file_extension", type=str, default=".log", help="Extension for log files")
    parser.add_argument("--log_format", type=str, default='%(asctime)s - %(levelname)s - %(message)s', help="Format for log messages")
    parser.add_argument("--log_date_format", type=str, default="%Y-%m-%d %H:%M:%S", help="Date format for log messages")
    parser.add_argument("--log_file_mode", type=str, default="a", help="Mode for writing to log files (a for append, w for write)")
    
    # Cluster / Cloud Arguments
    parser.add_argument("--cluster_machine", action="store_true", help="Flag to indicate cluster machine")
    parser.add_argument("--cloud_machine", action="store_true", help="Flag to indicate cloud machine")
    parser.add_argument("--machine_id", type=int, default=0, help="ID for the machine")
    parser.add_argument("--total_machines", type=int, default=1, help="Total number of machines")
    default_ip = socket.gethostbyname(socket.gethostname())
    parser.add_argument("--machine_ip", type=str, default=default_ip, help="IP address for current machine")
    parser.add_argument("--cloud_ip", type=str, default="localhost", help="IP address for cloud machine")
    parser.add_argument("--cloud_port", type=int, default=5000, help="Port for cloud machine")
    parser.add_argument("--cloud_log_level", type=str, default="INFO", help="Logging level for cloud machine (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    parser.add_argument("--cloud_log_dir", type=str, default=f"logs/{start_time}/cloud", help="Directory for log files on cloud machine")
    parser.add_argument("--cloud_log_file_extension", type=str, default=".log", help="Extension for log files on cloud machine")
    
    # Interactively ask for arguments
    parser.add_argument("--interactive", action="store_true", help="Flag to interactively ask for arguments")
    # Parse arguments
    args = parser.parse_args()
    
    if args.interactive:
        args = _interactive(args)
        
    # Check if the simulators need to be downloaded
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "Sims")):
        _get_sims()
    
    log_dir = args.log_dir
    log_labels = args.log_labels
    log_file_extension = args.log_file_extension
    log_files = {}
    for label in log_labels:
        log_file = f"{log_dir}/{label}{log_file_extension}"
        log_files[label] = log_file
    log_files["main"] = f"{log_dir}/main{log_file_extension}"

    # Start logging the main process
    _log_message(log_dir, "main", "Main process started")
    _log_message(log_dir, "main", f"Arguments passed: {args}")
    _log_message(log_dir, "main", f"Log directory: {log_dir}")
        
    # Training
    # Arguments needed for training
    # Arguments Needed:
        # continue from
        # timesteps
        # fresh
        # train
        # processes
        # episodes
        # steps per episode
        # evaluate
        # model path
        # expert path file
        # flask ip
        # flask start port
        # unity ip
        # unity start port
        # start hardware
    # Processes needed:
        # CM-DBPackage
        # Trainer
        # HardwareInterface
        # Sim
    
    _log_message(log_dir, "main", "Generating Training Processes...")
    training_processes = {"CM-DBPackage": [], "Trainer": [], "HardwareInterface": [], "LinuxSimulator": [], "WindowsSimulator": []}

    # Generate processes for each instance
    for i in range(args.processes):
        # CM-DBPackage
        training_processes["CM-DBPackage"].append([
            "python",
            "modules/CM-DBPackage.py",
            "--host", args.fip,
            "--port", str(args.fsport + i)
        ])

        # Trainer
        training_processes["Trainer"].append([
            "python",
            "modules/trainer.py",
            "--continue_from", args.continue_from,
            "--timesteps", str(args.timesteps),
            "--fresh", str(args.fresh),
            "--episodes", str(args.episodes),
            "--steps_per_episode", str(args.steps_per_episode),
            "--evaluate", str(args.evaluate),
            "--model_path", f"{args.model_path}_{i}",
            "--expert_path_file", args.expert_path_file,
            "--flask_ip", args.fip,
            "--flask_port", str(args.fsport + i),
            "--unity_ip", args.usip,
            "--unity_port", str(args.usport + i)
        ])

        # HardwareInterface
        training_processes["HardwareInterface"].append([
            "python",
            "modules/HardwareInterface.py",
            "--inputs_url", args.fip,
            "--inputs_port", str(args.fsport + i),
            "--unity_ip", args.usip,
            "--unity_port", str(args.usport + i)
        ])

        # Simulators
        if args.start_linux_simulator:
            training_processes["LinuxSimulator"].append([
                "./Sims/7-12-2025-Linux/AUV_Sim.x86_64",
                "-batchmode",
                "-nographics",
                "-port", str(args.usport + i)
            ])
        if args.start_windows_simulator:
            training_processes["WindowsSimulator"].append([
                ".\\Sims\\7-12-2025-Windows\\0008-AUVSim_With_Python_Interface.exe",
                "-batchmode",
                "-nographics",
                "-port", str(args.usport + i)
            ])

    _log_message(log_dir, "main", "Training Processes Generated")
        
    # Evaluation
    # Arguments needed for evaluation
    # Arguments Needed:
        # evaluate
        # host
        # port
        # episodes
        # steps per episode
        # model path
        # expert path file
        # processes
        # flask ip
        # flask start port
        # unity ip
        # unity start port
    # Processes needed:
        # CM-DBPackage
        # EvalPackage
        # HardwareInterface
        # Sim
        
    _log_message(log_dir, "main", "Generating Evaluation Processes...")
    evaluation_processes = {"CM-DBPackage": [], "EvalPackage": [], "HardwareInterface": [], "LinuxSimulator": [], "WindowsSimulator": []}

    # Generate evaluation processes for each instance
    for i in range(args.processes):
        # CM-DBPackage
        evaluation_processes["CM-DBPackage"].append([
            "python",
            "modules/CM-DBPackage.py",
            "--host", args.fip,
            "--port", str(args.fsport + i)
        ])

        # EvalPackage
        evaluation_processes["EvalPackage"].append([
            "python",
            "modules/EvalPackage.py",
            "--episodes", str(args.episodes),
            "--steps_per_episode", str(args.steps_per_episode),
            "--model_path", f"{args.model_path}_{i}",
            "--expert_path_file", args.expert_path_file,
            "--flask_ip", args.fip,
            "--flask_port", str(args.fsport + i),
            "--unity_ip", args.usip,
            "--unity_port", str(args.usport + i)
        ])

        # HardwareInterface
        evaluation_processes["HardwareInterface"].append([
            "python",
            "modules/HardwareInterface.py",
            "--inputs_url", args.fip,
            "--inputs_port", str(args.fsport + i),
            "--unity_ip", args.usip,
            "--unity_port", str(args.usport + i)
        ])

        # Simulators
        if args.start_linux_simulator:
            evaluation_processes["LinuxSimulator"].append([
                "./Sims/7-12-2025-Linux/AUV_Sim.x86_64",
                "-batchmode",
                "-nographics",
                "-ip", args.usip,
                "-port", str(args.usport + i)
            ])
        if args.start_windows_simulator:
            evaluation_processes["WindowsSimulator"].append([
                ".\\Sims\\7-12-2025-Windows\\0008-AUVSim_With_Python_Interface.exe",
                "-batchmode",
                "-nographics",
                "-ip", args.usip,
                "-port", str(args.usport + i)
            ])
    _log_message(log_dir, "main", "Evaluation Processes Generated")
    
    if args.cluster_machine:
        while True:
            _log_message(log_dir, "main", "Starting Cluster Processes...")
            # Start the necessary processes in seperate threads and log their output in real-time and with the necessary labels for training
            import threading

            def start_process_thread(i):
                _log_message(log_dir, "main", f"Starting Process {i}")
                if args.start_linux_simulator:
                    training_processes["LinuxSimulator"][i] = _start_process(log_dir, training_processes["LinuxSimulator"][i], "LinuxSimulator")
                if args.start_windows_simulator:
                    training_processes["WindowsSimulator"][i] = _start_process(log_dir, training_processes["WindowsSimulator"][i], "WindowsSimulator")
                training_processes["CM-DBPackage"][i] = _start_process(log_dir, training_processes["CM-DBPackage"][i], "CM-DBPackage")
                training_processes["Trainer"][i] = _start_process(log_dir, training_processes["Trainer"][i], "Trainer")
                training_processes["HardwareInterface"][i] = _start_process(log_dir, training_processes["HardwareInterface"][i], "HardwareInterface")
                _log_message(log_dir, "main", f"Process {i} Started")

            threads = []
            for i in range(args.processes):
                thread = threading.Thread(target=start_process_thread, args=(i,))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Wait for the trainer process to finish
            for i in range(args.processes):
                _log_message(log_dir, "main", f"Waiting for Process {i} to finish")
                training_processes["Trainer"][i].wait()
                _log_message(log_dir, "main", f"Process {i} Finished")
            
            _log_message(log_dir, "main", "Training Processes Finished.")
            _log_message(log_dir, "main", "Ensuring all processes are closed...")
            for process in training_processes.values():
                for p in process:
                    _terminate_process(p, "main")
            _log_message(log_dir, "main", "Starting Evaluation Processes...")
            
            def start_eval_process_thread(i):
                _log_message(log_dir, "main", f"Starting Evaluation Process {i}")
                if args.start_linux_simulator:
                    evaluation_processes["LinuxSimulator"][i] = _start_process(log_dir, evaluation_processes["LinuxSimulator"][i], "LinuxSimulator")
                if args.start_windows_simulator:
                    evaluation_processes["WindowsSimulator"][i] = _start_process(log_dir, evaluation_processes["WindowsSimulator"][i], "WindowsSimulator")
                evaluation_processes["CM-DBPackage"][i] = _start_process(log_dir, evaluation_processes["CM-DBPackage"][i], "CM-DBPackage")
                evaluation_processes["EvalPackage"][i] = _start_process(log_dir, evaluation_processes["EvalPackage"][i], "EvalPackage")
                evaluation_processes["HardwareInterface"][i] = _start_process(log_dir, evaluation_processes["HardwareInterface"][i], "HardwareInterface")
                _log_message(log_dir, "main", f"Evaluation Process {i} Started")

            eval_threads = []
            for i in range(args.processes):
                thread = threading.Thread(target=start_eval_process_thread, args=(i,))
                eval_threads.append(thread)
                thread.start()

            # Wait for all evaluation threads to complete
            for thread in eval_threads:
                thread.join()
                        
            # Wait for the evaluation process to finish
            for i in range(args.processes):
                _log_message(log_dir, "main", f"Waiting for Evaluation Process {i} to finish")
                evaluation_processes["EvalPackage"][i].wait()
                _log_message(log_dir, "main", f"Evaluation Process {i} Finished")
                
            _log_message(log_dir, "main", "Cluster Processes Finished")
            _log_message(log_dir, "main", "Main process finished")
            _log_message(log_dir, "main", "Ensuring all processes are closed...")
            for process in training_processes.values():
                for p in process:
                    _terminate_process(p, "main")
            
            # Evaluate and compare models
            _log_message(log_dir, "main", "Evaluating generated models...")
            
            # Read evaluation results from files
            eval_results = []
            for i in range(args.processes):
                result_file = f"{args.log_dir}/evaluation_results_{i}.json"
                with open(result_file, 'r') as f:
                    eval_results.append(json.load(f))
            
            # Compare models and find best performing one
            best_model_idx = max(range(len(eval_results)), 
                            key=lambda i: eval_results[i]['mean_reward'])
            
            # Save the best model with metadata
            best_model_path = f"{args.model_path}/best_model.zip"
            best_model_source = f"{args.model_path}/model_{best_model_idx}.zip"
            shutil.copy2(best_model_source, best_model_path)
            
            # Log evaluation results
            _log_message(log_dir, "main", f"Best model: {best_model_idx}")
            _log_message(log_dir, "main", f"Best model performance: {eval_results[best_model_idx]}")
            _log_message(log_dir, "main", f"Best model saved to: {best_model_path}")
            
            # Wait for user to be ready to send the best model to the cloud machine
            _log_message(log_dir, "main", "Ready to send best model to cloud machine?")
            pause()
            
            # # Send the best model stats to the cloud machine
            # # Zip the best file
            # shutil.make_archive(f"{args.model_path}/best_model", 'zip', f"{args.model_path}/best_model.zip")
            # # Send the zip file to the cloud machine
            # os.system(f"scp {args.model_path}/best_model.zip {args.cloud_machine_ip}:{args.cloud_machine_path}")
            # _log_message(log_dir, "main", "Best model sent to cloud machine")
            
            # # Wait for new data from the cloud machine selection. 
            # _log_message(log_dir, "main", "Waiting for new data from cloud machine...")
            # delete_models = False
            # while not delete_models:
            #     try:
            #         data = requests.get(f"http://{args.cloud_machine_ip}:{args.cloud_machine_port}/best_model")
            #         if data.status_code == 200:
            #             if data.json()["machine_id"] != args.machine_id:
            #                 delete_models = True
            #     except:
            #         time.sleep(1)
            
            # # Then either delete all models and pull from github
            # if delete_models:
            #     _log_message(log_dir, "main", "Deleting all models and pulling from github...")
            #     if os.path.exists(args.model_path):
            #         shutil.rmtree(args.model_path)
            #     os.system(f"git clone {args.github_url} {args.model_path}")
            #     _log_message(log_dir, "main", "All models deleted and pulled from github")
                
            # # or delete the bad models and push the good one to github
            # else:
            #     _log_message(log_dir, "main", "Deleting bad models and pushing good one to github...")
            #     for models in os.listdir(args.model_path):
            #         if models != f"model_{best_model_idx}.zip":
            #             os.remove(f"{args.model_path}/{models}")
            #     os.system(f"git add {args.model_path}")
            #     os.system(f"git commit -m 'Deleted bad models and pushed good one to github'")
            #     os.system(f"git push")
            #     _log_message(log_dir, "main", "Bad models deleted and good one pushed to github")
                            
            # Check if we are done
            if input("Continue? (y/n): ") == "n":
                _log_message(log_dir, "main", "Main process finished")
                break
            
        # End Loop
        _log_message(log_dir, "main", "Main process finished")
        _log_message(log_dir, "main", "Exiting...")
        
        for process in evaluation_processes.values():
            for p in process:
                _terminate_process(p, "main")
        
    if args.cloud_machine:
        _log_message(log_dir, "main", "Starting Cloud Processes...")
        cloud_processes = {"Cloud-DBPackage": [], "Cloud-Evaluator": []}
        
        # Cloud-DBPackage
        for i in range(args.processes):
            cloud_processes["Cloud-DBPackage"].append([
                "python",
                "modules/Cloud-DBPackage.py",
                "--host", args.fip,
                "--port", str(args.fsport + i)
            ])
        
        # Ensure a folder for models exists
        if not os.path.exists(args.model_path):
            os.makedirs(args.model_path)
        
        # Starting Cloud-DBPackage processes
        _log_message(log_dir, "main", "Starting Cloud-DBPackage processes...")
        for i, command in enumerate(cloud_processes["Cloud-DBPackage"]):
            _log_message(log_dir, "main", f"Starting Cloud-DBPackage process {i}")
            _start_process(log_dir, command, f"Cloud-DBPackage-{i}")
        _log_message(log_dir, "main", "All Cloud-DBPackage processes started")
        
        # Wait for models to be sent from the cluster machines
        _log_message(log_dir, "main", "Waiting for models to be sent from cluster machines...")
        while True:
            if len(os.listdir(args.model_path)) == args.total_machines:
                break
            time.sleep(1)
        
        # Evaluate the models
        for i, models in enumerate(os.listdir(args.model_path)):
            _log_message(log_dir, "main", f"Starting evaluation of {models}...")
            cloud_processes["Cloud-Evaluator"].append(
                subprocess.Popen(
                    [
                        "python",
                        "modules/Cloud-Evaluator.py",
                        "--host", args.fip,
                        "--port", str(args.fsport + i),
                        "--model_path", f"{args.model_path}/{models}",
                        "--machine_id", str(args.machine_id)
                    ],
                    stdout=subprocess.PIPE
                )
            )
        
        # Wait for evaluation to finish
        for i in range(len(cloud_processes["Cloud-Evaluator"])):
            cloud_processes["Cloud-Evaluator"][i].wait()
            
        # Take the returned data and store it in the database
        _log_message(log_dir, "main", "Evaluating models...")
        # Convert the data from the processes to a dictionary
        eval_data = {}
        for process in cloud_processes["Cloud-Evaluator"]:
            data = json.loads(process.stdout.read())
            eval_data[data["model_path"]] = data["score"]
        
        # Get the best model
        best_model = max(eval_data, key=eval_data.get)
        
        # Send the best model to the cluster machines
        _log_message(log_dir, "main", "Sending best model to cluster machines...")
        response = requests.post(f"http://{args.cloud_machine_ip}:{args.cloud_machine_port}/best_model", json={
            "machine_id": args.machine_id,
            "model_path": best_model,
            "score": eval_data[best_model]
        })   
        if response.status_code == 201:
            _log_message(log_dir, "main", "Best model sent to cluster machines")
        else:
            _log_message(log_dir, "main", "Failed to send best model to cluster machines")
        
        _log_message(log_dir, "main", "All models evaluated")
        
if __name__ == "__main__":
    main()