# Handles the creation and hosting of all necessary databases for the sub to function. This allows easier transmission of data and data logging.

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import argparse # For command line arguments when running the script
import subprocess
import logging
import sys

# Databases include both sensor and output data. Each database has a unique ID, datetime, and the data itself.
# Inputs (6 DOF, 3 Servos, 1 Arm, 1 Hover)
# Motors (0 - 256)
# Servos (0 - 256) (The Arm is a servo if you think about it)
# Sonar (2D Map of surroundings)
# IMU (Accelerometer / Gyroscope / Magenetometer)
# Voltage / Current Measurements (Voltage and Amperage)
# Hydrophone heading direction (Compass directions)
# Leak Detection
# Depth Sensor (meters)
# Internal Temperature
# External Temperature
# Internal Humidity
# Internal Pressure
# External Pressure

# Initialize the database object without binding to an app yet
db = SQLAlchemy()

# Initialize the Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # SQLite database file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Bind the db instance to the app
db.init_app(app)

# Ensure database tables exist before running the app
with app.app_context():
    db.create_all()  # This will create all tables
    db.session.commit()
    print("✅ Database tables created successfully")

# Define a test model
class inputs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=True, default=datetime.now(timezone.utc))
    X = db.Column(db.Float, nullable=False)
    Y = db.Column(db.Float, nullable=False)
    Z = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"Inputs('{self.X}', '{self.Y}', '{self.Z}')"

# Test endpoint
@app.route('/inputs', methods=['POST'])
def add_input():
    data = request.get_json()
    new_input = inputs(X=data['X'], Y=data['Y'], Z=data['Z'])
    db.session.add(new_input)
    db.session.commit()
    return jsonify({'message': 'Data added successfully'}), 201

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Flask App for AUV')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host address')
    parser.add_argument('--port', type=int, default=5001, help='Port number')
    args = parser.parse_args()

    app.run(host=args.host, port=args.port, debug=True)
