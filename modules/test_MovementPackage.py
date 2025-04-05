import numpy as np
import requests
import time
import json

class AUVController:
    """
    Implements AUV dynamics, thruster allocation, and MPPI-based optimization.
    """

    def __init__(self):
        """
        Initialize AUV parameters based on the given model.
        """
        # Mass-Inertia Matrix (Assumed diagonal for simplicity)
        self.M_tot = np.diag([50, 50, 50, 10, 10, 10])  # Adjust values as per AUV parameters

        # Damping Matrix (Approximated as linear damping)
        self.D = np.diag([5, 5, 10, 2, 2, 2])

        # Thruster Configuration Matrix
        self.THRUSTER_MATRIX = np.array([
            [ 1, -1,  0,  0,  0,  1],  # M1
            [ 1,  1,  0,  0,  0, -1],  # M2
            [-1,  1,  0,  0,  0,  1],  # M3
            [ 1, -1,  0,  0,  0, -1],  # M4
            [ 0,  0, -1,  1, -1,  0],  # M5
            [ 0,  0, -1, -1, -1,  0],  # M6
            [ 0,  0, -1, -1,  1,  0],  # M7
            [ 0,  0, -1,  1,  1,  0]   # M8
        ])

        # Initialize State (Position, Orientation, and Velocity)
        self.state = np.zeros(12)  # [x, y, z, roll, pitch, yaw, u, v, w, p, q, r]

    def coriolis_forces(self, velocity):
        """
        Compute the Coriolis and added mass forces.
        """
        C_tot = np.zeros((6, 6))  # Approximated as zero for simplicity
        return C_tot @ velocity

    def gravity_buoyancy_forces(self):
        """
        Compute gravity and buoyancy restoring forces.
        """
        g_m = np.array([0, 0, 9.81 * 50, 0, 0, 0])  # Buoyancy = Weight in steady state
        return g_m

    def compute_thruster_outputs(self, X, Y, Z, Roll, Pitch, Yaw):
        """
        Compute the thrust values for 8 thrusters based on 6DOF inputs.

        Parameters:
            X, Y, Z, Roll, Pitch, Yaw: Desired force/torque inputs.

        Returns:
            np.array: An array containing thrust values for M1 to M8.
        """
        input_vector = np.array([X, Y, Z, Roll, Pitch, Yaw])
        
        # Compute thrust allocation
        thruster_outputs = self.THRUSTER_MATRIX @ input_vector

        # Normalize output values between -1 and 1
        max_val = np.max(np.abs(thruster_outputs))
        if max_val > 1:
            thruster_outputs /= max_val

        return thruster_outputs

    def runge_kutta_update(self, thrust_forces, dt=0.1):
        """
        Updates the AUV state using Runge-Kutta 2nd order method.

        Parameters:
            thrust_forces (np.array): Thruster forces.
            dt (float): Time step for integration.
        """
        def f(state):
            """
            Computes the time derivative of the state vector.
            """
            # Extract velocities
            velocity = state[6:]

            # Compute Forces and Moments
            tau = self.THRUSTER_MATRIX.T @ thrust_forces  # Map thruster forces to generalized forces
            coriolis = self.coriolis_forces(velocity)
            gravity = self.gravity_buoyancy_forces()
            
            # Compute acceleration
            acceleration = np.linalg.inv(self.M_tot) @ (tau - coriolis - self.D @ velocity - gravity)

            # Kinematic update (velocity to position/orientation)
            state_derivative = np.zeros_like(state)
            state_derivative[:6] = velocity  # Position/Orientation derivative
            state_derivative[6:] = acceleration  # Velocity derivative

            return state_derivative

        # Runge-Kutta integration (RK2)
        k1 = f(self.state)
        k2 = f(self.state + dt * k1 / 2)
        self.state += dt * k2

    def fetch_inputs(self):
        """
        Fetch inputs from the AUV API at http://localhost:5000/inputs.

        Returns:
            dict: Input values for X, Y, Z, Roll, Pitch, Yaw, and Arm.
        """
        try:
            response = requests.get("http://localhost:5000/inputs")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching inputs: {e}")
            return None

    def send_thruster_outputs(self, thruster_outputs):
        """
        Sends thruster outputs to the API at http://localhost:5000/motors.

        Parameters:
            thruster_outputs (np.array): Computed thruster values.
        """
        data = {
            "M1": thruster_outputs[0],
            "M2": thruster_outputs[1],
            "M3": thruster_outputs[2],
            "M4": thruster_outputs[3],
            "M5": thruster_outputs[4],
            "M6": thruster_outputs[5],
            "M7": thruster_outputs[6],
            "M8": thruster_outputs[7]
        }

        try:
            response = requests.post("http://localhost:5000/motors", json=data)
            response.raise_for_status()
            print("Thruster outputs sent successfully:", data)
        except requests.exceptions.RequestException as e:
            print(f"Error sending thruster outputs: {e}")

    def run(self, dt=0.1):
        """
        Main control loop to fetch inputs, compute outputs, and send data.
        """
        while True:
            inputs = self.fetch_inputs()
            if inputs:
                X, Y, Z, Roll, Pitch, Yaw, Arm = (
                    inputs["X"], inputs["Y"], inputs["Z"], 
                    inputs["Roll"], inputs["Pitch"], inputs["Yaw"], 
                    inputs["Arm"]
                )

                # Compute optimal thruster outputs
                thruster_outputs = self.compute_thruster_outputs(X, Y, Z, Roll, Pitch, Yaw)

                # Update AUV state
                self.runge_kutta_update(thruster_outputs, dt)

                # Send outputs
                self.send_thruster_outputs(thruster_outputs)

            time.sleep(dt)  # Control loop delay

# Run Controller
auv = AUVController()
auv.run()
