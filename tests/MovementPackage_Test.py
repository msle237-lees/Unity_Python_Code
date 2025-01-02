# Move this script to root directory and run `python -m unittest MovementPackage_Test.py`
# This will run the tests and show the results
# Example output:
# [GET] Inputs - Failed: 500, Internal Server Error
# [GET] Inputs - Success: {'X': 0.5, 'Y': -0.5, 'Yaw': 0.2, 'Z': -0.8, 'Pitch': 0.1, 'Roll': 0.0, 'S1': 0.5, 'S2': -0.2, 'S3': 0.3}
# [POST] Motors - Failed: 500, Internal Server Error
# [POST] Motors - Success: {'status': 'OK'}
# [POST] Servos - Failed: 500, Internal Server Error
# [POST] Servos - Success: {'status': 'OK'}
# ----------------------------------------------------------------------
# Ran 8 tests in 0.003s
# OK

import unittest
from unittest.mock import patch, MagicMock
from modules.MovementPackage import MovementPackage, map  # Assuming the module is named `movement_package.py`

class TestMovementPackage(unittest.TestCase):

    def setUp(self):
        self.movement = MovementPackage("127.0.0.1", "5000")

    @patch('requests.get')
    def test_get_inputs_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "X": 0.5, "Y": -0.5, "Yaw": 0.2,
            "Z": -0.8, "Pitch": 0.1, "Roll": 0.0,
            "S1": 0.5, "S2": -0.2, "S3": 0.3
        }

        inputs = self.movement.get_inputs()

        self.assertIsNotNone(inputs)
        self.assertIn("X", inputs)
        self.assertEqual(inputs["X"], 0.5)

    @patch('requests.get')
    def test_get_inputs_failure(self, mock_get):
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = "Internal Server Error"

        inputs = self.movement.get_inputs()

        self.assertIsNone(inputs)

    def test_parse_inputs(self):
        mock_data = {
            "X": 0.5, "Y": -0.5, "Yaw": 0.2,
            "Z": -0.8, "Pitch": 0.1, "Roll": 0.0,
            "S1": 0.5, "S2": -0.2, "S3": 0.3
        }

        self.movement.parse_inputs(mock_data)

        # Validate horizontal motor mappings
        self.assertNotEqual(self.movement.motor_data["M1"], 127)
        self.assertNotEqual(self.movement.motor_data["M5"], 127)

        # Validate servo mappings
        self.assertNotEqual(self.movement.servo_data["S1"], 127)
        self.assertNotEqual(self.movement.servo_data["S2"], 127)

    @patch('requests.post')
    def test_post_motors_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "OK"}

        motor_data = {"M1": 128, "M2": 129, "M3": 130, "M4": 131, "M5": 128, "M6": 129, "M7": 130, "M8": 131}

        self.movement.post_motors(motor_data)
        mock_post.assert_called_with(self.movement.MOTORS, json=motor_data)

    @patch('requests.post')
    def test_post_motors_failure(self, mock_post):
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Internal Server Error"

        motor_data = {"M1": 128, "M2": 129, "M3": 130, "M4": 131, "M5": 128, "M6": 129, "M7": 130, "M8": 131}
        
        self.movement.post_motors(motor_data)
        mock_post.assert_called_with(self.movement.MOTORS, json=motor_data)

    @patch('requests.post')
    def test_post_servos_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "OK"}

        servo_data = {"S1": 128, "S2": 129, "S3": 130}

        self.movement.post_servos(servo_data)
        mock_post.assert_called_with(self.movement.SERVOS, json=servo_data)

    @patch('requests.post')
    def test_post_servos_failure(self, mock_post):
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Internal Server Error"

        servo_data = {"S1": 128, "S2": 129, "S3": 130}

        self.movement.post_servos(servo_data)
        mock_post.assert_called_with(self.movement.SERVOS, json=servo_data)

    def test_map_function(self):
        result = map(0.5, -1, 1, 0, 256)
        self.assertAlmostEqual(result, 192, delta=1)

if __name__ == "__main__":
    unittest.main()
