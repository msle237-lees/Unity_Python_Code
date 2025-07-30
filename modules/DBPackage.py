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
    arm = db.Column(db.Integer)  # ///< Arm state (0 or 1),

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
    arm = db.Column(db.Integer)  # ///< Arm state (0 or 1)
    X = db.Column(db.Float)  # ///< X coordinate of the expert step
    Y = db.Column(db.Float)  # ///< Y coordinate of the expert step
    Z = db.Column(db.Float)  # ///< Z coordinate of the expert step
    Roll = db.Column(db.Float)  # ///< Roll orientation of the expert step
    Pitch = db.Column(db.Float)  # ///< Pitch orientation of the expert step
    Yaw = db.Column(db.Float)  # ///< Yaw orientation of the expert step

    def __repr__(self):
        return f"ExpertPath(id={self.id}, step_index={self.step_index}, direction={self.direction}, force_level={self.force_level}, arm={self.arm}, X={self.X}, Y={self.Y}, Z={self.Z}, Roll={self.Roll}, Pitch={self.Pitch}, Yaw={self.Yaw})"

class Sensors(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # ///< Primary key ID
    step_index = db.Column(db.Integer)  # ///< Index of the sensor step
    arm = db.Column(db.Integer)  # ///< Arm state (0 or 1)
    X = db.Column(db.Float)  # ///< X coordinate of the sensor step
    Y = db.Column(db.Float)  # ///< Y coordinate of the sensor step
    Z = db.Column(db.Float)  # ///< Z coordinate of the sensor step
    Roll = db.Column(db.Float)  # ///< Roll orientation of the sensor step
    Pitch = db.Column(db.Float)  # ///< Pitch orientation of the sensor step
    Yaw = db.Column(db.Float)  # ///< Yaw orientation of the sensor step

    def __repr__(self):
        return f"Sensors(id={self.id}, step_index={self.step_index}, arm={self.arm}, X={self.X}, Y={self.Y}, Z={self.Z}, Roll={self.Roll}, Pitch={self.Pitch}, Yaw={self.Yaw})"

## @brief Route to store an agent's action in the database.
#  @return JSON response with success message and HTTP status code.
@app.route('/post_action', methods=['POST'])
def post_action():
    """
    Receive an action from the agent and store it in the database.
    """
    data = request.json
    new_input = Inputs(
        step_index=data['step_index'],
        direction=data['direction'],
        force_level=data['force_level'],
        arm=data['arm']
    )
    db.session.add(new_input)
    db.session.commit()
    return jsonify({"message": "Action received and stored successfully"}), 200

## @brief Route to retrieve the most recent agent action from the database.
#  @return JSON response with the latest Inputs data and HTTP status code.
@app.route('/get_action', methods=['GET'])
def get_action():
    """
    Get the latest action from the database.
    """
    latest_input = Inputs.query.order_by(Inputs.id.desc()).first()
    return jsonify({
        "step_index": latest_input.step_index,
        "direction": latest_input.direction,
        "force_level": latest_input.force_level,
        "arm": latest_input.arm
    }), 200

@app.route('/post_expert_path', methods=['POST'])
def post_expert_path():
    """
    Receive an expert path from the agent and store it in the database.
    """
    data = request.json
    new_expert_path = ExpertPath(
        step_index=data['step_index'],
        direction=data['direction'],
        force_level=data['force_level'],
        arm=data['arm'],
        X=data['X'],
        Y=data['Y'],
        Z=data['Z'],
        Roll=data['Roll'],
        Pitch=data['Pitch'],
        Yaw=data['Yaw']
    )
    db.session.add(new_expert_path)
    db.session.commit()
    return jsonify({"message": "Expert path received and stored successfully"}), 200

## @brief When the route is accessed, it gets the most recent expert path (From Arm = 0 to Arm = 1 and then Arm = 1 back to Arm = 0) from the database.
#  @return JSON response with the latest ExpertPath data and HTTP status code.
@app.route('/get_expert_path', methods=['GET'])
def get_expert_path():
    """
    Get all expert path entries from the database without any conversion or filtering.
    """
    expert_steps = ExpertPath.query.order_by(ExpertPath.id.asc()).all()
    data = []
    for step in expert_steps:
        data.append({
            "id": step.id,
            "step_index": step.step_index,
            "direction": step.direction,
            "force_level": step.force_level,
            "arm": step.arm,
            "X": step.X,
            "Y": step.Y,
            "Z": step.Z,
            "Roll": step.Roll,
            "Pitch": step.Pitch,
            "Yaw": step.Yaw
        })
    return jsonify(data), 200

## @brief Route to store sensor data in the database.
#  @return JSON response with success message and HTTP status code.
@app.route('/post_sensor_data', methods=['POST'])
def post_sensor_data():
    """
    Receive sensor data from the agent and store it in the database.
    """
    data = request.json
    new_sensor_data = Sensors(
        step_index=data['step_index'],
        arm=data['arm'],
        X=data['X'],
        Y=data['Y'],
        Z=data['Z'],
        Roll=data['Roll'],
        Pitch=data['Pitch'],
        Yaw=data['Yaw']
    )
    db.session.add(new_sensor_data)
    db.session.commit()
    return jsonify({"message": "Sensor data received and stored successfully"}), 200

## @brief Route to retrieve the most recent sensor data from the database.
#  @return JSON response with the latest Sensors data and HTTP status code.
@app.route('/get_sensor_data', methods=['GET'])
def get_sensor_data():
    """
    Get the latest sensor data from the database.
    """
    latest_sensor_data = Sensors.query.order_by(Sensors.id.desc()).first()
    if latest_sensor_data:
        return jsonify({
            "step_index": latest_sensor_data.step_index,
            "arm": latest_sensor_data.arm,
            "X": latest_sensor_data.X,
            "Y": latest_sensor_data.Y,
            "Z": latest_sensor_data.Z,
            "Roll": latest_sensor_data.Roll,
            "Pitch": latest_sensor_data.Pitch,
            "Yaw": latest_sensor_data.Yaw
        }), 200
    else:
        return jsonify({"message": "No sensor data found"}), 404

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
    app.run(host=args.host, port=args.port, debug=True, use_reloader=False)  # use_reloader=False to prevent double initialization
