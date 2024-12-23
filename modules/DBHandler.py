# Handles the creation and hosting of all necessary databases for the sub to function. This allows easier transmission of data and data logging.

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import argparse # For command line arguments when running the script

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Databases include both sensor and output data. Each database has a unique ID, datetime, and the data itself.
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

# Motor DB
class Motor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    M1 = db.Column(db.Integer, nullable=False)
    M2 = db.Column(db.Integer, nullable=False)
    M3 = db.Column(db.Integer, nullable=False)
    M4 = db.Column(db.Integer, nullable=False)
    M5 = db.Column(db.Integer, nullable=False)
    M6 = db.Column(db.Integer, nullable=False)
    M7 = db.Column(db.Integer, nullable=False)
    M8 = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Motor('{self.M1}', '{self.M2}', '{self.M3}', '{self.M4}', '{self.M5}', '{self.M6}', '{self.M7}', '{self.M8}')"

# Motor Routes
@app.route('/motor', methods=['POST', 'GET'])
def motor():
    if request.method == 'POST':
        M1 = request.json['M1']
        M2 = request.json['M2']
        M3 = request.json['M3']
        M4 = request.json['M4']
        M5 = request.json['M5']
        M6 = request.json['M6']
        M7 = request.json['M7']
        M8 = request.json['M8']
        new_motor = Motor(M1=M1, M2=M2, M3=M3, M4=M4, M5=M5, M6=M6, M7=M7, M8=M8)
        db.session.add(new_motor)
        db.session.commit()
        return jsonify({'message': 'OK'})

    elif request.method == 'GET':
        latest_motor_data = Motor.query.order_by(Motor.datetime.desc()).first()
        if latest_motor_data:
            motor_data = {'id': latest_motor_data.id, 'datetime': latest_motor_data.datetime, 'M1': latest_motor_data.M1, 'M2': latest_motor_data.M2, 'M3': latest_motor_data.M3, 'M4': latest_motor_data.M4, 'M5': latest_motor_data.M5, 'M6': latest_motor_data.M6, 'M7': latest_motor_data.M7, 'M8': latest_motor_data.M8}
            return jsonify({'motor_data': motor_data})
        else:
            return jsonify({'message': 'No data found'})

# Servo DB
class Servo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    S1 = db.Column(db.Integer, nullable=False)
    S2 = db.Column(db.Integer, nullable=False)
    S3 = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Servo('{self.S1}', '{self.S2}', '{self.S3}')"

# Servo Routes
@app.route('/servo', methods=['POST', 'GET'])
def servo():
    if request.method == 'POST':
        S1 = request.json['S1']
        S2 = request.json['S2']
        S3 = request.json['S3']
        new_servo = Servo(S1=S1, S2=S2, S3=S3)
        db.session.add(new_servo)
        db.session.commit()
        return jsonify({'message': 'OK'})

    elif request.method == 'GET':
        latest_servo_data = Servo.query.order_by(Servo.datetime.desc()).first()
        if latest_servo_data:
            servo_data = {'id': latest_servo_data.id, 'datetime': latest_servo_data.datetime, 'S1': latest_servo_data.S1, 'S2': latest_servo_data.S2, 'S3': latest_servo_data.S3}
            return jsonify({'servo_data': servo_data})
        else:
            return jsonify({'message': 'No data found'})

# Sonar DB
class Sonar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    sonar_data = db.Column(db.LongBinary, nullable=False)

    def __repr__(self):
        return f"Sonar('{self.sonar_data}')"

# Sonar Routes
@app.route('/sonar', methods=['POST', 'GET'])
def sonar():
    if request.method == 'POST':
        sonar_data = request.json['sonar_data']
        new_sonar = Sonar(sonar_data=sonar_data)
        db.session.add(new_sonar)
        db.session.commit()
        return jsonify({'message': 'OK'})

    elif request.method == 'GET':
        sonar_data = Sonar.query.all()
        output = []
        for data in sonar_data:
            sonar_data = {'id': data.id, 'datetime': data.datetime, 'sonar_data': data.sonar_data}
            output.append(sonar_data)
        return jsonify({'sonar_data': output})

# IMU DB
class IMU(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    Accelerometer_X = db.Column(db.Float, nullable=False)
    Accelerometer_Y = db.Column(db.Float, nullable=False)
    Accelerometer_Z = db.Column(db.Float, nullable=False)
    Gyroscope_X = db.Column(db.Float, nullable=False)
    Gyroscope_Y = db.Column(db.Float, nullable=False)
    Gyroscope_Z = db.Column(db.Float, nullable=False)
    Magnetometer_X = db.Column(db.Float, nullable=False)
    Magnetometer_Y = db.Column(db.Float, nullable=False)
    Magnetometer_Z = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"IMU('{self.Accelerometer_X}', '{self.Accelerometer_Y}', '{self.Accelerometer_Z}', '{self.Gyroscope_X}', '{self.Gyroscope_Y}', '{self.Gyroscope_Z}', '{self.Magnetometer_X}', '{self.Magnetometer_Y}', '{self.Magnetometer_Z}')"

# IMU Routes
@app.route('/imu', methods=['POST', 'GET'])
def imu():
    if request.method == 'POST':
        Accelerometer_X = request.json['Accelerometer_X']
        Accelerometer_Y = request.json['Accelerometer_Y']
        Accelerometer_Z = request.json['Accelerometer_Z']
        Gyroscope_X = request.json['Gyroscope_X']
        Gyroscope_Y = request.json['Gyroscope_Y']
        Gyroscope_Z = request.json['Gyroscope_Z']
        Magnetometer_X = request.json['Magnetometer_X']
        Magnetometer_Y = request.json['Magnetometer_Y']
        Magnetometer_Z = request.json['Magnetometer_Z']
        new_imu = IMU(Accelerometer_X=Accelerometer_X, Accelerometer_Y=Accelerometer_Y, Accelerometer_Z=Accelerometer_Z, Gyroscope_X=Gyroscope_X, Gyroscope_Y=Gyroscope_Y, Gyroscope_Z=Gyroscope_Z, Magnetometer_X=Magnetometer_X, Magnetometer_Y=Magnetometer_Y, Magnetometer_Z=Magnetometer_Z)
        db.session.add(new_imu)
        db.session.commit()
        return jsonify({'message': 'OK'})

    elif request.method == 'GET':
        imu_data = IMU.query.all()
        output = []
        for data in imu_data:
            imu_data = {'id': data.id, 'datetime': data.datetime, 'Accelerometer_X': data.Accelerometer_X, 'Accelerometer_Y': data.Accelerometer_Y, 'Accelerometer_Z': data.Accelerometer_Z, 'Gyroscope_X': data.Gyroscope_X, 'Gyroscope_Y': data.Gyroscope_Y, 'Gyroscope_Z': data.Gyroscope_Z, 'Magnetometer_X': data.Magnetometer_X, 'Magnetometer_Y': data.Magnetometer_Y, 'Magnetometer_Z': data.Magnetometer_Z}
            output.append(imu_data)
        return jsonify({'imu_data': output})

# Voltage / Current Measurements DB
class VoltageCurrent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    Voltage_B1 = db.Column(db.Float, nullable=False)
    Voltage_B2 = db.Column(db.Float, nullable=False)
    Voltage_B3 = db.Column(db.Float, nullable=False)
    Current_B1 = db.Column(db.Float, nullable=False)
    Current_B2 = db.Column(db.Float, nullable=False)
    Current_B3 = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"VoltageCurrent('{self.Voltage_B1}', '{self.Voltage_B2}', '{self.Voltage_B3}', '{self.Current_B1}', '{self.Current_B2}', '{self.Current_B3}')"

# Voltage / Current Measurements Routes
@app.route('/voltage_current', methods=['POST', 'GET'])
def voltage_current():
    if request.method == 'POST':
        Voltage_B1 = request.json['Voltage_B1']
        Voltage_B2 = request.json['Voltage_B2']
        Voltage_B3 = request.json['Voltage_B3']
        Current_B1 = request.json['Current_B1']
        Current_B2 = request.json['Current_B2']
        Current_B3 = request.json['Current_B3']
        new_voltage_current = VoltageCurrent(Voltage_B1=Voltage_B1, Voltage_B2=Voltage_B2, Voltage_B3=Voltage_B3, Current_B1=Current_B1, Current_B2=Current_B2, Current_B3=Current_B3)
        db.session.add(new_voltage_current)
        db.session.commit()
        return jsonify({'message': 'OK'})

    elif request.method == 'GET':
        voltage_current_data = VoltageCurrent.query.all()
        output = []
        for data in voltage_current_data:
            voltage_current_data = {'id': data.id, 'datetime': data.datetime, 'Voltage_B1': data.Voltage_B1, 'Voltage_B2': data.Voltage_B2, 'Voltage_B3': data.Voltage_B3, 'Current_B1': data.Current_B1, 'Current_B2': data.Current_B2, 'Current_B3': data.Current_B3}
            output.append(voltage_current_data)
        return jsonify({'voltage_current_data': output})

# Hydrophone heading direction DB
class Hydrophone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    Hydrophone_Heading = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"Hydrophone('{self.Hydrophone_Heading}')"

# Hydrophone heading direction Routes
@app.route('/hydrophone', methods=['POST', 'GET'])
def hydrophone():
    if request.method == 'POST':
        Hydrophone_Heading = request.json['Hydrophone_Heading']
        new_hydrophone = Hydrophone(Hydrophone_Heading=Hydrophone_Heading)
        db.session.add(new_hydrophone)
        db.session.commit()
        return jsonify({'message': 'OK'})

    elif request.method == 'GET':
        hydrophone_data = Hydrophone.query.all()
        output = []
        for data in hydrophone_data:
            hydrophone_data = {'id': data.id, 'datetime': data.datetime, 'Hydrophone_Heading': data.Hydrophone_Heading}
            output.append(hydrophone_data)
        return jsonify({'hydrophone_data': output})

# Leak Detection DB
class LeakDetection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    Leak_Detection = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return f"LeakDetection('{self.Leak_Detection}')"

# Leak Detection Routes
@app.route('/leak_detection', methods=['POST', 'GET'])
def leak_detection():
    if request.method == 'POST':
        Leak_Detection = request.json['Leak_Detection']
        new_leak_detection = LeakDetection(Leak_Detection=Leak_Detection)
        db.session.add(new_leak_detection)
        db.session.commit()
        return jsonify({'message': 'OK'})

    elif request.method == 'GET':
        leak_detection_data = LeakDetection.query.all()
        output = []
        for data in leak_detection_data:
            leak_detection_data = {'id': data.id, 'datetime': data.datetime, 'Leak_Detection': data.Leak_Detection}
            output.append(leak_detection_data)
        return jsonify({'leak_detection_data': output})

# Depth Sensor DB
class DepthSensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    Depth = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"DepthSensor('{self.Depth}')"

# Depth Sensor Routes
@app.route('/depth_sensor', methods=['POST', 'GET'])
def depth_sensor():
    if request.method == 'POST':
        Depth = request.json['Depth']
        new_depth_sensor = DepthSensor(Depth=Depth)
        db.session.add(new_depth_sensor)
        db.session.commit()
        return jsonify({'message': 'OK'})

    elif request.method == 'GET':
        depth_sensor_data = DepthSensor.query.all()
        output = []
        for data in depth_sensor_data:
            depth_sensor_data = {'id': data.id, 'datetime': data.datetime, 'Depth': data.Depth}
            output.append(depth_sensor_data)
        return jsonify({'depth_sensor_data': output})

# Internal Temperature DB
class InternalTemperature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    Internal_Temperature = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"InternalTemperature('{self.Internal_Temperature}')"

# Internal Temperature Routes
@app.route('/internal_temperature', methods=['POST', 'GET'])
def internal_temperature():
    if request.method == 'POST':
        Internal_Temperature = request.json['Internal_Temperature']
        new_internal_temperature = InternalTemperature(Internal_Temperature=Internal_Temperature)
        db.session.add(new_internal_temperature)
        db.session.commit()
        return jsonify({'message': 'OK'})

    elif request.method == 'GET':
        internal_temperature_data = InternalTemperature.query.all()
        output = []
        for data in internal_temperature_data:
            internal_temperature_data = {'id': data.id, 'datetime': data.datetime, 'Internal_Temperature': data.Internal_Temperature}
            output.append(internal_temperature_data)
        return jsonify({'internal_temperature_data': output})

# External Temperature DB
class ExternalTemperature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    External_Temperature = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"ExternalTemperature('{self.External_Temperature}')"

# External Temperature Routes
@app.route('/external_temperature', methods=['POST', 'GET'])
def external_temperature():
    if request.method == 'POST':
        External_Temperature = request.json['External_Temperature']
        new_external_temperature = ExternalTemperature(External_Temperature=External_Temperature)
        db.session.add(new_external_temperature)
        db.session.commit()
        return jsonify({'message': 'OK'})

    elif request.method == 'GET':
        external_temperature_data = ExternalTemperature.query.all()
        output = []
        for data in external_temperature_data:
            external_temperature_data = {'id': data.id, 'datetime': data.datetime, 'External_Temperature': data.External_Temperature}
            output.append(external_temperature_data)
        return jsonify({'external_temperature_data': output})

# Internal Humidity DB
class InternalHumidity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    Internal_Humidity = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"InternalHumidity('{self.Internal_Humidity}')"

# Internal Humidity Routes
@app.route('/internal_humidity', methods=['POST', 'GET'])
def internal_humidity():
    if request.method == 'POST':
        Internal_Humidity = request.json['Internal_Humidity']
        new_internal_humidity = InternalHumidity(Internal_Humidity=Internal_Humidity)
        db.session.add(new_internal_humidity)
        db.session.commit()
        return jsonify({'message': 'OK'})

    elif request.method == 'GET':
        internal_humidity_data = InternalHumidity.query.all()
        output = []
        for data in internal_humidity_data:
            internal_humidity_data = {'id': data.id, 'datetime': data.datetime, 'Internal_Humidity': data.Internal_Humidity}
            output.append(internal_humidity_data)
        return jsonify({'internal_humidity_data': output})

# Internal Pressure DB
class InternalPressure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    Internal_Pressure = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"InternalPressure('{self.Internal_Pressure}')"

# Internal Pressure Routes
@app.route('/internal_pressure', methods=['POST', 'GET'])
def internal_pressure():
    if request.method == 'POST':
        Internal_Pressure = request.json['Internal_Pressure']
        new_internal_pressure = InternalPressure(Internal_Pressure=Internal_Pressure)
        db.session.add(new_internal_pressure)
        db.session.commit()
        return jsonify({'message': 'OK'})

    elif request.method == 'GET':
        internal_pressure_data = InternalPressure.query.all()
        output = []
        for data in internal_pressure_data:
            internal_pressure_data = {'id': data.id, 'datetime': data.datetime, 'Internal_Pressure': data.Internal_Pressure}
            output.append(internal_pressure_data)
        return jsonify({'internal_pressure_data': output})

# External Pressure DB
class ExternalPressure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    External_Pressure = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"ExternalPressure('{self.External_Pressure}')"

# External Pressure Routes
@app.route('/external_pressure', methods=['POST', 'GET'])
def external_pressure():
    if request.method == 'POST':
        External_Pressure = request.json['External_Pressure']
        new_external_pressure = ExternalPressure(External_Pressure=External_Pressure)
        db.session.add(new_external_pressure)
        db.session.commit()
        return jsonify({'message': 'OK'})

    elif request.method == 'GET':
        external_pressure_data = ExternalPressure.query.all()
        output = []
        for data in external_pressure_data:
            external_pressure_data = {'id': data.id, 'datetime': data.datetime, 'External_Pressure': data.External_Pressure}
            output.append(external_pressure_data)
        return jsonify({'external_pressure_data': output})

# Command Line Arguments
parser = argparse.ArgumentParser(description='Run the database handler for the sub.')
parser.add_argument('-ip', '--ip', type=str, help='The IP address to host the database on.', default='0.0.0.0')
parser.add_argument('-p', '--port', type=int, help='The port to host the database on.', default=5001)
parser.add_argument('-d', '--debug', type=bool, help='Enable debugging mode.', default=True)
args = parser.parse_args()

if __name__ == '__main__':
    db.create_all()
    app.run(host=args.ip, port=args.port, debug=args.debug)
