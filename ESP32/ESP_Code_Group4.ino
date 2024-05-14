#include <Wire.h>
#include <Adafruit_BMP280.h>
#include "Adafruit_SHT4x.h"
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <esp_sleep.h>

/********************* WiFi and MQTT Broker Configuration ****************************/
const char* ssid = "Farhan";                  // WiFi SSID
const char* password = "1234asdfgh";                   // WiFi password
const char* mqtt_server = "192.168.171.188";             // MQTT Broker IP address
const int mqtt_port = 1883;                          // MQTT Broker port
const char* mqtt_Client = "";                        // MQTT Client ID (if needed)
const char* mqtt_username = "";                      // MQTT username (if needed)
const char* mqtt_password = "";                      // MQTT password (if needed)
char msg[200];                                       // Buffer for publishing messages
WiFiClient espClient;
PubSubClient client(espClient);

/******************* Sensor Definitions **********************/
Adafruit_BMP280 bmp;                                 // Define an instance for the BMP280 sensor
Adafruit_SHT4x sht4 = Adafruit_SHT4x();             // Define an instance for the SHT4x sensor
sensors_event_t humidity, temp;                     // Events to store sensor readings

/************** Queue Structure Definition **********/
struct dataRead {                                    // Structure to hold sensor data
  float Temperature;
  float Humidity;
  float airPressure;
  float airTemperature;
};
TaskHandle_t sendTaskHandle;
TaskHandle_t receiveTaskHandle;
QueueHandle_t Queue;                                 // Handle for the FreeRTOS queue

// Constants for deep sleep and timing
const long uS_TO_S_FACTOR = 1000000UL;               // Microseconds to seconds conversion factor
const int SLEEP_DURATION = 55;                       // Sleep duration in seconds
uint8_t counterRestart = 0;                          // Counter for restart attempts

void setup() {
  Serial.begin(115200);
  setCpuFrequencyMhz(80);                            // Set ESP32's CPU frequency to 80MHz for power efficiency
  Serial.print("CPU Frequency is: ");
  Serial.print(getCpuFrequencyMhz());
  Serial.println(" Mhz");

  esp_sleep_enable_timer_wakeup(SLEEP_DURATION * uS_TO_S_FACTOR);  // Setup timer for deep sleep wakeup
  Wire.begin(41, 40);                                // Start I2C communication
  if (bmp.begin(0x76)) {                             // Initialize BMP280 sensor
    Serial.println("BMP280 sensor ready");
  }
  if (sht4.begin()) {                                // Initialize SHT4x sensor
    Serial.println("SHT4x sensor ready");
  }

  WiFi.begin(ssid, password);                        // Connect to WiFi network
  Serial.print("Connecting to WiFi ");
  while (WiFi.status() != WL_CONNECTED) {
    counterRestart++;
    delay(500);
    Serial.print(".");
    if(counterRestart > 20) {                        // Restart ESP32 if not connected after 20 attempts
      ESP.restart();
    }
  }
  Serial.println("\nWiFi Connected");

  client.setServer(mqtt_server, mqtt_port);          // Setup MQTT connection
  if (!client.connected()) {
    if (client.connect(mqtt_Client, mqtt_username, mqtt_password)) {
      Serial.println("connected to MQTT");
    }
  }

  Queue = xQueueCreate(100, sizeof(struct dataRead)); // Create a queue capable of holding 100 `dataRead` structs
  xTaskCreate(subspendAllTask, "Subspend_Task", 2048, NULL, 3, NULL);  // Task to manage task suspension
  xTaskCreate(sendToQueue, "Sender", 2048, NULL, 1, &sendTaskHandle);  // Task to send sensor data to the queue
  xTaskCreate(receiveFromQueue, "Receiver", 2048, NULL, 2, &receiveTaskHandle);  // Task to process data from the queue
}

void loop() {
  // The loop function is intentionally empty because task scheduling is handled by FreeRTOS
}
// Task that gets data from sensors and sends it to the queue.
void sendToQueue(void *parameter) {
  while (1) {
    // Read data from sensor
    struct dataRead currentData;
    sht4.getEvent(&humidity, &temp);  // Retrieve current humidity and temperature data from the SHT4x sensor.
    currentData.Temperature = temp.temperature;  // Store the temperature value.
    currentData.Humidity = humidity.relative_humidity;  // Store the humidity value.
    currentData.airTemperature = bmp.readTemperature();  // Read and store air temperature from BMP280.
    currentData.airPressure = bmp.readPressure() / 1000; // Convert and store air pressure in kPa from BMP280.
    
    // Send structured data to the queue. If the queue is full, wait indefinitely until space is available.
    if (xQueueSend(Queue, &currentData, portMAX_DELAY) != pdPASS) {
      Serial.println("Failed to send data to the queue");  // Log an error message if data cannot be queued.
    }
    
    // Delay task for 60 seconds to throttle the data reading rate.
    vTaskDelay(60 * 1000 / portTICK_PERIOD_MS); 
  }
}

// Task that receives data from the queue and sends it over MQTT.
void receiveFromQueue(void *parameter) {
  while (1) {
    struct dataRead currentData;
    // Attempt to receive data from the queue indefinitely.
    if (xQueueReceive(Queue, &currentData, portMAX_DELAY) == pdPASS) {
      // Debugging outputs that could be uncommented for additional serial monitoring.
      // Serial.println("Temp data: "+String(currentData.Temperature)+" °C");
      // Serial.println("AirTemp data: "+String(currentData.airTemperature) + " °C");
      // Serial.println("AirPressure data: "+String(currentData.airPressure)+" kPa");
      // Serial.println("Humidity data: "+String(currentData.Humidity)+ " %(RH)");
    }

    // Check MQTT connection status and reconnect if necessary.
    if (!client.connected()) {
      if (client.connect(mqtt_Client, mqtt_username, mqtt_password)) {
        Serial.println("MQTT connected");
      }
    }
    client.loop();  // Maintain active MQTT connection.

    // Prepare JSON string with sensor data.
    String data = "{\"Temperature\":" + String(currentData.Temperature) +
                  ",\"Humidity\":" + String(currentData.Humidity) +
                  ",\"TemperatureS2\":" + String(currentData.airTemperature) +
                  ",\"Pressure\":" + String(currentData.airPressure) + "}";
    Serial.println(data);  // Debug output to Serial.
    data.toCharArray(msg, (data.length() + 1));  // Convert string to char array.
    client.publish("@msg/data", msg);  // Publish sensor data to MQTT topic.
  }
}

// Task to manage system suspension and power savings.
void subspendAllTask(void *pvParameters) {
  while (1) {
    Serial.println("All tasks will suspend in 1mn");
    // Delay for 3000 milliseconds.
    vTaskDelay(3 * 1000 / portTICK_PERIOD_MS); 
    // Suspend specific tasks to free up resources.
    vTaskSuspend(sendTaskHandle);
    vTaskSuspend(receiveTaskHandle);
   
    // Disconnect WiFi to save power.
    WiFi.disconnect(); 
 
    esp_deep_sleep_start();
  }
}
