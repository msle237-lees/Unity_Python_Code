#!/bin/bash

# AUV Control and Training Suite - Linux Bash Script
# This script provides easy access to common AUV system operations

set -e  # Exit on any error

echo "========================================"
echo "    AUV Control and Training Suite"
echo "========================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Check if we're in the correct directory
if [ ! -f "start.py" ]; then
    echo "ERROR: start.py not found"
    echo "Please run this script from the Unity_Python_Code directory"
    exit 1
fi

show_menu() {
    echo
    echo "Select an option:"
    echo
    echo "1. Start Complete System (Training + Hardware + Linux Sim)"
    echo "2. Start Single Machine Mode (All-in-One)"
    echo "3. Start Single Machine Fresh Training"
    echo "4. Start Training Only (Cluster Mode)"
    echo "5. Start Hardware Interface Only"
    echo "6. Start Controller (Manual Control)"
    echo "7. Start Fresh Training (Multi-Component)"
    echo "8. Continue Training from Existing Model"
    echo "9. Evaluate Trained Model"
    echo "10. Start Cloud Machine (Model Evaluation)"
    echo "11. Interactive Mode (Custom Arguments)"
    echo "0. Exit"
    echo
}

complete_system() {
    echo
    echo "Starting Complete AUV System..."
    echo "This will start: Database, Training, Hardware Interface, and Linux Simulator"
    echo
    $PYTHON_CMD start.py --start_hardware --start_linux_simulator --processes 4
}

single_machine() {
    echo
    echo "Starting Single Machine Mode (All-in-One)..."
    echo "This mode runs everything on one machine with simplified configuration"
    echo "Perfect for development, testing, or single-machine deployments"
    echo
    echo "Note: Each training process will run in parallel with its own:"
    echo "- Database instance (different ports)"
    echo "- Hardware interface"
    echo "- Unity simulator instance"
    echo
    read -p "Enter number of parallel training processes (default 4): " processes
    processes=${processes:-4}
    read -p "Enter training timesteps (default 1000000): " timesteps
    timesteps=${timesteps:-1000000}
    echo
    echo "Starting single machine AUV system with $processes parallel training process(es)..."
    $PYTHON_CMD start.py --start_hardware --start_linux_simulator --processes $processes --timesteps $timesteps --fresh
}

single_machine_fresh() {
    echo
    echo "Starting Single Machine Fresh Training..."
    echo "This mode starts fresh training optimized for single machine deployment"
    echo "Ideal for starting new training experiments on one machine"
    echo
    echo "Note: This will:"
    echo "- Start fresh training (ignore existing models)"
    echo "- Run multiple parallel training processes"
    echo "- Each process gets its own database, hardware interface, and simulator"
    echo "- Optimized settings for single machine performance"
    echo
    read -p "Enter number of parallel training processes (default 2): " processes
    processes=${processes:-2}
    read -p "Enter training timesteps (default 1000000): " timesteps
    timesteps=${timesteps:-1000000}
    echo
    echo "Starting fresh training on single machine with $processes parallel process(es)..."
    echo "Training for $timesteps timesteps..."
    $PYTHON_CMD start.py --fresh --start_hardware --start_linux_simulator --processes $processes --timesteps $timesteps
}

training_only() {
    echo
    echo "Starting Training System (Cluster Mode)..."
    echo "This will start multiple parallel training processes without simulators"
    echo "Use this mode when running on a cluster machine dedicated to training"
    echo
    read -p "Enter number of parallel training processes (default 4): " processes
    processes=${processes:-4}
    $PYTHON_CMD start.py --cluster_machine --processes $processes
}

hardware_only() {
    echo
    echo "Starting Hardware Interface Only..."
    echo "This will start the database and hardware interface for manual control"
    echo
    $PYTHON_CMD start.py --start_hardware
}

controller() {
    echo
    echo "Starting Controller for Manual Control..."
    echo "Make sure to connect your Xbox 360 or other supported controller"
    echo
    read -p "Enter Flask API IP (default localhost): " ip
    ip=${ip:-localhost}
    read -p "Enter Flask API port (default 5000): " port
    port=${port:-5000}
    $PYTHON_CMD controller.py --ip $ip --port $port
}

fresh_training() {
    echo
    echo "Starting Fresh Training..."
    echo "This will start new training from scratch with hardware and simulator"
    echo
    read -p "Enter training timesteps (default 1000000): " timesteps
    timesteps=${timesteps:-1000000}
    read -p "Enter number of parallel training processes (default 4): " processes
    processes=${processes:-4}
    $PYTHON_CMD start.py --fresh --timesteps $timesteps --processes $processes --start_hardware --start_linux_simulator
}

continue_training() {
    echo
    echo "Continuing Training from Existing Model..."
    echo
    read -p "Enter model path (default logs/run_20250709_135310/ppo_auv_model.zip): " model_path
    model_path=${model_path:-logs/run_20250709_135310/ppo_auv_model.zip}
    read -p "Enter additional timesteps (default 1000000): " timesteps
    timesteps=${timesteps:-1000000}
    $PYTHON_CMD start.py --continue_from "$model_path" --timesteps $timesteps --start_hardware --start_linux_simulator
}

evaluate_model() {
    echo
    echo "Evaluating Trained Model..."
    echo
    read -p "Enter model path (default logs/run_20250709_135310/ppo_auv_model.zip): " model_path
    model_path=${model_path:-logs/run_20250709_135310/ppo_auv_model.zip}
    read -p "Enter number of episodes (default 5): " episodes
    episodes=${episodes:-5}
    $PYTHON_CMD start.py --evaluate --model_path "$model_path" --episodes $episodes --start_hardware --start_linux_simulator
}

cloud_machine() {
    echo
    echo "Starting Cloud Machine (Model Evaluation Server)..."
    echo "This mode evaluates models from cluster machines"
    echo
    read -p "Enter machine ID (default 0): " machine_id
    machine_id=${machine_id:-0}
    $PYTHON_CMD start.py --cloud_machine --machine_id $machine_id
}

interactive_mode() {
    echo
    echo "Starting Interactive Mode..."
    echo "You will be prompted for all configuration options"
    echo
    $PYTHON_CMD start.py --interactive
}

# Main menu loop
while true; do
    show_menu
    read -p "Enter your choice (0-11): " choice

    case $choice in
        1) complete_system ;;
        2) single_machine ;;
        3) single_machine_fresh ;;
        4) training_only ;;
        5) hardware_only ;;
        6) controller ;;
        7) fresh_training ;;
        8) continue_training ;;
        9) evaluate_model ;;
        10) cloud_machine ;;
        11) interactive_mode ;;
        0)
            echo
            echo "Exiting AUV Control and Training Suite"
            echo "Thank you for using the system!"
            exit 0
            ;;
        *)
            echo "Invalid choice. Please try again."
            ;;
    esac
done
