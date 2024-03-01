# from ticlib import TicUSB
from ticlib import TicSerial
from time import sleep
import serial

port = serial.Serial("/dev/tty.usbserial-FT73TWW8", baudrate=9600, timeout=0.1, write_timeout=0.1)
meter = serial.Serial("/dev/tty.usbserial-FTXJ3D28", baudrate=9600, timeout=0.1, write_timeout=0.1)
tic = TicSerial(port)
# tic = TicUSB()

tic.halt_and_set_position(0)
tic.energize()
tic.exit_safe_start()

positions = [500, 300, 800, 0]
for position in positions:
    tic.set_target_position(position)
    print("Target position: " + str(position))
    print("Run Meter")
    meterCommand = 'run\n'
    meter.write(meterCommand.encode('ascii'))
    # while tic.get_current_position() != tic.get_target_position():
    #     print("Current position: " + str(tic.get_current_position()))
    #     print("Target position: " + str(tic.get_target_position()))
    #     print("Delta: " + str(tic.get_current_position() - tic.get_target_position()))
    #     sleep(0.1)
    # while True:
    #     sinceLastStep = tic.get_time_since_last_step()
    #     sleep(0.1)
    #     print("Time Since Last Step: " + str(sinceLastStep))
    #     if sinceLastStep > 30000:
    #         break
    # print("Current position: " + str(tic.get_current_position()))
    sleep(4)

tic.deenergize()
tic.enter_safe_start()