import numpy as np
import logging

# Configure logging
logging.basicConfig(filename='pid_controller.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class PIDController6DOF:
    """
    A PID controller for a 6 DOF AUV using NumPy for efficient computation.

    Attributes:
    ----------
    kp, ki, kd : np.ndarray
        PID gains for each DOF (6 values: surge, sway, heave, yaw, pitch, roll).
    setpoints : np.ndarray
        Desired target values for each DOF.
    integrals : np.ndarray
        Accumulated integral terms for each DOF.
    last_errors : np.ndarray
        Last error values for each DOF.
    last_time : float
        Time of the last update for derivative calculation.
    """

    def __init__(self, kp=None, ki=None, kd=None):
        """
        Initialize the PID controller with gains for 6 DOFs.

        Parameters:
        ----------
        kp, ki, kd : list or array-like
            PID gains for each DOF (6 values: surge, sway, heave, yaw, pitch, roll).
        """
        self.kp = np.array(kp if kp else [1.0] * 6)
        self.ki = np.array(ki if ki else [0.0] * 6)
        self.kd = np.array(kd if kd else [0.0] * 6)

        self.setpoints = np.zeros(6)  # Target values for 6 DOFs
        self.integrals = np.zeros(6)  # Accumulated integral terms
        self.last_errors = np.zeros(6)  # Last error values
        self.last_time = None

    def set_gains(self, kp, ki, kd):
        """
        Set PID gains for all DOFs.
        """
        self.kp, self.ki, self.kd = map(np.array, (kp, ki, kd))
        logging.info(f"Updated gains: kp={self.kp}, ki={self.ki}, kd={self.kd}")

    def set_setpoints(self, setpoints):
        """
        Set desired target values for all DOFs.
        """
        self.setpoints = np.clip(np.array(setpoints), -1.0, 1.0)
        logging.info(f"Setpoints updated: {self.setpoints}")

    def compute(self, measured_values, current_time):
        """
        Compute the control outputs for 6 DOFs.

        Parameters:
        ----------
        measured_values : list or array-like
            Measured values for the 6 DOFs.
        current_time : float
            Current time in seconds.

        Returns:
        -------
        np.ndarray
            Control outputs for each DOF, clamped between -1 and 1.
        """
        measured_values = np.array(measured_values)
        errors = self.setpoints - measured_values
        delta_time = 0 if self.last_time is None else current_time - self.last_time

        # Proportional term
        p_term = self.kp * errors

        # Integral term
        if delta_time > 0:
            self.integrals += errors * delta_time
        i_term = self.ki * self.integrals

        # Derivative term
        d_term = np.zeros(6)
        if self.last_time is not None:
            d_term = self.kd * (errors - self.last_errors) / delta_time

        # Total output
        outputs = p_term + i_term + d_term
        outputs = np.clip(outputs, -1.0, 1.0)

        # Update state
        self.last_errors = errors
        self.last_time = current_time

        logging.info(f"Measured values: {measured_values}, Errors: {errors}, Outputs: {outputs}")
        return outputs

# Example usage
if __name__ == "__main__":
    import time

    pid = PIDController6DOF(kp=[1.2, 1.0, 1.0, 1.0, 1.0, 1.0], ki=[0.1] * 6, kd=[0.05] * 6)
    pid.set_setpoints([0.5, -0.3, 0.0, 0.1, 0.0, 0.0])

    measured_values = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    for i in range(10):
        current_time = time.time()
        outputs = pid.compute(measured_values, current_time)
        print(f"Time: {current_time:.2f}, Outputs: {outputs}")

        # Simulate system update
        measured_values += outputs * 0.1
        time.sleep(0.1)
