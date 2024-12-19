import network
import time
from machine import Pin, I2C
import ujson
from simple import MQTTClient
from bmp280 import BMP280  # Import the BMP280 library
from wifi import WiFiHelper

# MQTT Server Parameters
MQTT_CLIENT_ID = "micropython-weather-demo"
MQTT_BROKER    = "broker.mqttdashboard.com"
MQTT_USER      = ""
MQTT_PASSWORD  = ""
MQTT_TOPIC     = "wokwi-weather"

# Initialize BMP280 sensor
i2c = I2C(id=1, scl=Pin(27), sda=Pin(26))  # Adjust GPIO pins for Pico W
sensor = BMP280(i2c)

# Connect to WiFi
# WiFi credentials
SSID = "vivo V25 Pro"
PASSWORD = "surekha123"

# Create an instance of the WiFiHelper
wifi = WiFiHelper(SSID, PASSWORD)

# Connect to WiFi
if wifi.connect():
    # Test internet connection
    wifi.test_connection()
else:
    print("Unable to connect. Check WiFi credentials.")

# Connect to MQTT server
print("Connecting to MQTT server... ", end="")
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, user=MQTT_USER, password=MQTT_PASSWORD)
client.connect()
print("Connected!")

prev_weather = ""

while True:
    print("Measuring weather conditions... ", end="")
    # Read temperature and pressure from the BMP280
    temperature = sensor.temperature
    pressure = sensor.pressure  # Pressure in hPa

    # Compose the message
    message = ujson.dumps({
        "temp": temperature,
        "pressure": pressure
    })

    # Publish if there's a change
    if message != prev_weather:
        print("Updated!")
        print(f"Reporting to MQTT topic {MQTT_TOPIC}: {message}")
        client.publish(MQTT_TOPIC, message)
        prev_weather = message
    else:
        print("No change")
    
    time.sleep(0.05)

