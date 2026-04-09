from flask import Flask, jsonify, request
import adafruit_dht
import board
import time
import json
import threading
from datetime import datetime
import random
from computer_vision import read_camera, release_camera
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
    while True:
        print("Collecting sensor data")
        cv_data = read_camera()
        bme_data = read_bme280()
        gas_reading = read_mq2()

        # Buffer the gas reading for sliding window features
        gas_readings_buffer.append(gas_reading)
        if len(gas_readings_buffer) > WINDOW_SIZE * 2:
            del gas_readings_buffer[: len(gas_readings_buffer) - WINDOW_SIZE * 2]

        # Run gas model inference
        features = engineer_features(gas_readings_buffer, window_size=WINDOW_SIZE)
        gas_prediction = predict_gas(features)

        record={
            "timestamp": datetime.now().isoformat(),
            # CV data
            "cvStage": cv_data["cvStage"],
            "cvConfidence": cv_data["cvConfidence"],
            "imageBase64": cv_data["imageBase64"],

            # BME280 data
            "temperature": bme_data['temperature'],
            "humidity": bme_data['humidity'],

            # Gas sensor raw data
            "ethylenePpm": gas_reading["ppm"],
            "voltage": gas_reading["voltage"],
        }

        # Add gas model prediction (None during buffering phase)
        if gas_prediction:
            record["gasStage"] = gas_prediction["gasStage"]
            record["gasConfidence"] = gas_prediction["gasConfidence"]
            record["action"] = gas_prediction["action"]
            record["ppmSlope"] = gas_prediction["ppmSlope"]
        else:
            buffered = len(gas_readings_buffer)
            print(f"  Gas model buffering: {buffered}/{WINDOW_SIZE} readings")
            record["gasStage"] = None
            record["gasConfidence"] = None
            record["action"] = None
            record["ppmSlope"] = None

        try:
            with open(DATA_FILE, "r") as f:
                history = json.load(f)
        except FileNotFoundError:
            history = []

        history.append(record)
        
        with open(DATA_FILE, "w") as f:
            json.dump(history, f, indent = 2)
        print(f"Saved reading #{len(history)}")
        time.sleep(60)

@app.route('/sensors/fetch/latest', methods=["GET"])
def get_latest():
    try:
        with open(DATA_FILE, "r") as f:
            history = json.load(f)
        if history:
            return jsonify(history[-1])
        else:
            return jsonify({"error": "No data yet"})
    except Exception as e:
        return jsonify({"error": str(e)})

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
    app.run(host='0.0.0.0', port=5000)