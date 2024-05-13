"""
Real-Time Prediction- Group 4
This script sets up a Flask web server to handle real-time temperature predictions using a pre-trained SVM model.
"""

# Importing necessary libraries
import joblib
import pandas as pd
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS
import json

# Loading the trained SVM model and the column names used for the model input
svm_model = joblib.load('svm_model.pkl')  # Load SVM model from file
svm_columns = joblib.load("svm_model_columns.pkl")  # Load column names for the model input

# Load environment variables from a ".env" file for configuration and security
load_dotenv()

# Configuration for InfluxDB: establish connection details using environment variables
BUCKET = os.environ.get('INFLUXDB_BUCKET')
print("Connecting to InfluxDB at URL:", os.environ.get('INFLUXDB_URL'))
client = InfluxDBClient(
    url=str(os.environ.get('INFLUXDB_URL')),
    token=str(os.environ.get('INFLUXDB_TOKEN')),
    org=os.environ.get('INFLUXDB_ORG')
)
write_api = client.write_api()  # Asynchronous write to InfluxDB

# Initialize Flask app for creating a REST API server
app = Flask(__name__)

# A list to store the last five temperature readings, necessary for model input
recent_temperatures = []

# Default route to check if the model is loaded properly
@app.route('/')
def check_model():
    if svm_model:
        return "Model is ready for prediction"
    return "Server is running but something is wrong with the model"

# Route to handle POST requests for predictions
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Extracting JSON data from the POST request
        json_text = request.data
        json_data = json.loads(json_text)

        # Validate presence of expected temperature key in the data
        if 'Temperature' not in json_data:
            return "Invalid input: 'Temperature' key not found in input data.", 400
        
        # Read and append the temperature value to the recent temperatures list
        temp = json_data['Temperature']
        recent_temperatures.append(temp)
        
        # Maintain the list at exactly five readings to match the model's input requirements
        if len(recent_temperatures) > 5:
            recent_temperatures.pop(0)
        
        # Check if enough readings are available to make a prediction
        if len(recent_temperatures) < 5:
            return "Insufficient data: Waiting for five temperature readings before predicting.", 200
        
        # Use recent temperature readings to make a prediction with the SVM model
        query = pd.DataFrame([recent_temperatures], columns=svm_columns)
        predict_sample = svm_model.predict(query)
        predicted_output = float(predict_sample[0])  # Converting prediction result to float for precision
        
        # Log and write the predicted temperature to InfluxDB
        point = Point("predicted_temperature")\
            .field("next_temperature", predicted_output)\
            .field("Error", abs((predicted_output - float(temp)) * 100 / float(temp)))
        write_api.write(BUCKET, os.environ.get('INFLUXDB_ORG'), point)

        # Return the predicted temperature in JSON format
        return jsonify({"Predicted output": predicted_output}), 200
    
    except Exception as e:
        # Handle errors gracefully and provide feedback
        return f"Error processing the prediction request: {str(e)}", 400
    
# Condition to ensure the script runs only when executed, not when imported
if __name__ == '__main__':
    app.run()  # Start the Flask application
