from machine import Pin, I2C
import network
import utime
from bmp280 import BMP280  # Use BMP280 library
import ssl
from umqtt import MQTTClient
import config
import time

ssid = "TP-Link_3C96"
password = "khan@1322.."
message_count = 0
latency_log = []
start_time = time.time()

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.config(pm=0xa11140)  # Disable powersave mode
wlan.connect(ssid, password)

max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    utime.sleep(1)

# Handle connection error
if wlan.status() != 3:
    raise RuntimeError('wifi connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])
#initialise I2C
i2c=I2C(1,sda=Pin(26), scl=Pin(27), freq=100000)
bmp = BMP280(i2c)  # Initialize BMP280 sensor
led_pin = Pin('LED', Pin.OUT)
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
def publish(topic, value):
    print(topic)
    print(value)
    client.publish(topic, value)
    print("publish Done")
def on_message(topic, msg):
    print(f"Received message: {msg} on topic: {topic}")
    if msg == b"ON":
        led_pin.on()  # Turn on the LED
        print("LED ON")
    elif msg == b"OFF":
        led_pin.off()  # Turn off the LED
        print("LED OFF")
client.set_callback(on_message)
client.subscribe(b"picow/control")
while True:
    # Read sensor data
    temperature = bmp.temperature  # Read temperature from BMP280
    pressure = bmp.pressure 
    #humidity = sensor_reading.values[2]
    publish_time = time.time()
    publish('picow/temperature', f"{temperature:.2f}")
    publish('picow/pressure', f"{pressure:.2f}")
    response_time = time.time()
    latency = response_time - publish_time
    latency_log.append(latency)
    message_count += 1


    print(f"Temperature: {temperature}C")
    print(f"Pressure: {pressure}hPa")
    # Publish as MQTT payload
    #publish('picow/temperature', f"{temperature:.2f}")
    #publish('picow/pressure', f"{pressure:.2f}")
    #publish('picow/humidity', humidity)
    print('Latency is: ',latency)
    print('message_count is: ',message_count)
    
    client.check_msg()

    # Delay 5 seconds
    utime.sleep(5)
    
    #import time



# Inside the publish function




