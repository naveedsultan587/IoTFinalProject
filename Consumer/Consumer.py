"""
Run this file on Raspberry Pi. This script is responsible for setting up connections to both InfluxDB and an MQTT broker,
 receiving messages over MQTT, and logging them to InfluxDB. It also posts data to a prediction REST API endpoint.
"""

# Importing necessary libraries for environmental variables, data storage, messaging, and HTTP requests
import os
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS
import paho.mqtt.client as mqtt
import json
import requests

# Load environment variables from a ".env" file which stores sensitive information such as URLs and tokens securely
load_dotenv()

# Configuration for InfluxDB: establishing connection parameters using environment variables
BUCKET = os.environ.get('INFLUXDB_BUCKET')
print("Connecting to InfluxDB at URL:", os.environ.get('INFLUXDB_URL'))
client = InfluxDBClient(
    url=str(os.environ.get('INFLUXDB_URL')),
    token=str(os.environ.get('INFLUXDB_TOKEN')),
    org=os.environ.get('INFLUXDB_ORG')
)
write_api = client.write_api(write_options=ASYNCHRONOUS)  # Use asynchronous write to InfluxDB

# MQTT broker configuration: Setting up the MQTT client and connecting to the broker using provided URL and default port 1883
MQTT_BROKER_URL = os.environ.get('MQTT_URL')
MQTT_PUBLISH_TOPIC = "@msg/data"
print("Connecting to MQTT Broker at URL:", MQTT_BROKER_URL)
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.connect(MQTT_BROKER_URL, 1883)

# REST API endpoint for predicting output: fetched from environment variable
predict_url = os.environ.get('PREDICT_URL')
 
def on_connect(client, userdata, flags, rc, properties):
    """Callback function triggered upon successful connection to the MQTT broker."""
    print("Connected with result code "+str(rc))

# Subscribe to MQTT topic to receive data
mqttc.subscribe(MQTT_PUBLISH_TOPIC)
 
def on_message(client, userdata, msg):
    """Callback function triggered when a new message is published on the subscribed MQTT topic."""
    print(msg.topic + " " + str(msg.payload))

    # Deserialize JSON payload received via MQTT
    payload = json.loads(msg.payload)
    write_to_influxdb(payload)

    # Serialize payload to JSON for POST request
    json_data = json.dumps(payload)
    post_to_predict(json_data)

# Function to send data to a REST API for real-time prediction
def post_to_predict(data):
    """Sends data to the REST API endpoint and handles the response."""
    response = requests.post(predict_url, data=data)
    if response.status_code == 200:
        print("POST request successful")
    else:
        print("POST request failed!", response.status_code)

# Function to write data points to InfluxDB
def write_to_influxdb(data):
    """Formats and writes sensor data as points to the designated InfluxDB bucket."""
    point = Point("update_data")\
        .field("Temperature", data["Temperature"])\
        .field("Air_Temperature", data["Air_Temperature"])\
        .field("Humidity", data["Humidity"])\
        .field("Air_Pressure", data["Air_Pressure"])
    write_api.write(BUCKET, os.environ.get('INFLUXDB_ORG'), point)

# Register MQTT callback functions and initiate an infinite loop to keep listening for messages
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.loop_forever()
