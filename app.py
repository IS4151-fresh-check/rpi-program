from flask import Flask, jsonify, request
import adafruit_dht
import board
import time
import json
import os
import threading
from datetime import datetime
import random
from computer_vision import read_camera, release_camera
from mq2 import read_mq2, calibrate_mq2
from bme import read_bme280
from mq2 import read_mq2
from gas_features import engineer_features
from gas_model import predict_gas, WINDOW_SIZE
import atexit
import signal
import sys

app = Flask(__name__)
DATA_FILE = "/home/pi/sensor_readings.json"

# Buffer for gas model — persists across sensor_loop iterations
gas_readings_buffer = []

def sensor_loop():
    calibrate_mq2()

    while True:
        print("Collecting sensor data")
        try:
            cv_data = read_camera()
            bme_data = read_bme280()
            mq_data = read_mq2()

            record={
                "timestamp": datetime.now().isoformat(),
                "cvStage": cv_data["cvStage"],
                "cvConfidence": cv_data["cvConfidence"],
                "imageBase64": cv_data["imageBase64"],
                "temperature": bme_data['temperature'],
                "humidity": bme_data['humidity'],
                "gas_voltage": mq_data.get('gas_voltage'),
                "ppm": mq_data.get('lpg_ppm')
            }
            history = []
            if os.path.exists(DATA_FILE):
                try:
                    with open(DATA_FILE, "r") as f:
                        history = json.load(f)
                except json.JSONDecodeError:
                        history = []

            history.append(record)
            history = history[-60:]

            with open(DATA_FILE, "w") as f:
                json.dump(history, f, indent=2)
            
            print(f"Reading saved. History size: {len(history)}")
        except Exception as e:
            print(f"Error in sensor loop: {e}")
        time.sleep(30)

@app.route('/sensors/fetch/latest', methods=["GET"])
def get_latest():
    try:
        if not os.path.exists(DATA_FILE):
            return jsonify({"error": "No data file found"}), 404
            
        with open(DATA_FILE, "r") as f:
            history = json.load(f)
            
        if history:
            # Return ONLY the last record to save bandwidth (Base64 is heavy!)
            return jsonify(history[-1])
        else:
            return jsonify({"error": "No readings recorded yet"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cleanup():
    print("Shutting down")
    release_camera()

def handle_exit(signum, frame):
    cleanup()
    sys.exit(0)

if __name__ == '__main__':
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Run on 0.0.0.0 so it's accessible by your Node.js server IP
    threading.Thread(target=sensor_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)