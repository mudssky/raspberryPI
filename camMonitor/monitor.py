from flask import Flask
from cammonitor import CamMonitor
from flask_cors import CORS
import logging
app = Flask(__name__)
# 开启跨域
CORS(app)
cam = CamMonitor()

@app.route("/monitoring")
def start_monitor():
    logging.debug('start monitoring')
    if cam.open_switch is False:
        cam.run()
    return 'start monitoring'
@app.route('/hello')
def hello():
    logging.debug('hello')
    return 'hello'
@app.route('/stopmonitor')
def stop_monitoring():
    cam.stop()
    return 'stoped'

@app.route('/motiondetecton')
def start_motion_detect():
    cam.motion_detect_on=True
    return 'motion detect on'

@app.route('/motiondetectoff')
def stop_motiondetect():
    cam.motion_detect_on=False
    return 'motion detect off'
if __name__=='__main__':
    app.run(host='127.0.0.1',port='3000',debug=True)


