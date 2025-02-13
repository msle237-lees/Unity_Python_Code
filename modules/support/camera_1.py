from flask import Flask, render_template, Response, Blueprint
from support import routes
from support.WebCamService import WebCam

zedcam_blueprint = Blueprint('camera_1', __name__)

@zedcam_blueprint.route('/video_0')
def video_0():
    try:
        # Replace with your IP camera URL
        zedcam = WebCam(camera_number=0)
        return Response(routes.gen(zedcam), mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as err:
        return Response(f'Error {err}')