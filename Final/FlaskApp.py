import io
import logging
from flask import Flask, Response, jsonify, render_template, request, send_file
import threading
import sys
import paho.mqtt.client as mqtt
import datetime
import os

app = Flask(__name__)

# Global variable to store the latest data
data_store = {"temperature": "N/A", "humidity": "N/A"}
data_log = []
data_store_lock = threading.Lock()

USERNAME = "admin"
PASSWORD = "admin"


# Authentication decorator
def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
        "You need to log in with proper credentials", 
        401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# MQTT Callback when a message is received
def on_message(client, userdata, message):
    global data_store
    payload = message.payload.decode()
    try:
        payloadSplit = payload.split(":")
        temp = payloadSplit[0].strip()
        humidity = payloadSplit[1].strip()
        with data_store_lock:
            data_store["temperature"] = temp
            data_store["humidity"] = humidity
            data_log.append({
                "temperature": temp,
                "humidity": humidity,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            print(data_store)
    except Exception as e:
        print(f"Failed to parse message: {e}")
#index
@app.route('/')
@requires_auth
def index():
    data_log.clear()
    return render_template('index.html', data=data_store)
#list
@app.route('/list')
@requires_auth
def list_readings():
    data_log.clear()
    return render_template('list.html', data=data_log)

@app.route('/download', methods=['GET'])
@requires_auth
def download_file():
    if not data_log:
        return jsonify({"message": "No data to download"}), 400

    output = io.StringIO()
    output.write("Sensor Readings Log\n")
    output.write("====================\n")
    for reading in data_log:
        output.write(
            f"Time: {reading['timestamp']}, "
            f"Temperature: {reading['temperature']} °C, "
            f"Humidity: {reading['humidity']} %\n"
        )    
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()), 
        as_attachment=True, 
        download_name="readings.txt", 
        mimetype="text/plain"
    )

@app.route('/data')
def get_data():
    with data_store_lock:
        print(f"Accessing data_store: {data_store}")
        response = jsonify(data_store)
        return response

def start_mqtt():
    client = mqtt.Client()
    client.on_message = on_message
    if client.connect("RPI", 1883, 60) != 0:
        print("could not connect to mqtt broker")
        sys.exit(1)

    client.subscribe("temp")
    #client.disconnect
    try:
        print("Press CTRL+C exit..")
        client.loop_forever()
    except Exception:
        print("caugh exception, something went wrong..")
    finally:
        print("disconnecting from MQTT")
        client.disconnect()
        

if __name__ == "__main__":
    # Start MQTT client in a separate thread
    
    mqtt_thread = threading.Thread(target=start_mqtt)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    # Run the Flask app
    app.run(debug=True)
