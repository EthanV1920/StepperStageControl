"""
File: meterCommTest.py
Author: Ethan Vosburg 
Date: 02-29-2024
Description: This file will be used to test serial connectivity with the 
Newport Model 1835-c Multi-Function Optical Meter. 
""" 

from ticlib import TicSerial
from time import sleep
from pynput import keyboard
from tqdm import tqdm

import numpy as np
import sys
import serial
import matplotlib.pyplot as plt
import csv
import configparser

# Set up Configuration File
config = configparser.ConfigParser()
config.read("diodeTestConfig.ini")
print(config.sections())


# Define Global Variables
devicesConnected = False
stepperRunning = True
symbols = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▁"]
i = 0

while devicesConnected == False:
    devicesConnected = True 
    i = (i + 1) % len(symbols)
    sys.stdout.write("\033[K")   # Erase the current line
    try:
        port = serial.Serial(config['COMMPORTS']['tic'], baudrate=9600, timeout=0.1, write_timeout=0.1)
        tic = TicSerial(port)
        print('\r✓', flush=True, end='')
        sys.stdout.write("Serial port detected for tic\n")
        
    except serial.SerialException:
        print('\r\033[K%s' % symbols[i], flush=True, end='')
        sys.stdout.write("No serial port detected for tic\n")
        sys.stdout.flush()
        devicesConnected = False
        tic = None

    sys.stdout.write("\033[K")   # Erase the current line
    print('\r\033[K%s' % symbols[i], flush=True, end='')
    
    try:
        meter = serial.Serial(config['COMMPORTS']['meter'], baudrate=9600, timeout=0.1, write_timeout=0.1)
        print('\r✓', flush=True, end='')
        sys.stdout.write("Serial port detected for meter\n")
    except serial.SerialException:
        sys.stdout.write("No serial port detected for meter\n")
        sys.stdout.flush()
        devicesConnected = False

    sys.stdout.write("\033[K")   # Erase the current line
    print('\r\033[K%s' % symbols[i], flush=True, end='')

    try:
        source = serial.Serial(config['COMMPORTS']['source'], baudrate=38400, timeout=0.1, write_timeout=0.1)
        print('\r✓', flush=True, end='')
        sys.stdout.write("Serial port detected for source\n")
    except serial.SerialException:
        sys.stdout.write("No serial port detected for source\n")
        sys.stdout.flush()
        devicesConnected = False

    
    # Wait for 1 second and try again
    if devicesConnected == False:
        sys.stdout.write("\033[3A")  # Move the cursor up 3 lines
        sleep(0.1)

print("All devices connected")

def setup(measMin):
    # Set up motor sequence
    tic.halt_and_set_position(0)
    tic.energize()
    tic.exit_safe_start()

# def on_press(key):
#     if key == keyboard.Key.esc:
#         print("Stopping motor and moving to home position...")
#         tic.set_target_position(0)
#         stepperRunning = False
#         sleep(5)
#         while tic.get_current_velocity() != 0:
#             sleep(.1)
#         return False  # Stop listener


def stepper_routine(measMin, measMax, forward, waitTime):
    # with keyboard.Listener(on_press=on_press) as listener:

    startPosition = measMin
    if not forward:
        startPosition = startPosition * -1

    tic.set_target_position(startPosition * 100)
    sleep(2)
    while tic.get_current_velocity() != 0:
        sleep(.2)

    # Define result array
    results = []
    source.write("LAS:OUT ON\n".encode("ascii"))

    if stepperRunning:
        # for position in tqdm(range(measMin, measMax), desc="Stepping Motor"):
        for position in tqdm(range(measMin, measMax), desc="Stepping Motor"):
            # Multiply by 100 to convert to degrees
            position = position * 100
            if not forward:
                position = position * -1
            tic.set_target_position(position)
            sys.stdout.write("Target angle: " + str(position) + "\n")
            sleep(waitTime)
            # while tic.get_current_velocity() != 0:
            #     sleep(.1)
            
            response = []

            for i in range(5):
                # Send command to trigger measurement
                meterCommand = "RUN\n".encode("ascii")
                meter.write(meterCommand)
                # Send command to read measurement
                meterCommand = "R?\n".encode("ascii")
                meter.write(meterCommand)
                sleep(0.1)

                # Convert scientific notation to float
                response.append(float(meter.readline()))

            # Calculate average magnitude of the 10 readings
            results.append([position / 100, sum(response) / len(response)])
            sys.stdout.write("Average Intensity: " + str(results[-1]) + "\n")
            sys.stdout.write("\033[3A")  # Move the cursor up 3 lines
            sys.stdout.flush()

        # listener.join()


    source.write("LAS:OUT OFF\n".encode("ascii"))




    # Export results to CSV
    resultFile = f"results_{measMin}_{measMax}_{waitTime}_{forward}.csv"
    with open(resultFile, "w") as f:
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
    plt.title("Diode Beam Intensity")
    plt.xlabel("Angle (degrees)")
    plt.ylabel("Magnitude")
    plt.ylim(min(results) * 0.99, max(results) * 1.01)
    # plt.show()
    return np.argmax(results)


if __name__ == "__main__":
    """This is executed when run from the command line"""
    # Define measurement range
    while True:
        try:
            # In terminal user input
            # measMax = int(input("Measurement extent: "))
            measMax = int(config['TESTPARAMS']['sweepDegrees'])
            break
        except ValueError:
            print("That's not a valid integer. Please try again.")
    measMin = -measMax
    measMax = measMax + 1
    print("Setting up motor...")
    setup(measMin)
    delta = 1
    waitTime = 3
    while delta != 0:
        maxForward = stepper_routine(measMin, measMax, True, waitTime)
        maxReverse = stepper_routine(measMin, measMax, False, waitTime)
        maxReverse = (measMax + (-measMin)) - maxReverse
        print("\n\n\n")
        sys.stdout.write("Max Forward: " + str(maxForward) + "\n")
        sys.stdout.write("Max Reverse: " + str(maxReverse) + "\n")
        delta = abs(maxForward - maxReverse)
        print("Delta: " + str(delta))
        if delta != 0:
            waitTime = waitTime + .5
            sys.stdout.write("Adjusting wait time to: " + str(waitTime) + "\n")
        sys.stdout.flush()

    
    print("Measurement complete")
    print("Final wait time: " + str(waitTime))
    # Return to 0 position (home)
    tic.set_target_position(0)
    sleep(2)
    while tic.get_current_velocity() != 0:
        sleep(.2)
