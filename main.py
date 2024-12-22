# This main script is used as a program manager to execute the necessary functions to run the program.
# Options allowed:
# 1. Run the program in the default mode, which is to run the program with AI controls in Real World.
# 2. Run the program in the simulation mode, which is to run the program with AI controls in a simulated environment.
# 3. Run the program in the manual mode, which is to run the program with manual controls in Real World.
# 4. Run the program in the manual simulation mode, which is to run the program with manual controls in a simulated environment.

# Import necessary python libraries
import sys
import os
import argparse
from datetime import datetime

# Import modules from the project
from modules import DBHandler, MovementPackage

# Define the functions for each mode
# Default mode: Run the program with AI controls in Real World
def default_mode():
    from modules import AIPackage
    from modules.RealWorld import Cameras, HardwareInterface
    while True:
        pass

# Simulation mode: Run the program with AI controls in a simulated environment
def simulation_mode():
    from modules import AIPackage, Simulation
    from modules.Virtual import Cameras, HardwareInterface
    while True:
        pass

# Manual mode: Run the program with manual controls in Real World
def manual_mode():
    from modules.RealWorld import Cameras, HardwareInterface
    while True:
        pass

# Manual simulation mode: Run the program with manual controls in a simulated environment
def manual_simulation_mode():
    from modules import Simulation
    from modules.Virtual import Cameras, HardwareInterface
    while True:
        pass

# Run the program in the selected mode
if __name__ == '__main__':
    # Define the command line arguments and parse them
    parser = argparse.ArgumentParser(description='Run the program in different modes.')
    parser.add_argument('--mode', type=str, default='default', help='The mode to run the program. Default is default.', choices=['default', 'simulation', 'manual', 'manual_simulation'])
    parser.add_argument('--debug', type=bool, default=False, help='Whether to run the program in debug mode. Default is False.')
    parser.add_argument('--log', type=bool, default=False, help='Whether to log the program output. Default is False.')
    parser.add_argument('--log_path', type=str, default='logs/', help='The path to save the log files. Default is logs/.')
    parser.add_argument('--ip', type=str, default='0.0.0.0', help='The IP address of the server. Default is set to be broadcasted.')
    parser.add_argument('--port', type=int, default=5000, help='The port of the server. Default is 5000. DB port is <port_argument> + 1')
    args = parser.parse_args()

    if args.mode == 'default':
        # Run the program in the default mode
        default_mode()
    elif args.mode == 'simulation':
        # Run the program in the simulation mode
        simulation_mode()
    elif args.mode == 'manual':
        # Run the program in the manual mode
        manual_mode()
    elif args.mode == 'manual_simulation':
        # Run the program in the manual simulation mode
        manual_simulation_mode()

    # Print the program execution completion message
    print('Program execution completed.')