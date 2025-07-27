## @file
#  @brief Flask API for storing and retrieving actions and expert paths.
#  This API is used to interact with a Unity simulation or similar agents by posting actions and expert paths,
#  and retrieving the most recent ones from a SQLite database.

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

from datetime import datetime
from typing import List, Dict, Any
import argparse
import logging
import sys
import os

## Initialize the Flask application
app = Flask(__name__)

## Configure SQLite as the database engine
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'  # Use SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Initialize SQLAlchemy with the Flask app
db = SQLAlchemy(app)

## Suppress all logs from Flask's Werkzeug server
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

## Redirect all stdout and stderr to null (suppress console output)
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

## @class Inputs
#  @brief SQLAlchemy model for storing agent actions. \n
#         The Inputs table is used to store the actions taken by the agent.
#         step_index: Index of the action step
#         direction: Direction taken by the agent
#         force_level: Force level applied
class Inputs(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) # ///< Primary key ID
    step_index = db.Column(db.Integer)  # ///< Index of the action step
    direction = db.Column(db.String(1024))  # ///< Directions taken by the agent, stored as comma-separated string
    force_level = db.Column(db.Integer)  # ///< Force level applied
    X = db.Column(db.Float)  # ///< X-axis force
    Y = db.Column(db.Float)  # ///< Y-axis force
    Z = db.Column(db.Float)  # ///< Z-axis force
    Roll = db.Column(db.Float)  # ///< Roll force
    Pitch = db.Column(db.Float)  # ///< Pitch force
    Yaw = db.Column(db.Float)  # ///< Yaw force
    S1 = db.Column(db.Float)  # ///< S1 force
    S2 = db.Column(db.Float)  # ///< S2 force
    S3 = db.Column(db.Float)  # ///< S3 force
    arm = db.Column(db.Integer)  # ///< Arm state (0 or 1)

    def __repr__(self):
        return f"Inputs(id={self.id}, step_index={self.step_index}, direction={self.direction}, force_level={self.force_level}, arm={self.arm})"

## @class ExpertPath
#  @brief SQLAlchemy model for storing expert demonstration data.
#         The ExpertPath table is used to store the expert demonstration data.
#         id: Primary key ID
#         step_index: Index of the expert step
#         direction: Direction taken by the expert
#         force_level: Force level applied by the expert
class ExpertPath(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # ///< Primary key ID
    step_index = db.Column(db.Integer)  # ///< Index of the expert step
    direction = db.Column(db.String(255))  # ///< Direction taken by the expert
    force_level = db.Column(db.Integer)  # ///< Force level applied
    X = db.Column(db.Float)  # ///< X-axis force
    Y = db.Column(db.Float)  # ///< Y-axis force
    Z = db.Column(db.Float)  # ///< Z-axis force
    Roll = db.Column(db.Float)  # ///< Roll force
    Pitch = db.Column(db.Float)  # ///< Pitch force
    Yaw = db.Column(db.Float)  # ///< Yaw force
    S1 = db.Column(db.Float)  # ///< S1 force
    S2 = db.Column(db.Float)  # ///< S2 force
    S3 = db.Column(db.Float)  # ///< S3 force
    arm = db.Column(db.Integer)  # ///< Arm state (0 or 1)

    def __repr__(self):
        return f"ExpertPath(id={self.id}, step_index={self.step_index}, direction={self.direction}, force_level={self.force_level}, arm={self.arm})"

## @brief Route to store an agent's action in the database.
#  @return JSON response with success message and HTTP status code.
@app.route('/action', methods=['POST'])
def action():
    """
    Receive an action from the agent and store it in the database.
    """
    data = request.json
    new_input = Inputs(
        step_index=data['step_index'],
        direction=data['direction'],
        force_level=data['force_level'],
        X=data.get('X', 0.0),
        Y=data.get('Y', 0.0),
        Z=data.get('Z', 0.0),
        Roll=data.get('Roll', 0.0),
        Pitch=data.get('Pitch', 0.0),
        Yaw=data.get('Yaw', 0.0),
        S1=data.get('S1', 0.0),
        S2=data.get('S2', 0.0),
        S3=data.get('S3', 0.0),
        arm=data['arm']
    )
    db.session.add(new_input)
    db.session.commit()
    return jsonify({"message": "Action received and stored successfully"}), 200

## @brief Route to retrieve the most recent agent action from the database.
#  @return JSON response with the latest Inputs data and HTTP status code.
@app.route('/action', methods=['GET'])
def action():
    """
    Get the latest action from the database.
    """
    latest_input = Inputs.query.order_by(Inputs.id.desc()).first()
    return jsonify({
        "step_index": latest_input.step_index,
        "direction": latest_input.direction,
        "force_level": latest_input.force_level,
        "X": latest_input.X,
        "Y": latest_input.Y,
        "Z": latest_input.Z,
        "Roll": latest_input.Roll,
        "Pitch": latest_input.Pitch,
        "Yaw": latest_input.Yaw,
        "S1": latest_input.S1,
        "S2": latest_input.S2,
        "S3": latest_input.S3,
        "arm": latest_input.arm
    }), 200

## @brief When the route is accessed, it gets the most recent expert path (From Arm = 0 to Arm = 1 and then Arm = 1 back to Arm = 0) from the database.
#  @return JSON response with the latest ExpertPath data and HTTP status code.
@app.route('/expert_path', methods=['GET'])
def expert_path():
    """
    Get the latest expert path from the database.
    """
    # Get all ExpertPath entries ordered by id
    expert_steps = ExpertPath.query.order_by(ExpertPath.id.asc()).all()

    # Find the indices where arm transitions from 0 to 1 and 1 to 0
    arm_transitions = []
    prev_direction = None
    for idx, step in enumerate(expert_steps):
        if prev_direction is not None and step.direction != prev_direction:
            arm_transitions.append(idx)
        prev_direction = step.direction

    # Select the segment from first transition (0->1) to second transition (1->0)
    if len(arm_transitions) >= 2:
        latest_expert_path = expert_steps[arm_transitions[0]:arm_transitions[1]+1]
    else:
        latest_expert_path = expert_steps  # fallback: return all if transitions not found
    data = {}
    for step in latest_expert_path:
        data[step.id] = {
            "step_index": step.step_index,
            "direction": step.direction,
            "force_level": step.force_level,
            "X": step.X,
            "Y": step.Y,
            "Z": step.Z,
            "Roll": step.Roll,
            "Pitch": step.Pitch,
            "Yaw": step.Yaw,
            "S1": step.S1,
            "S2": step.S2,
            "S3": step.S3,
            "arm": step.arm
        }
    return jsonify(data), 200

## @brief Ensure all tables are created before the first request.
with app.app_context():
    db.create_all()

## @brief Set up argument parser for host and port configuration.
parser = argparse.ArgumentParser(description="Flask API for Unity Interface")
parser.add_argument("--port", type=int, default=5000, help="Port for Flask API")
parser.add_argument("--host", type=str, default="0.0.0.0", help="Host for Flask API")
args = parser.parse_args()

## @brief Entry point of the Flask application.
if __name__ == "__main__":
    app.run(host=args.host, port=args.port, debug=False)
