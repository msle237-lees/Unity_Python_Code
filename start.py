import argparse
import sys
import subprocess
import time
import logging
import threading
import requests
import platform
if platform.system() == 'Windows':
    import msvcrt
else:
    import termios
    import tty

# Set up logging configuration with a specific format and level
class PackageFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)

    def format(self, record):
        if not hasattr(record, 'package'):
            record.package = 'UnknownPackage'
        return super().format(record)

package_format = '%(asctime)s - %(levelname)s - %(package)s - %(message)s'
logging.basicConfig(
    format=package_format,
    level=logging.INFO
)
logging.setLoggerClass(logging.getLoggerClass())
for handler in logging.root.handlers:
    handler.setFormatter(PackageFormatter(package_format))

logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Global process list
processes = []

def stream_output(proc, package):
    """
    Reads and logs the stdout and stderr output from the given subprocess.
    Logs stdout as INFO and stderr as ERROR under the specified package name.
    """
    for line in proc.stdout:
        logging.info(line.decode().strip(), extra={'package': package})
    for line in proc.stderr:
        logging.error(line.decode().strip(), extra={'package': package})

def launch_subprocess(cmd, package):
    """
    Launches a subprocess using the given command and starts a background thread
    to stream and log its stdout and stderr output.
    """
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1)
    processes.append(proc)
    thread = threading.Thread(target=stream_output, args=(proc, package))
    thread.daemon = True
    thread.start()
    return proc

def cleanup():
    """
    Terminates all running subprocesses that were launched during execution
    and exits the program cleanly.
    """
    logging.info("Shutting down all subprocesses...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception as e:
            logging.error(f"Error terminating process: {e}")
    sys.exit(0)

def monitor_exit_keys():
    """
    Runs in a background thread to listen for 'q', 'ESC', or Ctrl+C key presses
    and gracefully shuts down all subprocesses.
    """
    if platform.system() == 'Windows':
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in [b'q', b'\x1b']:  # q or ESC
                    cleanup()
            time.sleep(0.1)
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch in ['q', '\x1b']:
                    cleanup()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def main():
    """
    Entry point that coordinates launching various subprocess modules (DB, Trainer, Hardware Interface, etc.)
    based on command-line arguments. Streams their logs, supports interactive shutdown via 'q', 'ESC', or Ctrl+C.
    """
    parser = argparse.ArgumentParser(description="Run AUV Training and Evaluation modules")

    parser.add_argument('--db', action='store_true', help='Run the DBPackage module')
    parser.add_argument('--db-host', type=str, default='localhost')
    parser.add_argument('--db-port', type=int, default=5000)

    parser.add_argument('--hwi', action='store_true')
    parser.add_argument('--unity-port', type=int, default=9999)
    parser.add_argument('--test', action='store_true')

    parser.add_argument('--trainer', action='store_true')
    parser.add_argument('--continue-from', action='store_true')
    parser.add_argument('--timesteps', type=int, default=1000000)
    parser.add_argument('--fresh', action='store_true')

    parser.add_argument('--controller', action='store_true')
    parser.add_argument('--print-mode', choices=['none', 'raw', 'output', 'both', 'just'], default='output')
    parser.add_argument('--print-interval', type=float, default=0.1)

    parser.add_argument('--exc', action='store_true')

    args = parser.parse_args()

    try:
        if args.db:
            flask_cmd = [sys.executable, 'modules/DBPackage.py', '--host', args.db_host, '--port', str(args.db_port)]
            launch_subprocess(flask_cmd, 'DBPackage')

            # Verify if the DBPackage is running
            payload = {
                "step_index": 0,
                "direction": "forward",
                "force_level": 0.5,
                "arm": 0
            }
            response = requests.post(f"http://{args.db_host}:{args.db_port}/action", json=payload)
            while response.status_code != 200:
                logging.warning("DBPackage is not ready yet...")
                time.sleep(1)
                response = requests.post(f"http://{args.db_host}:{args.db_port}/action", json=payload)
            logging.info("DBPackage is running and ready to accept requests.")
        else:
            logging.info("Skipping DBPackage module as per command line arguments.")

        if args.hwi:
            hwi_cmd = [sys.executable, 'modules/HardwareInterface.py', '--unity_port', str(args.unity_port),
                       '--inputs_url', f"http://{args.db_host}", '--inputs_port', str(args.db_port)]
            if args.test:
                hwi_cmd.append('--test')
            launch_subprocess(hwi_cmd, 'HardwareInterface')
            time.sleep(2)
        else:
            logging.info("Skipping Hardware Interface module as per command line arguments.")

        if args.runTrainer:
            trainer_cmd = [sys.executable, 'modules/trainer.py', '--timesteps', str(args.timesteps)]
            if args.continue_from:
                trainer_cmd.append('--continue_from')
            if args.fresh:
                trainer_cmd.append('--fresh')
            launch_subprocess(trainer_cmd, 'Trainer')
            time.sleep(2)
        else:
            logging.info("Skipping Trainer module as per command line arguments.")

        if args.controller:
            ctrl_cmd = [sys.executable, 'start.py', '--ip', args.db_host, '--port', str(args.db_port),
                        '--print-interval', str(args.print_interval)]
            if args.print_mode == 'none':
                ctrl_cmd.append('--no-print')
            elif args.print_mode == 'raw':
                ctrl_cmd.append('--print-raw')
            elif args.print_mode == 'output':
                ctrl_cmd.append('--print-output')
            elif args.print_mode == 'both':
                ctrl_cmd.append('--print-both')
            elif args.print_mode == 'just':
                ctrl_cmd.append('--just-print')
            launch_subprocess(ctrl_cmd, 'Controller')
            time.sleep(2)
        else:
            logging.info("Skipping Controller module as per command line arguments.")

        if args.exc:
            expert_cmd = [sys.executable, 'expert_path_creator.py']
            launch_subprocess(expert_cmd, 'ExpertPathCreator')

        key_thread = threading.Thread(target=monitor_exit_keys)
        key_thread.daemon = True
        key_thread.start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
