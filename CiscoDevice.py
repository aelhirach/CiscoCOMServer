__author__ = 'rzouka'
import sys
import re
from enum import  Enum
import glob
import time
from time import sleep
import serial


class DeviceMode(Enum):
    enable = "enable_mode"
    global_config = "global_configuration_mode"
    sub_config = "sub_configuration_mode"
    non_privileged = "non_privileged_mode"

class CiscoDevice:
    serial = None
    enable_password = None
    connected = False
    _receive_wait = 0

    def __init__(self,enable_password, port, baud_rate=9600):
        try:
            self.serial = serial.Serial(port, baudrate=baud_rate, timeout=None, parity=serial.PARITY_NONE,
                                              bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE, xonxoff=False)
            self.port=port
            self.connected = True
            self.serial.flushInput()
            self.enable_password = enable_password

        except serial.serialutil.SerialException as e:
            print("error")
            connected = False

    def __enter__(self):
        return self

    def _clear_buffers(self):
        self.serial.read(self.serial.inWaiting())
        self.serial.flushInput()
        self.serial.flushOutput()

    def set_receive_wait(self, wait):
        self._receive_wait = wait

###########################  getMode  #########################
    def get_mode(self):
        self._clear_buffers()
        self.serial.write("\r".encode())
        sleep(.2)
        while True:

            current_prompt = self.serial.read(self.serial.inWaiting()).decode()

            if current_prompt != "":
                if current_prompt[-1] == ">" or current_prompt[-1] == "#":
                    break
                else:
                    self._clear_buffers()

                    # Hit return once so that we can see the prompt
                    self.serial.write("\r".encode())
            sleep(.2)

        # First check if we are in non-privileged mode
        if current_prompt[-1] == ">":
            self._clear_buffers()
            return DeviceMode.non_privileged
        elif current_prompt[-1] != ">" and "config" not in current_prompt:
            self._clear_buffers()
            return DeviceMode.enable
        elif re.findall(r'\((.+?)\)', current_prompt)[0] == "config":
            self._clear_buffers()
            return DeviceMode.global_config
        else:
            self._clear_buffers()
            return DeviceMode.sub_config

###########################  SetMode  #########################
    def set_mode(self, desired_mode):
        self._clear_buffers()
        current_mode = self.get_mode()
        if current_mode is DeviceMode.non_privileged:
            if desired_mode is DeviceMode.non_privileged:
                pass
            elif desired_mode is DeviceMode.enable:
                self.serial.write("\r".encode())
                self.serial.write("enable\r".encode())
                sleep(.5)
                self.serial.write((self.enable_password + "\r").encode())
            else:
                self.serial.write("\r".encode())
                self.serial.write("enable\r".encode())

                sleep(.5)
                self.serial.write((self.enable_password + "\r").encode())

                # Wait half a second to send another command
                sleep(.3)
                self.serial.write("configure terminal\r".encode())

        elif current_mode is DeviceMode.enable:

            # If we are already in enable mode pass
            if desired_mode is DeviceMode.enable:
                pass

            # Enter non-privileged mode
            elif desired_mode is DeviceMode.non_privileged:
                self.serial.write("exit\r".encode())
                sleep(.5)

            # Move to global configuration mode
            else:
                self.serial.write("configure terminal\r".encode())

        elif current_mode is DeviceMode.global_config:

            # If we are already in global configuration mode pass
            if desired_mode is DeviceMode.global_config:
                pass

            # Enter non-privileged mode
            elif desired_mode is DeviceMode.non_privileged:
                self.serial.write("exit\r".encode())
                sleep(.3)
                self.serial.write("exit\r".encode())

            # Enter enable mode
            else:
                self.serial.write("exit\r".encode())

        elif current_mode is DeviceMode.sub_config:

            # Move to non-privileged mode
            if desired_mode is DeviceMode.non_privileged:
                self.serial.write("end\r".encode())
                self.serial.write("exit\r".encode())

            # Move to enable mode
            elif desired_mode is DeviceMode.enable:
                self.serial.write("end\r".encode())

            # Move to global configuration mode
            else:
                self.serial.write("exit\r".encode())

        self._clear_buffers()
        return self.get_mode()

###########################  receive Data  #########################
    def _receive_output(self):
        bytes_to_read = -1
        received_data = ""
        while bytes_to_read < self.serial.inWaiting():
            bytes_to_read = self.serial.inWaiting()
            received_data += self.serial.read(bytes_to_read).decode()
            bytes_to_read = 0

            sleep(.1)
            sleep(self._receive_wait)
        if "building configuration" in received_data.lower():
            bytes_to_read = 0
            while self.serial.inWaiting() == 0:
                pass
            while bytes_to_read < self.serial.inWaiting():
                bytes_to_read = self.serial.inWaiting()
                received_data += self.serial.read(bytes_to_read).decode()
                bytes_to_read = 0
                sleep(.1)
        self._clear_buffers()
        return received_data

###########################  Send Command  #########################
    def send_command(self, user_input):
        self._clear_buffers()
        if type(user_input) is str:
            self.serial.write((user_input + "\r").encode())

    def send_char(self, char):
        self._clear_buffers()
        if type(char) is str:
            self.serial.write((char).encode())

###########################  exit #########################
    def __exit__(self, exc_type, exc_value, traceback):
        if self.connected:
            self.set_mode(DeviceMode.enable)
            self.send_command("terminal length 24\r")
            self.serial.close()

        return exc_value

###########################  all serial ports #########################
def serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM' + str(i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this is to exclude your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')

    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')

    else:
        raise EnvironmentError('Unsupported platform')
    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result







