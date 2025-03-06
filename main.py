from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timezone
import subprocess
import argparse
import logging
import sys

# If you are having a problem with the database, try running the following commands in the terminal:
# export FLASK_APP=app.py  # macOS/Linux
# set FLASK_APP=app.py     # Windows

# flask db init
# flask db migrate -m "Initial migration"
# flask db upgrade

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure database (change to PostgreSQL or MySQL if needed)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Enables flask db commands

# Databases include both sensor and output data. Each database has a unique ID, datetime, and the data itself.
# Inputs (6 DOF, 3 Servos, 1 Arm, 1 Hover)
# Motors (8 * 0 - 256)
# Servos (3 * 0 - 256) (The Arm is a servo if you think about it)
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

# Define Model
class Inputs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    X = db.Column(db.Float, nullable=False)
    Y = db.Column(db.Float, nullable=False)
    Z = db.Column(db.Float, nullable=False)
    Roll = db.Column(db.Float, nullable=False, default=0.0)
    Pitch = db.Column(db.Float, nullable=False, default=0.0)
    Yaw = db.Column(db.Float, nullable=False)
    Arm = db.Column(db.Boolean, nullable=False, default=0)
    Hover = db.Column(db.Boolean, nullable=False, default=0)
    S1 = db.Column(db.Integer, nullable=False, default=0)
    S2 = db.Column(db.Integer, nullable=False, default=0)
    S3 = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {"id": self.id, "datetime": self.datetime.isoformat(), "X": self.X, "Y": self.Y, "Z": self.Z}

class Motors(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    M1 = db.Column(db.Integer, nullable=False, default=0)
    M2 = db.Column(db.Integer, nullable=False, default=0)
    M3 = db.Column(db.Integer, nullable=False, default=0)
    M4 = db.Column(db.Integer, nullable=False, default=0)
    M5 = db.Column(db.Integer, nullable=False, default=0)
    M6 = db.Column(db.Integer, nullable=False, default=0)
    M7 = db.Column(db.Integer, nullable=False, default=0)
    M8 = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {"id": self.id, "datetime": self.datetime.isoformat(), "M1": self.M1, "M2": self.M2, "M3": self.M3, "M4": self.M4, "M5": self.M5, "M6": self.M6, "M7": self.M7, "M8": self.M8}

class Servos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    S1 = db.Column(db.Integer, nullable=False, default=0)
    S2 = db.Column(db.Integer, nullable=False, default=0)
    S3 = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {"id": self.id, "datetime": self.datetime.isoformat(), "S1": self.S1, "S2": self.S2, "S3": self.S3}

class Sonar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    sonar_data = db.Column(db.PickleType, nullable=False)

    def to_dict(self):
        return {"id": self.id, "datetime": self.datetime.isoformat(), "sonar_data": self.sonar_data}

class IMU(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    X = db.Column(db.Float, nullable=False)
    Y = db.Column(db.Float, nullable=False)
    Z = db.Column(db.Float, nullable=False)
    Roll = db.Column(db.Float, nullable=False, default=0.0)
    Pitch = db.Column(db.Float, nullable=False, default=0.0)
    Yaw = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {"id": self.id, "datetime": self.datetime.isoformat(), "X": self.X, "Y": self.Y, "Z": self.Z, "Roll": self.Roll, "Pitch": self.Pitch, "Yaw": self.Yaw}
    
class VoltageCurrent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    voltage1 = db.Column(db.Float, nullable=False)
    voltage2 = db.Column(db.Float, nullable=False)
    voltage3 = db.Column(db.Float, nullable=False)
    current1 = db.Column(db.Float, nullable=False)
    current2 = db.Column(db.Float, nullable=False)
    current3 = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {"id": self.id, "datetime": self.datetime.isoformat(), "voltage1": self.voltage1, "voltage2": self.voltage2, "voltage3": self.voltage3, "current1": self.current1, "current2": self.current2, "current3": self.current3}

class LeakDetection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    leak_detected = db.Column(db.Boolean, nullable=False, default=0)

    def to_dict(self):
        return {"id": self.id, "datetime": self.datetime.isoformat(), "leak_detected": self.leak_detected}

class DepthSensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    depth = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {"id": self.id, "datetime": self.datetime.isoformat(), "depth": self.depth}
    
class Temperature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    internal_temp = db.Column(db.Float, nullable=False)
    external_temp = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {"id": self.id, "datetime": self.datetime.isoformat(), "internal_temp": self.internal_temp, "external_temp": self.external_temp}

class Humidity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    internal_humidity = db.Column(db.Float, nullable=False)
    external_humidity = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {"id": self.id, "datetime": self.datetime.isoformat(), "internal_humidity": self.internal_humidity, "external_humidity": self.external_humidity}
    
class Pressure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    internal_pressure = db.Column(db.Float, nullable=False)
    external_pressure = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {"id": self.id, "datetime": self.datetime.isoformat(), "internal_pressure": self.internal_pressure, "external_pressure": self.external_pressure}

# API Routes
# Inputs Routes
@app.route('/inputs', methods=['POST'])
def add_input():
    """ Adds a new input record """
    data = request.get_json()
    
    try:
        new_input = Inputs(
            X=data['X'], 
            Y=data['Y'], 
            Z=data['Z'], 
            Roll=data['Roll'], 
            Pitch=data['Pitch'], 
            Yaw=data['Yaw'], 
            Arm=data['Arm'], 
            Hover=data['Hover'], 
            S1=data['S1'], 
            S2=data['S2'], 
            S3=data['S3']
        )
        db.session.add(new_input)
        db.session.commit()
        return jsonify({'message': 'Data added successfully', 'data': new_input.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/inputs', methods=['GET'])
def get_inputs():
    """ Retrieves all input records """
    inputs = Inputs.query.all()
    return jsonify([input.to_dict() for input in inputs])

@app.route('/inputs/latest', methods=['GET'])
def get_latest_input():
    """ Retrieves the latest input record """
    latest_input = Inputs.query.order_by(Inputs.datetime.desc()).first()
    if latest_input:
        return jsonify(latest_input.to_dict())
    else:
        return jsonify({'error': 'No input records found'}), 404

# Motors Routes
@app.route('/motors', methods=['POST'])
def add_motor():
    """ Adds a new motor record """
    data = request.get_json()
    try:
        new_motor = Motors(
            M1=data['M1'], 
            M2=data['M2'], 
            M3=data['M3'], 
            M4=data['M4'], 
            M5=data['M5'], 
            M6=data['M6'], 
            M7=data['M7'], 
            M8=data['M8']
        )
        db.session.add(new_motor)
        db.session.commit()
        return jsonify({'message': 'Data added successfully', 'data': new_motor.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@app.route('/motors', methods=['GET'])
def get_motors():
    """ Retrieves all motor records """
    motors = Motors.query.all()
    return jsonify([motor.to_dict() for motor in motors])

@app.route('/motors/latest', methods=['GET'])
def get_latest_motor():
    """ Retrieves the latest motor record """
    latest_motor = Motors.query.order_by(Motors.datetime.desc()).first()
    if latest_motor:
        return jsonify(latest_motor.to_dict())
    else:
        return jsonify({'error': 'No motor records found'}), 404

# Servos Routes
@app.route('/servos', methods=['POST'])
def add_servo():
    """ Adds a new servo record """
    data = request.get_json()
    try:
        new_servo = Servos(
            S1=data['S1'], 
            S2=data['S2'], 
            S3=data['S3']
        )
        db.session.add(new_servo)
        db.session.commit()
        return jsonify({'message': 'Data added successfully', 'data': new_servo.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@app.route('/servos', methods=['GET'])
def get_servos():
    """ Retrieves all servo records """
    servos = Servos.query.all()
    return jsonify([servo.to_dict() for servo in servos])

@app.route('/servos/latest', methods=['GET'])
def get_latest_servo():
    """ Retrieves the latest servo record """
    latest_servo = Servos.query.order_by(Servos.datetime.desc()).first()
    if latest_servo:
        return jsonify(latest_servo.to_dict())
    else:
        return jsonify({'error': 'No servo records found'}), 404

# Skip Sonar, VoltageCurrent, LeakDetection, Temperature, Humidity, Pressure since I'll never use them
@app.route('/imu', methods=['POST'])
def add_imu():
    """ Adds a new IMU record """
    data = request.get_json()
    try:
        new_imu = IMU(
            X=data['X'], 
            Y=data['Y'], 
            Z=data['Z'], 
            Roll=data['Roll'], 
            Pitch=data['Pitch'], 
            Yaw=data['Yaw']
        )
        db.session.add(new_imu)
        db.session.commit()
        return jsonify({'message': 'Data added successfully', 'data': new_imu.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@app.route('/imu', methods=['GET'])
def get_imu():
    """ Retrieves all IMU records """
    imu = IMU.query.all()
    return jsonify([imu.to_dict() for imu in imu])

@app.route('/imu/latest', methods=['GET'])
def get_latest_imu():
    """ Retrieves the latest IMU record """
    latest_imu = IMU.query.order_by(IMU.datetime.desc()).first()
    if latest_imu:
        return jsonify(latest_imu.to_dict())
    else:
        return jsonify({'error': 'No IMU records found'}), 404

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Flask App for AUV Data Logging')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host address')
    parser.add_argument('--port', type=int, default=5001, help='Port number')
    args = parser.parse_args()

    # Define all subprocesses that can be run in the background
    # [py, 'modules/MovementPackage.py', '--host', args.host, '--port', str(args.port)],
    # [py, 'modules/VirtualModules/HardwareInterface.py', '--host', args.host, '--port', str(args.port)]
    # [py, 'modules/AIPackage.py', '--host', args.host, '--port', str(args.port)]
    py = sys.executable
    processes = {
        [py, 'modules/VirtualModules/Cameras.py', '--host', args.host, '--port', str(args.port)]
    }

    # Start all subprocesses
    for process in processes:
        subprocess.Popen(process)

    logger.info(f"Starting Flask app on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=True)
