// Uses POSIX serial port functions to send and receive data from a Tic.
// NOTE: The Tic's control mode must be "Serial / I2C / USB".
// NOTE: You will need to change the 'const char * device' line below to
//   specify the correct serial port.
 
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>
#include <stdint.h>
#include <termios.h>
 
// Opens the specified serial port, sets it up for binary communication,
// configures its read timeouts, and sets its baud rate.
// Returns a non-negative file descriptor on success, or -1 on failure.
int open_serial_port(const char * device, uint32_t baud_rate)
{
  int fd = open(device, O_RDWR | O_NOCTTY);
  if (fd == -1)
  {
    perror(device);
    return -1;
  }
 
  // Flush away any bytes previously read or written.
  int result = tcflush(fd, TCIOFLUSH);
  if (result)
  {
    perror("tcflush failed");  // just a warning, not a fatal error
  }
 
  // Get the current configuration of the serial port.
  struct termios options;
  result = tcgetattr(fd, &options);
  if (result)
  {
    perror("tcgetattr failed");
    close(fd);
    return -1;
  }
 
  // Turn off any options that might interfere with our ability to send and
  // receive raw binary bytes.
  options.c_iflag &= ~(INLCR | IGNCR | ICRNL | IXON | IXOFF);
  options.c_oflag &= ~(ONLCR | OCRNL);
  options.c_lflag &= ~(ECHO | ECHONL | ICANON | ISIG | IEXTEN);
 
  // Set up timeouts: Calls to read() will return as soon as there is
  // at least one byte available or when 100 ms has passed.
  options.c_cc[VTIME] = 1;
  options.c_cc[VMIN] = 0;
 
  // This code only supports certain standard baud rates. Supporting
  // non-standard baud rates should be possible but takes more work.
  switch (baud_rate)
  {
  case 4800:   cfsetospeed(&options, B4800);   break;
  case 9600:   cfsetospeed(&options, B9600);   break;
  case 19200:  cfsetospeed(&options, B19200);  break;
  case 38400:  cfsetospeed(&options, B38400);  break;
  case 115200: cfsetospeed(&options, B115200); break;
  default:
    fprintf(stderr, "warning: baud rate %u is not supported, using 9600.\n",
      baud_rate);
    cfsetospeed(&options, B9600);
    break;
  }
  cfsetispeed(&options, cfgetospeed(&options));
 
  result = tcsetattr(fd, TCSANOW, &options);
  if (result)
  {
    perror("tcsetattr failed");
    close(fd);
    return -1;
  }
 
  return fd;
}
 
// Writes bytes to the serial port, returning 0 on success and -1 on failure.
int write_port(int fd, uint8_t * buffer, size_t size)
{
  ssize_t result = write(fd, buffer, size);
  if (result != (ssize_t)size)
  {
    perror("failed to write to port");
    return -1;
  }
  return 0;
}
 
// Reads bytes from the serial port.
// Returns after all the desired bytes have been read, or if there is a
// timeout or other error.
// Returns the number of bytes successfully read into the buffer, or -1 if
// there was an error reading.
ssize_t read_port(int fd, uint8_t * buffer, size_t size)
{
  size_t received = 0;
  while (received < size)
  {
    ssize_t r = read(fd, buffer + received, size - received);
    if (r < 0)
    {
      perror("failed to read from port");
      return -1;
    }
    if (r == 0)
    {
      // Timeout
      break;
    }
    received += r;
  }
  return received;
}
 
// Sends the "Exit safe start" command.
// Returns 0 on success and -1 on failure.
int tic_exit_safe_start(int fd)
{
  uint8_t command[] = { 0x83 };
  return write_port(fd, command, sizeof(command));
}
 
// Sets the target position, returning 0 on success and -1 on failure.
//
// For more information about what this command does, see the
// "Set target position" command in the "Command reference" section of the
// Tic user's guide.
int tic_set_target_position(int fd, int32_t target)
{
  uint32_t value = target;
  uint8_t command[6];
  command[0] = 0xE0;
  command[1] = ((value >>  7) & 1) |
               ((value >> 14) & 2) |
               ((value >> 21) & 4) |
               ((value >> 28) & 8);
  command[2] = value >> 0 & 0x7F;
  command[3] = value >> 8 & 0x7F;
  command[4] = value >> 16 & 0x7F;
  command[5] = value >> 24 & 0x7F;
  return write_port(fd, command, sizeof(command));
}
 
// Gets one or more variables from the Tic.
// Returns 0 for success, -1 for failure.
int tic_get_variable(int fd, uint8_t offset, uint8_t * buffer, uint8_t length)
{
  uint8_t command[] = { 0xA1, offset, length };
  int result = write_port(fd, command, sizeof(command));
  if (result) { return -1; }
  ssize_t received = read_port(fd, buffer, length);
  if (received < 0) { return -1; }
  if (received != length)
  {
    fprintf(stderr, "read timeout: expected %u bytes, got %zu\n",
      length, received);
    return -1;
  }
  return 0;
}
 
// Gets the "Current position" variable from the Tic.
// Returns 0 for success, -1 for failure.
int tic_get_current_position(int fd, int32_t * output)
{
  *output = 0;
  uint8_t buffer[4];
  int result = tic_get_variable(fd, 0x22, buffer, sizeof(buffer));
  if (result) { return -1; }
  *output = buffer[0] + ((uint32_t)buffer[1] << 8) +
    ((uint32_t)buffer[2] << 16) + ((uint32_t)buffer[3] << 24);
  return 0;
}
 
int main()
{
  // Choose the serial port name.
  const char * device = "/dev/tty.usbserial-FT73TWW8";
 
  // Choose the baud rate (bits per second).  This must match the baud rate in
  // the Tic's serial settings.
  uint32_t baud_rate = 9600;
 
  int fd = open_serial_port(device, baud_rate);
  if (fd < 0) { return 1; }
 
  int result;
 
  int32_t position;
  result = tic_get_current_position(fd, &position);
  if (result) { return 1; }
  printf("Current position is %d.\n", position);
 
  int32_t new_target = position > 0 ? -200 : 200;
  printf("Setting target position to %d.\n", new_target);
  result = tic_exit_safe_start(fd);
  if (result) { return 1; }
  result = tic_set_target_position(fd, new_target);
  if (result) { return 1; }
 
  close(fd);
  return 0;
}