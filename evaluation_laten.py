from machine import Pin, I2C
import network
import utime
from bmp280 import BMP280  # Use BMP280 library
import ssl
from umqtt import MQTTClient
import time
import json
import math  # For checking NaN

# Wi-Fi Credentials
ssid = "TP-Link_3C96"
password = "khan@1322.."

# Initialize Counters and Metrics
messages_sent = 0
messages_received = 0
latency_log = []
payload_size_log = []
start_time = time.time()
send_time = None  # For device responsiveness measurement

# Initialize Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.config(pm=0xa11140)  # Disable powersave mode
wlan.connect(ssid, password)

max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('Waiting for connection...')
    utime.sleep(1)

# Handle connection error
if wlan.status() != 3:
    raise RuntimeError('Wi-Fi connection failed')
else:
    print('Connected')
    status = wlan.ifconfig()
    print('IP = ' + status[0])

# Initialize I2C and Scan for Devices
i2c = I2C(1, sda=Pin(26), scl=Pin(27), freq=100000)
devices = i2c.scan()
if len(devices) == 0:
    print("No I2C devices found. Check wiring!")
else:
    print("I2C devices found:", [hex(device) for device in devices])

# Initialize BMP280 Sensor
try:
    bmp = BMP280(i2c)  # Initialize BMP280 sensor
    print("BMP280 Sensor Initialized Successfully")
except Exception as e:
    print(f"Error initializing BMP280: {e}")

# Initialize MQTT
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.verify_mode = ssl.CERT_NONE

def connectMQTT():
    client = MQTTClient(client_id=b"topic",
                        server=b"609bf6e7c62f4151950f1269013f68c7.s1.eu.hivemq.cloud",
                        port=8883,
                        user=b"Iot20242024",
                        password=b"Iot20242024",
                        keepalive=7200,
                        ssl=context)
    client.connect()
    return client

client = connectMQTT()

# Sensor Data Validation
def is_valid(value):
    return not (math.isnan(value) or value is None)

# Publish Function with Latency and Payload Tracking
def publish(topic, value):
    global messages_sent
    try:
        publish_time = utime.ticks_us()
        payload = json.dumps({"value": value})
        payload_size = len(payload.encode('utf-8'))
        
        client.publish(topic, payload)
        latency = utime.ticks_diff(utime.ticks_us(), publish_time) / 1_000_000
        
        # Increment counters and log metrics
        messages_sent += 1
        latency_log.append(latency)
        payload_size_log.append(payload_size)
        
        print(f"Published: {payload}")
        print(f"Payload Size: {payload_size} bytes")
        print(f"Latency: {latency:.6f} seconds")
        print("Publish Done")
    except Exception as e:
        print(f"Error during publish: {e}")

# Callback Function for MQTT Messages
def on_message(topic, msg):
    global messages_received, send_time
    received_time = utime.ticks_us()
    messages_received += 1
    print(f"Received message: {msg} on topic: {topic}")
    
    if msg == b"ON":
        led_pin.on()  # Turn on LED
        print("LED ON")
        if send_time is not None:
            # Calculate device responsiveness
            responsiveness = utime.ticks_diff(received_time, send_time) / 1_000  # Convert to milliseconds
            print(f"LED Turned ON after {responsiveness:.2f} ms from condition detection")
            send_time = None  # Reset send_time after calculating responsiveness
    elif msg == b"OFF":
        led_pin.off()  # Turn off LED
        print("LED OFF")

client.set_callback(on_message)
client.subscribe(b"picow/control")

# Message Loss Calculation
def calculate_message_loss():
    if messages_sent > 0:
        message_loss = ((messages_sent - messages_received) / messages_sent) * 100
        print(f"Messages Sent: {messages_sent}")
        print(f"Messages Received: {messages_received}")
        print(f"Message Loss: {message_loss:.2f}%")

# Main Loop with Throughput and Device Responsiveness
led_pin = Pin('LED', Pin.OUT)

while True:
    try:
        # Read Sensor Data
        temperature = bmp.temperature
        pressure = bmp.pressure
        
        # Validate Sensor Data
        if is_valid(temperature) and is_valid(pressure):
            print(f"Temperature: {temperature:.2f}C")
            print(f"Pressure: {pressure:.2f}hPa")
            
            # Publish Sensor Data
            publish('picow/temperature', f"{temperature:.2f}")
            publish('picow/pressure', f"{pressure:.2f}")
            
            # Check for Temperature Condition (>23°C)
            if temperature > 23:
                send_time = utime.ticks_us()
                publish('picow/control', 'ON')
                print(f"Condition Met: Temperature > 23°C. LED ON Sent at {send_time}")
            else:
                publish('picow/control', 'OFF')
                print("Condition Not Met: Temperature ≤ 23°C. LED OFF Command Sent")
            
        else:
            print("Invalid sensor data: Skipping publish.")
        
        # Check for Incoming Messages
        client.check_msg()
        
        # Periodically Calculate and Print Throughput
        if messages_sent % 10 == 0 and messages_sent > 0:
            elapsed_time = time.time() - start_time
            throughput = messages_sent / elapsed_time
            print(f"Throughput: {throughput:.2f} messages/second")
        
        # Periodic Message Loss Calculation
        if messages_sent % 10 == 0 and messages_sent > 0:
            calculate_message_loss()
        
        # Delay
        utime.sleep(5)
    except Exception as e:
        print(f"Error in main loop: {e}")

