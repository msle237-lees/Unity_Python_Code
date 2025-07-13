# AUV Control and Training Suite

A comprehensive Python-based system for controlling and training autonomous underwater vehicles (AUVs) in Unity simulation environments. This suite provides joystick control, data logging, reinforcement learning capabilities, and expert demonstration tools for AUV research and development.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Unity AUV simulation (builds available in `Sims/` folder)
- Optional: Xbox/PlayStation controller for manual control

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd Unity_Python_Code

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage
```bash
# Start the complete system with hardware interface
python start.py --start_hardware

# Train an AI model
python start.py --train

# Evaluate a trained model
python start.py --evaluate

# Create expert demonstration data
python start.py --get-expert-path
```

## 📁 Repository Structure

```
Unity_Python_Code/
├── Sims/                          # Unity simulation builds
│   ├── 7-12-2025-Linux/          # Linux build
│   └── 7-12-2025-Windows/        # Windows build
├── modules/                       # Core system modules
│   ├── DBPackage.py              # Central data API server
│   ├── EnvPackage.py             # RL environment
│   ├── EvalPackage.py            # Model evaluation
│   ├── HardwareInterface.py      # Unity communication bridge
│   ├── trainer.py                # PPO training system
│   └── expert_paths/             # Expert demonstration data
│       ├── path_1.json           # Original expert path
│       └── path_2.json           # Updated expert path (from row 133)
├── configs/                       # Configuration files
│   └── controller.json           # Controller mappings
├── logs/                         # Training logs and models
├── evaluation_results/           # Evaluation output files
├── start.py                      # Main system launcher
├── controller.py                 # Manual joystick control
└── expert_path_creator.py        # Expert data collection tool
```

## 🎮 System Components

### Core Modules
- **DBPackage.py**: SQLite-based Flask API for data management
- **EnvPackage.py**: Gymnasium-compatible RL environment with discrete action space
- **HardwareInterface.py**: Unity simulation communication bridge
- **trainer.py**: PPO-based reinforcement learning training system
- **EvalPackage.py**: Model evaluation and performance analysis

### Training System
- **Algorithm**: Proximal Policy Optimization (PPO)
- **Action Space**: 40 discrete actions (8 directions × 5 force levels)
- **Observation Space**: 12D vector (position, rotation, velocity)
- **Expert Learning**: Imitation learning from human demonstrations
- **Model Management**: Automatic checkpoint saving and loading

### Expert Demonstration System
- **Data Collection**: Records human pilot control inputs
- **Filtering**: Removes inactive periods (when Arm is disengaged)
- **Format**: JSON files with discrete actions and original inputs
- **Integration**: Seamless loading into RL environment

## 🎯 Key Features

- **Discrete Action Control**: Simplified 8-direction movement with 5 force levels
- **Expert Path Integration**: Train from human demonstrations starting at specific database rows
- **Automatic Model Management**: Continues training from latest checkpoints
- **Comprehensive Evaluation**: Detailed performance metrics and result logging
- **Unity Build Support**: Works with standalone Unity builds for optimal performance
- **Modular Architecture**: Microservices-based design with HTTP API communication

## 📊 Training Workflow

1. **Collect Expert Data**: Use joystick control to demonstrate desired behavior
2. **Process Demonstrations**: Convert continuous inputs to discrete actions
3. **Train AI Model**: Use PPO with expert imitation learning
4. **Evaluate Performance**: Test model on evaluation episodes
5. **Iterate**: Continue training from checkpoints for improved performance

## 🔧 Configuration

### Controller Setup
Edit `configs/controller.json` to configure joystick mappings:
```json
{
  "controller_type": "xbox",
  "axis_mappings": {...},
  "button_mappings": {...}
}
```

### Training Parameters
Modify training settings in `modules/trainer.py`:
- Learning rate: 5e-4
- Batch size: 512
- Training timesteps: 1,000,000 (configurable)
- Expert path: `modules/expert_paths/path_2.json`

## 📈 Performance Optimizations

- **Discrete Action Space**: Simplified control for faster learning
- **Expert Normalization**: Proper -10 to +10 input range handling
- **CPU-Optimized Training**: Forced CPU mode for consistent performance
- **Unity Build Support**: Headless simulation builds for training efficiency

For detailed documentation, see [docs/README.md](docs/README.md).