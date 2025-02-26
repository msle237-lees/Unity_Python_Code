import cv2
import pyautogui
import numpy as np
from flask import Flask, Response
from threading import Thread
import time

# Unbuilt Unity game screen capture from within Unity
# Saved Coordinates:
# 1: X=997, Y=294       1
# 2: X=1718, Y=699      1
# 3: X=1720, Y=295      2
# 4: X=2437, Y=699      2
# 5: X=1361, Y=701      3
# 6: X=2080, Y=1109     3

# Define screen capture areas (x, y, width, height)
CAPTURE_REGIONS = [
    # X1,  Y1,   X2  -  X1,  Y2  -  Y1
    (1720, 295, 2437 - 1720, 699 - 295),  # Section 1
    (997, 294, 1718 - 997, 699 - 294),    # Section 2
    (1361, 701, 2080 - 1361, 1109 - 701)  # Section 3
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
