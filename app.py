from flask import Flask, jsonify, request
import adafruit_dht
import board
import random

app = Flask(__name__)
# Mock data helper (Use this until your wiring is finished)
def get_mock_data(section_id):
    return {
        "section": section_id,
        "temperature": round(random.uniform(20.0, 30.0), 2),
        "humidity": round(random.uniform(40.0, 60.0), 2),
        "gas": round(random.uniform(100, 500), 2)
    }

@app.route('/sensors/<section_id>', methods=['GET'])
def get_section(section_id):
    # Real logic would go here: 
    # temp = dht_device.temperature
    data = get_mock_data(section_id)
    return jsonify(data)

@app.route('/sensors/all', methods=['GET'])
def get_all():
    sections = ["sectionA", "sectionB", "sectionC"]
    all_data = [get_mock_data(s) for s in sections]
    return jsonify(all_data)

@app.route('/read', methods=['GET'])
def manual_read():
    section = request.args.get('section', 'default')
    return jsonify(get_mock_data(section))

if __name__ == '__main__':
    # Run on 0.0.0.0 so it's accessible by your Node.js server IP
    app.run(host='0.0.0.0', port=5000)