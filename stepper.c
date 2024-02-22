#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>

void main() {
    // Open the serial port
    int serialPort = open("/dev/usbserial-FT73TWW8", O_RDWR);
    if (serialPort == -1) {
        perror("Error opening serial port");
        return 1;
    }

    // Configure the serial port
    struct termios serialConfig;
    tcgetattr(serialPort, &serialConfig);
    cfsetispeed(&serialConfig, B9600);  // Set baud rate to 9600
    cfsetospeed(&serialConfig, B9600);
    serialConfig.c_cflag &= ~PARENB;    // Disable parity bit
    serialConfig.c_cflag &= ~CSTOPB;    // Set stop bit to 1
    serialConfig.c_cflag &= ~CSIZE;     // Clear data size bits
    serialConfig.c_cflag |= CS8;        // Set data size to 8 bits
    tcsetattr(serialPort, TCSANOW, &serialConfig);

    // Send a hexadecimal command
    unsigned char command[] = {0x85}; 
    write(serialPort, command, sizeof(command));


    // // Send a hexadecimal command
    // command[] = {0xE3, 0x40}; 
    // write(serialPort, command, sizeof(command));

    // Close the serial port
    close(serialPort);

}
