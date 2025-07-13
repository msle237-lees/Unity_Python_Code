@echo off
REM AUV Control and Training Suite - Windows Batch Script
REM This script provides easy access to common AUV system operations

setlocal enabledelayedexpansion

echo ========================================
echo    AUV Control and Training Suite
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if we're in the correct directory
if not exist "start.py" (
    echo ERROR: start.py not found
    echo Please run this script from the Unity_Python_Code directory
    pause
    exit /b 1
)

:MENU
echo.
echo Select an option:
echo.
echo 1. Start Complete System (Training + Hardware + Windows Sim)
echo 2. Start Single Machine Mode (All-in-One)
echo 3. Start Single Machine Fresh Training
echo 4. Start Training Only (Cluster Mode)
echo 5. Start Hardware Interface Only
echo 6. Start Controller (Manual Control)
echo 7. Start Fresh Training (Multi-Component)
echo 8. Continue Training from Existing Model
echo 9. Evaluate Trained Model
echo 10. Start Cloud Machine (Model Evaluation)
echo 11. Interactive Mode (Custom Arguments)
echo 0. Exit
echo.

set /p choice="Enter your choice (0-11): "

if "%choice%"=="1" goto COMPLETE_SYSTEM
if "%choice%"=="2" goto SINGLE_MACHINE
if "%choice%"=="3" goto SINGLE_MACHINE_FRESH
if "%choice%"=="4" goto TRAINING_ONLY
if "%choice%"=="5" goto HARDWARE_ONLY
if "%choice%"=="6" goto CONTROLLER
if "%choice%"=="7" goto FRESH_TRAINING
if "%choice%"=="8" goto CONTINUE_TRAINING
if "%choice%"=="9" goto EVALUATE
if "%choice%"=="10" goto CLOUD_MACHINE
if "%choice%"=="11" goto INTERACTIVE
if "%choice%"=="0" goto EXIT

echo Invalid choice. Please try again.
goto MENU

:COMPLETE_SYSTEM
echo.
echo Starting Complete AUV System...
echo This will start: Database, Training, Hardware Interface, and Windows Simulator
echo.
python start.py --start_hardware --start_windows_simulator --processes 4
goto MENU

:SINGLE_MACHINE
echo.
echo Starting Single Machine Mode (All-in-One)...
echo This mode runs everything on one machine with simplified configuration
echo Perfect for development, testing, or single-machine deployments
echo.
echo Note: Each training process will run in parallel with its own:
echo - Database instance (different ports)
echo - Hardware interface
echo - Unity simulator instance
echo.
set /p processes="Enter number of parallel training processes (default 4): "
if "%processes%"=="" set processes=4
set /p timesteps="Enter training timesteps (default 1000000): "
if "%timesteps%"=="" set timesteps=1000000
echo.
echo Starting single machine AUV system with %processes% parallel training process(es)...
python start.py --start_hardware --start_windows_simulator --processes %processes% --timesteps %timesteps% --fresh
goto MENU

:SINGLE_MACHINE_FRESH
echo.
echo Starting Single Machine Fresh Training...
echo This mode starts fresh training optimized for single machine deployment
echo Ideal for starting new training experiments on one machine
echo.
echo Note: This will:
echo - Start fresh training (ignore existing models)
echo - Run multiple parallel training processes
echo - Each process gets its own database, hardware interface, and simulator
echo - Optimized settings for single machine performance
echo.
set /p processes="Enter number of parallel training processes (default 2): "
if "%processes%"=="" set processes=2
set /p timesteps="Enter training timesteps (default 1000000): "
if "%timesteps%"=="" set timesteps=1000000
echo.
echo Starting fresh training on single machine with %processes% parallel process(es)...
echo Training for %timesteps% timesteps...
python start.py --fresh --start_hardware --start_windows_simulator --processes %processes% --timesteps %timesteps%
goto MENU

:TRAINING_ONLY
echo.
echo Starting Training System (Cluster Mode)...
echo This will start multiple parallel training processes without simulators
echo Use this mode when running on a cluster machine dedicated to training
echo.
set /p processes="Enter number of parallel training processes (default 4): "
if "%processes%"=="" set processes=4
python start.py --cluster_machine --processes %processes%
goto MENU

:HARDWARE_ONLY
echo.
echo Starting Hardware Interface Only...
echo This will start the database and hardware interface for manual control
echo.
python start.py --start_hardware
goto MENU

:CONTROLLER
echo.
echo Starting Controller for Manual Control...
echo Make sure to connect your Xbox 360 or other supported controller
echo.
set /p ip="Enter Flask API IP (default localhost): "
if "%ip%"=="" set ip=localhost
set /p port="Enter Flask API port (default 5000): "
if "%port%"=="" set port=5000
python controller.py --ip %ip% --port %port%
goto MENU

:FRESH_TRAINING
echo.
echo Starting Fresh Training...
echo This will start new training from scratch with hardware and simulator
echo.
set /p timesteps="Enter training timesteps (default 1000000): "
if "%timesteps%"=="" set timesteps=1000000
set /p processes="Enter number of parallel training processes (default 4): "
if "%processes%"=="" set processes=4
python start.py --fresh --timesteps %timesteps% --processes %processes% --start_hardware --start_windows_simulator
goto MENU

:CONTINUE_TRAINING
echo.
echo Continuing Training from Existing Model...
echo.
set /p model_path="Enter model path (default logs/run_20250709_135310/ppo_auv_model.zip): "
if "%model_path%"=="" set model_path=logs/run_20250709_135310/ppo_auv_model.zip
set /p timesteps="Enter additional timesteps (default 1000000): "
if "%timesteps%"=="" set timesteps=1000000
python start.py --continue_from "%model_path%" --timesteps %timesteps% --start_hardware --start_windows_simulator
goto MENU

:EVALUATE
echo.
echo Evaluating Trained Model...
echo.
set /p model_path="Enter model path (default logs/run_20250709_135310/ppo_auv_model.zip): "
if "%model_path%"=="" set model_path=logs/run_20250709_135310/ppo_auv_model.zip
set /p episodes="Enter number of episodes (default 5): "
if "%episodes%"=="" set episodes=5
python start.py --evaluate --model_path "%model_path%" --episodes %episodes% --start_hardware --start_windows_simulator
goto MENU

:CLOUD_MACHINE
echo.
echo Starting Cloud Machine (Model Evaluation Server)...
echo This mode evaluates models from cluster machines
echo.
set /p machine_id="Enter machine ID (default 0): "
if "%machine_id%"=="" set machine_id=0
python start.py --cloud_machine --machine_id %machine_id%
goto MENU

:INTERACTIVE
echo.
echo Starting Interactive Mode...
echo You will be prompted for all configuration options
echo.
python start.py --interactive
goto MENU

:EXIT
echo.
echo Exiting AUV Control and Training Suite
echo Thank you for using the system!
pause
exit /b 0
