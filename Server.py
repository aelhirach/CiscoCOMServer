__author__ = 'ABDERRAZZAK'

import sys, serial,glob, time

# Server admin

class Server :
    def __init__(self,name, host,tcp_port):
         self.channel_list = []
         self.devices={}
         self.name=name
         self.endpoint=(host,tcp_port)
         self.host=host
         self.tcp_port=tcp_port
         self.serial_ports()
         if sys.platform.startswith('win'): self.os="windows"
         elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin') or sys.platform.startswith('darwin'):
                                self.os= "linux"

    def serial_ports(self):
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
          i=0
          self.devices.clear()
          for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
                self.devices[port]="Router"+str(i)
                i=i+1
            except (OSError, serial.SerialException):
                 pass
          return result



