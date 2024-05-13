
# IoT Final Project - Group 4
## Farhan Iqbal
## Zahid Maqbool
## Naveed Sultan
## Shahzad Ali

## Overview
This project demonstrates an IoT system using ESP32 for sensor data collection, MQTT for messaging, and a Raspberry Pi as the command center. It includes real-time data processing and machine learning for predictive analytics.

## Components
- **ESP32**: Handles sensor data and publishes it to MQTT.
- **Raspberry Pi**: Acts as an MQTT broker and hosts Docker containers for data processing.
- **Machine Learning**: Includes training and real-time prediction models for temperature data. 
- **InfluxDb**: To store Real time and predicted values

## Repository Structure
- `/ESP32/`: Code for interfacing ESP32 with sensors and MQTT.
- `/Consumer/`: Docker setup for MQTT and data processing on Raspberry Pi.
- `/DataAnalytics/Model/`: Python scripts for training machine learning models.
- `/DataAnalytics/RealTimePrediction/`: Flask app for deploying models and making predictions.

## Setup Instructions
1. **Influxdb**: Deploy influxdb on cloud to store data.
1. **ESP32 Setup**: Run ESP32 code to your ESP32 devices to collec sonsor data.
2. **Raspberry Pi Setup**: Run Consumer file in Raspberry by using configuration provided to retrieve data from esp32 and write it to ifluxdb and provide for real time prediction.
3. **Model Training**: Execute scripts on Model file to train model. Get the csv file from influxdb.
4. **Real-Time Prediction**: Deploy your trained model to predict temperature and store it to the influxdb.


## Technologies Used
- **ESP32** for hardware interfacing.
- **MQTT** for messaging.
- **Docker** and **Flask** for application deployment.
- **InfluxDB** for data storage.
- **Machine Learning** with Python for predictive analytics.

---

