"""
File: meterCommTest.py
Author: Ethan Vosburg 
Date: 02-29-2024
Description: This file will be used to test serial connectivity with the 
Newport Model 1835-c Multi-Function Optical Meter. 
""" 

from ticlib import TicSerial
from time import sleep
import serial
import matplotlib.pyplot as plt
import csv

port = serial.Serial("/dev/tty.usbserial-FT73TWW8", baudrate=9600, timeout=0.1, write_timeout=0.1)
meter = serial.Serial("/dev/tty.usbserial-FTXJ3D28", baudrate=9600, timeout=0.1, write_timeout=0.1)

tic = TicSerial(port)

# Set up motor sequence
tic.halt_and_set_position(0)
tic.energize()
tic.exit_safe_start()

# Define result array
results = []

# Define measurement range
measMin = -50
measMax = 50 + 1

# Prime motor position
tic.set_target_position(measMin * 100)
sleep(14)


for position in range(measMin, measMax):
    # Multiply by 100 to convert to degrees
    position = position * 100
    tic.set_target_position(position)
    print("Target angle: " + str(position))
    sleep(1)
    # currentVariables = tic.get_variables()
    # print("Current position: " + str(currentVariables['current_position']))
    # print("Target position: " + str(currentVariables['target_position']))
    print("Run Meter")
    response = []
    for i in range(10):
        # Send command to trigger measurement
        meterCommand = 'RUN\n'.encode('ascii')
        meter.write(meterCommand)
        # Send command to read measurement
        meterCommand = 'R?\n'.encode('ascii')
        meter.write(meterCommand)

        # Convert scientific notation to float
        response.append(float(meter.readline()))

    # Calculate average magnitude of the 10 readings
    results.append([position / 100, sum(response) / len(response)])
    print("Average Intensity: " + str(results[-1]))
    
# Return to 0 position (home)
tic.set_target_position(0)
# sleep(7)

# Export results to CSV
with open('results.csv', 'w') as f:
    writer = csv.writer(f)
    for result in results:
        writer.writerow(result)

# Create list of angles for plotting
xList = range(measMin, measMax)

# Get results for plotting
results = [x[1] for x in results]

# Plot results
plt.figure()
plt.plot(xList, results)
plt.title('Diode Beam Intensity')
plt.xlabel('Angle (degrees)')
plt.ylabel('Magnitude')
plt.ylim(min(results) * 0.99 , max(results) * 1.01) 
plt.show()
