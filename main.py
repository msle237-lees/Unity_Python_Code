from flask import Flask, render_template, jsonify
import subprocess
import argparse
import logging
import sys
import os


# Set up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.debug("Logging initialized")

# Parse command line arguments
parser = argparse.ArgumentParser(description='Flask App for Camera Control')
parser.add_argument('--host', type=str, default='localhost', help='Host address')
parser.add_argument('--port', type=int, default=5000, help='Port number')
parser.add_argument('-RWCP', '--camera_package', type=bool, default=False, help='Use camera package')
parser.add_argument('-MP', '--movement_package', type=bool, default=False, help='Use movement package')
parser.add_argument('-RWHI', '--hardware_interface', type=bool, default=False, help='Use hardware interface')
parser.add_argument('-AI', '--ai_package', type=bool, default=False, help='Use AI package')
parser.add_argument('-VHI', '--virtual_hardware_interface', type=bool, default=False, help='Use virtual hardware interface')
parser.add_argument('-VCP', '--virtual_camera_package', type=bool, default=False, help='Use virtual camera package')

def run_AI_package():
    # Run the AI package script
    logger.debug("Running AI package script")
    subprocess.run(['python', 'modules/AI.py'])

def run_camera_package():
    # Run the camera package script
    logger.debug("Running camera package script")
    subprocess.run(['python', 'modules/RWModules/Cameras.py'])

def run_DBHandler():
    # Run the DBHandler script
    logger.debug("Running DBHandler script")
    subprocess.run(['python', 'modules/DBHandler.py'])

def run_hardware_interface():
    # Run the hardware interface script
    logger.debug("Running hardware interface script")
    subprocess.run(['python', 'modules/RWModules/HardwareInterface.py'])

def run_movement_package():
    # Run the movement package script
    logger.debug("Running movement package script")
    subprocess.run(['python', 'modules/MovementPackage.py'])

def run_VirtualModules():
    # Run the VirtualModules script
    logger.debug("Running VirtualModules script")
    subprocess.run(['python', 'modules/VirtualModules/HardwareInterface.py'])
    subprocess.run(['python', 'modules/VirtualModules/Cameras.py'])

# Create the flask app
app = Flask(__name__)
logger.debug("Flask app created")

# Create the homepage route
@app.route('/')
def index():
    # Render the index.html template
    return render_template('index.html')

# Start the Flask app
if __name__ == '__main__':
    # Parse the command line arguments
    args = parser.parse_args()

    if args.ai_package:
        run_AI_package()
    if args.camera_package:
        run_camera_package()
    if args.DBHandler:
        run_DBHandler()
    if args.hardware_interface:
        run_hardware_interface()
    if args.movement_package:
        run_movement_package()

    # Run the Flask app
    app.run(host=args.host, port=args.port, debug=True)
