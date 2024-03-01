"""
File: meterCommTest.py
Author: Ethan Vosburg 
Date: 02-29-2024
Description: This file will be used to test serial connectivity with the 
Newport Model 1835-c Multi-Function Optical Meter. 
""" 

import serial

meter = serial.Serial(port='/dev/tty.usbserial-FTXJ3D28', baudrate=9600, timeout=0.1, write_timeout=0.1)

print("Run Meter")
meterCommand = 'RUN\n'.encode('ascii')
meter.write(meterCommand)
meterCommand = 'R?\n'.encode('ascii')
meter.write(meterCommand)
response = meter.readline()
print(response)
# meter.write('run')
meter.close()

# positions = [500, 300, 800, 0]
# for position in positions:
#     print("Run Meter")
#     meterCommand = 'run'
#     meter.write(meterCommand.encode('ascii'))