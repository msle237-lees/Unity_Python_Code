from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

from datetime import datetime
from typing import List, Dict, Any
import argparse

import sys
import os

# helpful logging function
def _log_message(label: str, start_time:str, log_dir:str, message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = f"{log_dir}/{start_time}/{label}.log"
    with open(log_file, "a") as f:
        output = f"[{timestamp}] {message}\n"
        f.write(output)
        print(output, end='\n')

# Initialize Flask app and SQLAlchemy
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'  # Use SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define database models
class BestModel(db.Model):
    __tablename__ = 'best_model'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    machine_id = db.Column(db.String(120), nullable=False)
    model_path = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<BestModel {self.id}, {self.date}, {self.machine_id}, {self.model_path}, {self.score}>'

# Define routes
@app.route('/best_model', methods=['GET'])
def get_best_model():
    best_model_record = BestModel.query.order_by(BestModel.id.desc()).first()
    if best_model_record:
        return jsonify({
            'id': best_model_record.id,
            'date': best_model_record.date.isoformat() if best_model_record.date else None,
            'machine_id': best_model_record.machine_id,
            'model_path': best_model_record.model_path,
            'score': best_model_record.score
        }), 200
    else:
        return jsonify({'message': 'No data available'}), 404

@app.route('/best_model', methods=['POST'])
def add_best_model():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    try:
        # Handle date field - use current time if not provided
        date_value = datetime.now()
        if 'date' in data and data['date']:
            try:
                date_value = datetime.strptime(data['date'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Try ISO format
                date_value = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))

        new_best_model = BestModel(
            date=date_value,
            machine_id=str(data['machine_id']),
            model_path=data['model_path'],
            score=float(data['score'])
        )
        db.session.add(new_best_model)
        db.session.commit()
        return jsonify({'message': 'Best model data added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

# Initialize the database and create tables
with app.app_context():
    db.create_all()

# Configure the arguments for the Flask app
parser = argparse.ArgumentParser(description="Flask API for Cloud DB")
parser.add_argument("--host", type=str, default="0.0.0.0", help="Host for Flask API")
parser.add_argument("--port", type=int, default=5000, help="Port for Flask API")
args = parser.parse_args()

if __name__ == "__main__":
    app.run(host=args.host, port=args.port, debug=False)