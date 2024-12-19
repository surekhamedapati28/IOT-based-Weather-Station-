from machine import Pin
from bmp280 import BMP280
import network
import socket
import time
import config


# setup wifi
ssid = config.ssid
password = config.pwd

# connect to wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

connection_timeout = 10
while connection_timeout > 0:
    if wlan.status() == 3: # connected
        break
    connection_timeout -= 1
    print('Waiting for Wi-Fi connection...')
    time.sleep(1)

# check if connection successful
if wlan.status() != 3: 
    raise RuntimeError('[ERROR] Failed to establish a network connection')
else: 
    print('[INFO] CONNECTED!')
    network_info = wlan.ifconfig()
    print('[INFO] IP address:', network_info[0])

# set up socket and listen on port 80
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)  # Listen for incoming connections

print('[INFO] Listening on', addr)

# generate html
def generate_html(press, temp):
    html = f"""\
    HTTP/1.1 200 OK
    Content-Type: text/html

    <!DOCTYPE html>
    <html>
      <head>
          <title>Raspberry Pi Pico Web Server</title>
          <meta http-equiv="refresh" content="2">
      </head>
      <body>
          <h1>Sensing values</h1>
          <h3>Presure (Pa): {press}</h3>
          <h3>Temperature (C): {temp}</h3>
      </body>
    </html>
    """
    return str(html)

# Define I2C connection and BMP 
i2c = machine.I2C(id=1, sda=Pin(14), scl=Pin(15)) #id=channel
bmp = BMP280(i2c)

# accept connections + send HTTP response
while True:
    cl, addr = s.accept()
    print('[INFO] Client connected from', addr)
    
    # receive request
    request = cl.recv(1024)
    print('[INFO] Request:', request)
    
    # generate the response
    response = generate_html(bmp.pressure, bmp.temperature)
    
    # send the response to the client
    cl.send(response)
    
    # close connection
    cl.close()


# 