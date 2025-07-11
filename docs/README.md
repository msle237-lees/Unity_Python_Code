# AUV Control and Training Suite Documentation

This repository contains a comprehensive collection of Python scripts and modules for controlling and training an autonomous underwater vehicle (AUV) in a Unity simulation environment. The system is designed as a modular architecture with small utilities and service modules that communicate via HTTP requests and WebSockets.

## Table of Contents

- [AUV Control and Training Suite Documentation](#auv-control-and-training-suite-documentation)
  - [Table of Contents](#table-of-contents)
  - [System Architecture](#system-architecture)
    - [Communication Flow](#communication-flow)
  - [Installation and Setup](#installation-and-setup)
    - [Prerequisites](#prerequisites)
    - [Dependencies Installation](#dependencies-installation)
    - [Key Dependencies](#key-dependencies)
    - [Quick Start](#quick-start)
  - [Core Components](#core-components)
    - [Main Scripts](#main-scripts)
      - [start.py](#startpy)
      - [controller.py](#controllerpy)
      - [expert\_path\_creator.py](#expert_path_creatorpy)
    - [Modules Directory](#modules-directory)
      - [modules/DBPackage.py](#modulesdbpackagepy)
      - [modules/HardwareInterface.py](#moduleshardwareinterfacepy)
      - [modules/EnvPackage.py](#modulesenvpackagepy)
      - [modules/KwasiEnvPackage.py](#moduleskwasienvpackagepy)
      - [modules/Virtual\_Cameras.py](#modulesvirtual_cameraspy)
      - [modules/trainer.py](#modulestrainerpy)
    - [Support Modules](#support-modules)
      - [modules/support/WebCamService.py](#modulessupportwebcamservicepy)
      - [modules/support/routes.py](#modulessupportroutespy)
      - [modules/support/camera\_0.py \& camera\_1.py](#modulessupportcamera_0py--camera_1py)
    - [Examples Directory](#examples-directory)
      - [examples/joystick.py](#examplesjoystickpy)
  - [API Endpoints](#api-endpoints)
    - [DBPackage API (Default: http://localhost:5000)](#dbpackage-api-default-httplocalhost5000)
      - [Position Endpoints](#position-endpoints)
      - [Rotation Endpoints](#rotation-endpoints)
      - [Velocity Endpoints](#velocity-endpoints)
      - [Input Endpoints](#input-endpoints)
      - [Expert Path Endpoint](#expert-path-endpoint)
    - [Virtual Cameras API (Default: http://localhost:5001)](#virtual-cameras-api-default-httplocalhost5001)
    - [Webcam Support API](#webcam-support-api)
  - [Configuration](#configuration)
    - [Controller Configuration (configs/controller.json)](#controller-configuration-configscontrollerjson)
    - [Screen Capture Configuration](#screen-capture-configuration)
  - [Usage Examples](#usage-examples)
    - [Basic System Startup](#basic-system-startup)
    - [Training Workflow](#training-workflow)
    - [Development and Testing](#development-and-testing)
  - [Training and AI](#training-and-ai)
    - [Reinforcement Learning Setup](#reinforcement-learning-setup)
      - [EnvPackage.py](#envpackagepy)
      - [Training Process](#training-process)
    - [Expert Demonstration System](#expert-demonstration-system)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
      - [1. Joystick Not Detected](#1-joystick-not-detected)
      - [2. Unity Connection Failed](#2-unity-connection-failed)
      - [3. Database Connection Issues](#3-database-connection-issues)
      - [4. Screen Capture Problems](#4-screen-capture-problems)
      - [5. Training Issues](#5-training-issues)
    - [Performance Optimization](#performance-optimization)
      - [System Performance](#system-performance)
      - [Training Performance](#training-performance)
    - [Logging and Debugging](#logging-and-debugging)
      - [Enable Debug Mode](#enable-debug-mode)
      - [Monitor API Requests](#monitor-api-requests)
      - [Check System Status](#check-system-status)
  - [Additional Resources](#additional-resources)

## System Architecture

The system follows a distributed microservices architecture where different components communicate through HTTP APIs:

```
Unity Simulation ←→ HardwareInterface ←→ DBPackage (Flask API) ←→ Controller/AI
                                            ↓
                                    Virtual_Cameras
                                            ↓
                                    Expert Path Creator
```

### Communication Flow
1. **Unity Simulation** runs the AUV physics simulation
2. **HardwareInterface** bridges Unity and the data API
3. **DBPackage** serves as the central data hub (SQLite + Flask)
4. **Controller** reads joystick input and sends commands
5. **Virtual_Cameras** captures Unity screen regions for visual feedback
6. **AI/Training** components use the API for reinforcement learning

## Installation and Setup

### Prerequisites
- Python 3.8+
- Unity simulation environment
- Joystick/controller (optional, for manual control)

### Dependencies Installation
```bash
pip install -r requirements.txt
```

### Key Dependencies
- **Flask 3.1.1** - Web framework for API
- **Flask-SQLAlchemy 3.1.1** - Database ORM
- **pygame 2.6.1** - Joystick input handling
- **opencv-python 4.11.0.86** - Computer vision and screen capture
- **PyAutoGUI 0.9.54** - Screen capture utilities
- **stable_baselines3 2.6.0** - Reinforcement learning framework
- **torch 2.7.1** - Deep learning framework
- **requests 2.32.4** - HTTP client library
- **numpy 1.26.4** - Numerical computing

### Quick Start
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Start the system: `python start.py --start_hardware`
4. Run controller: `python controller.py` (with joystick connected)

## Core Components

### Main Scripts

#### start.py
**Purpose**: System orchestrator that launches multiple services in the correct order.

**Features**:
- Launches Flask API (DBPackage) first
- Optionally starts hardware interface, AI package, and training
- Handles graceful shutdown of all subprocesses
- Configurable IP addresses and ports

**Usage**:
```bash
python start.py [OPTIONS]

Options:
  --ip TEXT              IP address to bind to (default: 0.0.0.0)
  --unity_ip TEXT        IP address for Unity communication (default: localhost)
  --unity_port INTEGER   Port for Unity communication (default: 9999)
  --port INTEGER         Port to bind to (default: 5000)
  --start_hardware       Flag to start the hardware interface
  --start_ai            Flag to start the AI package
  --train               Flag to start the training process
```

#### controller.py
**Purpose**: Joystick input handler that translates physical controller input to AUV commands.

**Features**:
- Reads joystick input using pygame
- Maps controller axes/buttons to AUV movement commands
- Sends commands to DBPackage via HTTP POST
- Configurable controller mapping via JSON file
- Real-time input processing with 0.1s intervals

**Control Mapping** (configurable in `configs/controller.json`):
- **X, Y, Z axes**: Linear movement
- **Yaw**: Rotational movement
- **S1, S2, S3**: Special functions (configurable)
- **Arm button**: System arming/disarming

#### expert_path_creator.py
**Purpose**: Records expert demonstrations by capturing system state and control inputs.

**Features**:
- Fetches combined position, rotation, velocity, and input data from API
- Filters out steps where Arm is not engaged
- Saves expert trajectories as JSON files for training
- Supports custom output file paths

**Usage**:
```bash
python expert_path_creator.py --host localhost --port 5000 --output expert_paths/demo1.json
```

### Modules Directory

#### modules/DBPackage.py
**Purpose**: Central Flask API server that manages all system data using SQLite database.

**Database Schema**:
- **Position**: id, datetime, X, Y, Z
- **Rotation**: id, datetime, Roll, Pitch, Yaw
- **Velocity**: id, datetime, Vx, Vy, Vz, Roll, Pitch, Yaw
- **Inputs**: id, datetime, X, Y, Z, Roll, Pitch, Yaw, S1, S2, S3, Arm

**Key Features**:
- RESTful API with GET/POST endpoints
- Real-time data storage and retrieval
- Expert path generation endpoint
- CORS enabled for cross-origin requests
- Configurable host and port

#### modules/HardwareInterface.py
**Purpose**: Bridge between Unity simulation and the data API.

**Key Functions**:
- **Unity Communication**: Gets position, rotation, velocity from Unity
- **Command Execution**: Applies velocity commands to Unity simulation
- **Data Logging**: Posts all state data to DBPackage API
- **Position Reset**: Handles submarine position restart commands

**Data Flow**:
1. Continuously polls Unity for submarine state
2. Fetches control inputs from DBPackage API
3. Applies control commands to Unity
4. Posts updated state back to DBPackage

#### modules/EnvPackage.py
**Purpose**: Gymnasium-compatible reinforcement learning environment.

**Features**:
- **Observation Space**: 12D vector [position(3) + rotation(3) + linear_vel(3) + angular_vel(3)]
- **Action Space**: 10D continuous control [X, Y, Z, Roll, Pitch, Yaw, S1, S2, S3, Arm]
- **Expert Path Loading**: Loads demonstration data for imitation learning
- **Reward Function**: Customizable reward based on task objectives
- **Episode Management**: Handles reset and step functions

#### modules/KwasiEnvPackage.py
**Purpose**: Alternative RL environment implementation with different observation/action spaces.

**Differences from EnvPackage**:
- Simplified action space bounds
- Direct Unity communication integration
- Different observation processing pipeline

#### modules/Virtual_Cameras.py
**Purpose**: Captures specific regions of the Unity screen and streams them as HTTP video feeds.

**Features**:
- **Multi-Camera Support**: Captures 3 predefined screen regions
- **Real-time Streaming**: Serves video feeds via Flask HTTP endpoints
- **Configurable Regions**: Screen capture areas defined by pixel coordinates
- **MJPEG Streaming**: Efficient video streaming format

**Endpoints**:
- `/feed1` - Camera 1 stream (region 1)
- `/feed2` - Camera 2 stream (region 2)
- `/feed3` - Camera 3 stream (region 3)

**Screen Regions** (configurable):
```python
cam_1: (997, 294) to (1718, 699)    # Top-left camera view
cam_2: (1720, 295) to (2437, 699)   # Top-right camera view
cam_3: (1361, 701) to (2080, 1109)  # Bottom camera view
```

#### modules/trainer.py
**Purpose**: Reinforcement learning training script using Stable-Baselines3 PPO algorithm with checkpoint continuation support.

**Features**:
- **PPO Algorithm**: Proximal Policy Optimization for continuous control
- **Custom Policy**: Multi-layer perceptron with configurable architecture
- **GPU Support**: Automatic CUDA detection and usage
- **Tensorboard Logging**: Training metrics and visualization
- **Environment Validation**: Checks custom environment compatibility
- **Model Continuation**: Automatically continues training from existing checkpoints
- **Flexible Training**: Command-line options for custom training configurations

**Training Configuration**:
- **Policy**: Custom MLP with configurable hidden layers
- **Algorithm**: PPO with optimized hyperparameters
- **Batch Size**: 512 samples
- **Learning Rate**: 2.5e-4
- **Gamma**: 0.99 (discount factor)
- **GAE Lambda**: 0.95 (advantage estimation)
- **Default Timesteps**: 1,000,000 (configurable)

**Command Line Options**:
```bash
python modules/trainer.py [OPTIONS]

Options:
  --continue_from PATH   Path to existing model (default: latest model)
  --timesteps INTEGER    Number of training timesteps (default: 1,000,000)
  --fresh               Force fresh training, ignore existing models
```

**Usage Examples**:
```bash
# Continue from most recent model
python modules/trainer.py

# Continue with more timesteps
python modules/trainer.py --timesteps 2000000

# Start fresh training
python modules/trainer.py --fresh

# Continue from specific model
python modules/trainer.py --continue_from logs/run_20250709_135310/ppo_auv_model.zip
```

### Support Modules

#### modules/support/WebCamService.py
**Purpose**: Webcam service class for handling camera operations.

**Features**:
- **Multi-camera Support**: Handles multiple camera indices
- **Frame Processing**: JPEG encoding and frame cropping
- **Error Handling**: Robust camera access with exception handling

#### modules/support/routes.py
**Purpose**: Flask blueprint for webcam streaming routes.

#### modules/support/camera_0.py & camera_1.py
**Purpose**: Individual camera endpoint handlers for different camera feeds.

### Examples Directory

#### examples/joystick.py
**Purpose**: Pygame example for testing joystick connectivity and events.

**Usage**: Run to verify joystick is properly connected and responsive before using the main controller.

## API Endpoints

### DBPackage API (Default: http://localhost:5000)

#### Position Endpoints
- **GET /position** - Retrieve latest position data
- **POST /position** - Store new position data
  ```json
  {
    "datetime": "2025-01-09 12:00:00",
    "X": 0.0,
    "Y": 0.0,
    "Z": 0.0
  }
  ```

#### Rotation Endpoints
- **GET /rotation** - Retrieve latest rotation data
- **POST /rotation** - Store new rotation data
  ```json
  {
    "datetime": "2025-01-09 12:00:00",
    "Roll": 0.0,
    "Pitch": 0.0,
    "Yaw": 0.0
  }
  ```

#### Velocity Endpoints
- **GET /velocity** - Retrieve latest velocity data
- **POST /velocity** - Store new velocity data
  ```json
  {
    "datetime": "2025-01-09 12:00:00",
    "Vx": 0.0,
    "Vy": 0.0,
    "Vz": 0.0,
    "Roll": 0.0,
    "Pitch": 0.0,
    "Yaw": 0.0
  }
  ```

#### Input Endpoints
- **GET /inputs** - Retrieve latest input commands
- **POST /inputs** - Store new input commands
  ```json
  {
    "datetime": "2025-01-09 12:00:00",
    "X": 0.0,
    "Y": 0.0,
    "Z": 0.0,
    "Roll": 0.0,
    "Pitch": 0.0,
    "Yaw": 0.0,
    "S1": 0.0,
    "S2": 0.0,
    "S3": 0.0,
    "Arm": 0
  }
  ```

#### Expert Path Endpoint
- **GET /get_expert_path** - Retrieve complete expert demonstration data
  - Returns combined position, rotation, velocity, and input data
  - Filters out steps where Arm is not engaged

### Virtual Cameras API (Default: http://localhost:5001)
- **GET /feed1** - Camera 1 video stream (MJPEG)
- **GET /feed2** - Camera 2 video stream (MJPEG)
- **GET /feed3** - Camera 3 video stream (MJPEG)

### Webcam Support API
- **GET /stream** - General webcam stream
- **GET /video_0** - Camera 0 stream (ZED camera)
- **GET /video_1** - Camera 1 stream (Anchor camera)

## Configuration

### Controller Configuration (configs/controller.json)

The controller configuration file maps joystick inputs to AUV control commands:

```json
{
    "joystick_1": {
        "name": "Spektrum InterLink DX",
        "axis": {
            "X": 4,      // Axis index for X movement
            "Y": 1,      // Axis index for Y movement
            "Z": 3,      // Axis index for Z movement
            "Yaw": 0,    // Axis index for Yaw rotation
            "S3": 7      // Axis index for S3 function
        },
        "button": {
            "S1_Increase": {"button": 1},    // Button for S1 increase
            "S1_Decrease": {"button": 2},    // Button for S1 decrease
            "S2_Increase": {"button": 10},   // Button for S2 increase
            "S2_Decrease": {"button": 9},    // Button for S2 decrease
            "Arm": {"button": 0}             // Arming button
        },
        "hat": {}    // Hat/D-pad configuration (unused)
    }
}
```

**Customization**: Modify axis and button indices to match your specific joystick model.

### Screen Capture Configuration

Virtual camera regions can be adjusted in `modules/Virtual_Cameras.py`:

```python
# Modify these coordinates to match your Unity window layout
cam_1_top_left = (997, 294)
cam_1_bottom_right = (1718, 699)
# ... additional camera regions
```

**Calibration**: Use a coordinate fetching utility to determine exact pixel positions for your setup.

## Usage Examples

### Basic System Startup

1. **Start Core Services**:
   ```bash
   python start.py --start_hardware
   ```

2. **Manual Control**:
   ```bash
   python controller.py
   ```

3. **Record Expert Demonstration**:
   ```bash
   python expert_path_creator.py --output expert_paths/demo1.json
   ```

### Training Workflow

1. **Collect Expert Data**:
   ```bash
   # Start system with hardware interface
   python start.py --start_hardware

   # In another terminal, run controller for demonstration
   python controller.py

   # Record the demonstration
   python expert_path_creator.py --output expert_paths/training_demo.json
   ```

2. **Train AI Model**:
   ```bash
   # Option 1: Using start script (basic training)
   python start.py --train

   # Option 2: Direct training with options
   python modules/trainer.py --timesteps 1000000

   # Option 3: Continue training from existing model
   python modules/trainer.py --continue_from logs/run_20250709_135310/ppo_auv_model.zip --timesteps 2000000
   ```

3. **Continue Training** (to improve model performance):
   ```bash
   # Automatically continue from most recent model
   python modules/trainer.py --timesteps 1000000

   # Continue with specific model and more timesteps
   python modules/trainer.py --continue_from logs/run_YYYYMMDD_HHMMSS/ppo_auv_model.zip --timesteps 2000000
   ```

4. **Test Trained Model**:
   ```bash
   # Test with hardware interface
   python start.py --start_hardware --start_ai

   # Evaluate model performance
   python start.py --evaluate
   ```

### Development and Testing

1. **Test Joystick**:
   ```bash
   python examples/joystick.py
   ```

2. **Monitor Video Feeds**:
   - Open browser to `http://localhost:5001/feed1`
   - View additional feeds at `/feed2` and `/feed3`

3. **API Testing**:
   ```bash
   curl http://localhost:5000/position
   curl http://localhost:5000/inputs
   ```

## Training and AI

### Reinforcement Learning Setup

The system supports reinforcement learning through two main environment implementations:

#### EnvPackage.py
- **Observation**: 12-dimensional state vector
- **Action**: 10-dimensional continuous control
- **Reward**: Customizable based on task objectives
- **Expert Integration**: Loads demonstration data for imitation learning

#### Training Process

1. **Environment Validation**:
   ```python
   from stable_baselines3.common.env_checker import check_env
   check_env(env, warn=True)
   ```

2. **Model Training**:
   - Algorithm: PPO (Proximal Policy Optimization)
   - Policy: Custom MLP with configurable architecture
   - Logging: Tensorboard integration for monitoring
   - Checkpoint Management: Automatic model saving and loading

3. **Training Modes**:
   - **Fresh Training**: Start from scratch with random weights
   - **Continued Training**: Resume from existing model checkpoint
   - **Automatic Detection**: Finds and loads most recent model

4. **Hyperparameters**:
   - Learning Rate: 2.5e-4
   - Batch Size: 512
   - Gamma: 0.99
   - GAE Lambda: 0.95
   - Entropy Coefficient: 0.01
   - Default Timesteps: 1,000,000

5. **Model Checkpoints**:
   - Models saved in `logs/run_YYYYMMDD_HHMMSS/ppo_auv_model.zip`
   - Tensorboard logs in same directory
   - Continued training creates new log directory with `_continued` suffix

### Expert Demonstration System

The expert demonstration system allows human operators to provide training data:

1. **Data Collection**: Records position, rotation, velocity, and control inputs
2. **Filtering**: Removes inactive periods (when Arm is not engaged)
3. **Storage**: Saves demonstrations as JSON files
4. **Integration**: Loads expert data into RL environment for imitation learning

### Model Management and Training Best Practices

#### Model Checkpoints
- **Location**: Models are saved in `logs/run_YYYYMMDD_HHMMSS/ppo_auv_model.zip`
- **Automatic Detection**: Training script automatically finds the most recent model
- **Manual Selection**: Use `--continue_from` to specify a particular checkpoint
- **Backup**: Keep important model checkpoints backed up

#### Training Strategies

1. **Incremental Training**:
   ```bash
   # Start with initial training
   python modules/trainer.py --fresh --timesteps 1000000

   # Continue training for better performance
   python modules/trainer.py --timesteps 1000000

   # Further refinement
   python modules/trainer.py --timesteps 500000
   ```

2. **Performance Monitoring**:
   ```bash
   # Monitor training with Tensorboard
   tensorboard --logdir logs/

   # Evaluate model performance
   python modules/EvalPackage.py
   ```

3. **Training Tips**:
   - Start with shorter training sessions (500k-1M timesteps)
   - Monitor evaluation results to track improvement
   - Continue training if model hasn't converged
   - Use fresh training if model performance degrades

#### Model Evaluation Workflow
1. **Train Model**: Use trainer.py with desired timesteps
2. **Evaluate Performance**: Run evaluation to check expert path following
3. **Continue Training**: If performance is insufficient, continue training
4. **Deploy Model**: Use best-performing model for actual control

## Troubleshooting

### Common Issues

#### 1. Joystick Not Detected
**Symptoms**: Controller input not working, pygame errors
**Solutions**:
- Verify joystick is connected and recognized by OS
- Run `python examples/joystick.py` to test connectivity
- Check controller configuration in `configs/controller.json`
- Ensure pygame is properly installed

#### 2. Unity Connection Failed
**Symptoms**: HardwareInterface cannot connect to Unity
**Solutions**:
- Verify Unity simulation is running
- Check Unity IP and port configuration (default: localhost:9999)
- Ensure Unity has the appropriate communication interface
- Verify firewall settings

#### 3. Database Connection Issues
**Symptoms**: API endpoints returning errors, data not persisting
**Solutions**:
- Ensure DBPackage.py is running (started by start.py)
- Check database file permissions
- Verify Flask API is accessible at configured port
- Review SQLite database integrity

#### 4. Screen Capture Problems
**Symptoms**: Virtual cameras showing black/incorrect regions
**Solutions**:
- Verify Unity window is visible and not minimized
- Adjust screen capture coordinates in Virtual_Cameras.py
- Check display scaling settings
- Ensure PyAutoGUI has screen access permissions

#### 5. Training Issues
**Symptoms**: RL training not converging, environment errors, model loading failures
**Solutions**:
- Validate environment with `check_env()`
- Verify expert demonstration data quality
- Adjust hyperparameters in trainer.py
- Check GPU/CUDA availability for training
- Monitor Tensorboard logs for training progress
- Use `--fresh` flag if model loading fails
- Ensure sufficient training timesteps (try 2M+ for complex tasks)
- Continue training from checkpoints if initial training insufficient

#### 6. Model Checkpoint Issues
**Symptoms**: Cannot load existing model, training starts from scratch unexpectedly
**Solutions**:
- Verify model file exists: `ls logs/run_*/ppo_auv_model.zip`
- Check file permissions on model files
- Use absolute path with `--continue_from`
- Ensure model was saved properly (check for .zip file)
- Use `--fresh` to intentionally start new training

### Performance Optimization

#### System Performance
- **Reduce Update Frequency**: Adjust sleep intervals in main loops
- **Optimize Screen Capture**: Reduce capture resolution or frame rate
- **Database Optimization**: Use appropriate SQLite settings for high-frequency writes

#### Training Performance
- **GPU Utilization**: Ensure CUDA is properly configured
- **Batch Size**: Adjust based on available memory
- **Parallel Environments**: Use vectorized environments for faster training

### Logging and Debugging

#### Enable Debug Mode
```python
# In DBPackage.py
app.run(host=args.host, port=args.port, debug=True)
```

#### Monitor API Requests
```bash
# View real-time API logs
tail -f logs/api.log
```

#### Check System Status
```bash
# Verify all services are running
ps aux | grep python
netstat -tulpn | grep :5000
```

---

## Additional Resources

- **Unity Integration**: Ensure Unity project has appropriate communication scripts
- **Hardware Setup**: Configure joystick/controller according to manufacturer instructions
- **Network Configuration**: Adjust IP addresses and ports for distributed setups
- **Expert Demonstrations**: Record high-quality demonstrations for better training results

For detailed implementation information, refer to the inline documentation in each module file.