import cv2
import pyautogui
import numpy as np
from flask import Flask, Response
from threading import Thread
import time

# Define screen capture areas (x, y, width, height)
CAPTURE_REGIONS = [
    (100, 100, 400, 300),  # Section 1
    (600, 100, 400, 300),  # Section 2
    (1100, 100, 400, 300)  # Section 3
]

app = Flask(__name__)

# Function to capture a screen region
def capture_screen(region):
    x, y, width, height = region
    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    return frame

# Function to generate video stream
def generate_feed(region):
    while True:
        frame = capture_screen(region)
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.05)  # Adjust for desired FPS

# Flask routes to serve the streams
@app.route('/feed1')
def video_feed1():
    return Response(generate_feed(CAPTURE_REGIONS[0]), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/feed2')
def video_feed2():
    return Response(generate_feed(CAPTURE_REGIONS[1]), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/feed3')
def video_feed3():
    return Response(generate_feed(CAPTURE_REGIONS[2]), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Run the Flask app on port 5000
    thread = Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5000, 'debug': False})
    thread.start()
