#!/bin/bash

# AUV Control and Training Suite - Linux Bash Script
# This script provides easy access to common AUV system operations

set -e  # Exit on any error

echo "========================================"
echo "    AUV Control and Training Suite"
echo "========================================"
echo

# # Check if Python is available
# if ! command -v python3 &> /dev/null || ! command -v python &> /dev/null; then
#     echo "ERROR: Python is not installed or not in PATH"
#     echo "Please install Python 3.8+ and try again"
#     exit 1
# fi

# # Use python3 if available, otherwise python
# PYTHON_CMD="python3"
# if ! command -v python3 &> /dev/null; then
#     PYTHON_CMD="python"
# fi

# Check if we're in the correct directory
if [ ! -f "start.py" ]; then
    echo "ERROR: start.py not found"
    echo "Please run this script from the Unity_Python_Code directory"
    exit 1
fi

python start.py --start_hardware --start_linux_simulator --processes 6 --fresh