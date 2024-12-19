import machine
from machine import Pin
from bmp280 import BMP280

i2c = machine.I2C(id=1, sda=Pin(26), scl=Pin(27)) #id=channel
bmp = BMP280(i2c)


while True:
    print(bmp.temperature, bmp.pressure)

