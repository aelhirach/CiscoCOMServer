__author__ = 'ABDERRAZZAK'
from Server import *
from Labo import *
from Channel import *
from Client import *
from CiscoDevice import *
from socket import *
import thread
unused_caracters=('\x1b[1~','\x1b[3~','\x1b[4~','\x1b[5~','\x1b[6~','\x1b[11~','\x1b[12~','\x1b[13~','\x1b[14~','\x1b[15~'
        ,'\x1b[17~','\x1b[18~','\x1b[19~','\x1b[20~','\x1b[21~','\x1b[23~','\x1b[24~','\x1b[D','\x1b[C','\x1b[A', '\x1b[B','\x7f')
def handler(clientsock,addr):
    clientsock.send("Your address is :"+ str(addr)+"\n\r")
    while 1:
        client=Client(clientsock,addr)
        channel=None
        result_channel=None
        result_cnx=check_cnx(client)
        client.clientsock.send("\n\r########### Welcome to IRISIB COMSERVER  ###########\n\r")
        if (result_cnx==-1):##error
            break
        ####admin
        elif (result_cnx==15):
             client.isAdmin=True
             client.clientsock.send("\n\r###### You are connecting as a privileged user ######\n\r")
             display_ports(client)
             result_port=choose_port(client)
             if (result_port==-1):
                      break
             channel=Channel(result_port,client)
             client.clientsock.send(str(result_port)+" has been successfully connected to channel-"+str(channel.id)+"\n\r")
             client.clientsock.send("Write 'close' to quit \n\r")
             channel.isConnected=True
             ## subscirbe client
             channel.client_list.append(client)
             comserver.channel_list.append(channel)
             result_conf=configure_port(channel,client)
             if (result_conf==-2):
                 comserver.channel_list.remove(channel)
                 channel.close()
                 del channel
             if (result_conf==-1):
                      break

        #### user
        elif  (result_cnx==1):
             if not comserver.channel_list:
                client.clientsock.send("\n\r###### You are connecting as a simple user ######\n\r")
                client.clientsock.send("The are no connected channels please contact server administrator\n\r")
                break
             client.isAdmin=False
             result_channel=choose_channel(client)
             if (result_channel==-1):
                     break
             result_channel.client_list.append(client)
             result_show_channel=show_channel(result_channel,client)
             if (result_show_channel==-2):   # channel closed
                    result_channel.client_list.remove(client)
                    del client
                    print("channel closed or client disconnected")
                    continue
             elif (result_show_channel==-1): # socket closed by user
                    break
    if client.isAdmin :
        if channel:
            comserver.channel_list.remove(channel)
            channel.close()
            del channel

        client.clientsock.close()
        print (addr, "- admin closed connection") #log on console
        del client
    else :
        if result_channel :
            result_channel.client_list.remove(client)
        clientsock.close()
        print (addr, "- user closed connection") #log on console
        del client
def check_cnx(client):
    quit=False
    isConnected=False
    while isConnected==False:
        client.clientsock.send("Username:")
        user=''
        while ('\r' in user)==False:
            buff = client.clientsock.recv(BUFF)
            if  not buff :
                quit=True
                break
            elif (buff not in unused_caracters):
                    user=user+buff
                    client.clientsock.send(buff)
            elif ((buff=='\x7f' and len(user)>0)):
                 user=user[:-1]
                 client.clientsock.send(buff)
        if quit:
            return -1
            break
        user=user.strip("\r")
        client.clientsock.send("\n\rPASSWORD:")
        password=''
        while ('\r' in password)==False:
            buff = client.clientsock.recv(BUFF)
            if  not buff :
                 quit=True
                 break
            elif (buff not in unused_caracters):
                    password=password+buff
            elif ((buff=='\x7f' and len(password)>0)):
                 password=password[:-1]
        if quit:
            return -1
            break
        password=password.strip("\r")

        if (user=="admin" and password=="admin"):
                isConnected=True
                return 15
        if (user=="user" and password=="user"):
                isConnected=True
                return 1
        else :
             client.clientsock.send("\n\rWrong username or password  \n\r")
def configure_port(channel,client):
     with CiscoDevice("COMSERVER",channel.port) as device:

           if device.connected:
                     #display_connected_devices()
                     #device.set_mode(DeviceMode.enable)
                     #print(device.get_mode())
                     #client.clientsock.send(device.get_mode())
                     start_time = time.time()
                     elapsed_time = 0
                     data=None
                     while not data :
                        device.send_char("\r")
                        data=(device._receive_output())
                        elapsed_time = time.time() - start_time
                        if elapsed_time>5 :
                            client.clientsock.send("No data received : Make sure that this device is connected \n\r")
                            device.connected=False
                            return -2
                     command=''
                     while 1:
                         drdata=(device._receive_output())
                         print(drdata.decode())
                         channel.send(drdata)
                         prdata = client.clientsock.recv(BUFF)
                         if prdata == '\xc3\xa9': prdata ='i'
                         elif prdata =='\xc2\xa7' : prdata="'"
                         elif prdata == '\xc3\xa8': prdata='h'
                         elif prdata == '\xc3\xa7': prdata='g'
                         elif prdata == '\xc3\xa0': prdata='`'
                         elif prdata == '\xc2\xb2': prdata='2'
                         if not prdata :
                                device.connected=False
                                return -1
                         elif (prdata!='\x7f'):
                              command=command+prdata
                         elif ((prdata=='\x7f' and len(command)>0)):
                                 command=command[:-1]

                         if ('\r' in command):
                              command=command.strip('\r')
                              print(command)
                              if (command =="close") :
                                  client.clientsock.send("\n\r")
                                  device.connected=False
                                  return -2
                              else : command=""

                         device.send_char(prdata)

           else:
                     client.clientsock.send("Unable to connect to the device.")
def show_channel(channel,client):
   quit=False
   while 1 :
                 command=''
                 while ('\r' in command)==False:
                     buff = client.clientsock.recv(BUFF)
                     if  not buff :
                         quit=True
                         break
                     elif (buff not in unused_caracters):
                         command=command+buff
                         client.clientsock.send(buff)
                     elif ((buff=='\x7f' and len(command)>0)):
                         command=command[:-1]
                         client.clientsock.send(buff)
                 if quit:
                     return -1
                     break
                 if  not channel.isConnected :
                     client.clientsock.send("\n\rthe channel has been closed by admin\n\r")
                     return -2
                     break
                 if (command.strip('\r') =="close") :
                        client.clientsock.send("\n\r")
                        return -2
                        break
                 else :
                        command=""
                        client.clientsock.send("\n\runknown command\n\r")

def choose_port(client):
    quit=False
    portFound=False
    if client.isAdmin :
        if not comserver.devices:
            return -1
        else:
            while (portFound==False):
                 client.clientsock.send("Enter an available serial port :")
                 port=''
                 while ('\r' in port)==False:
                     buff = client.clientsock.recv(BUFF)
                     if  not buff :
                         quit=True
                         break
                     elif (buff not in unused_caracters):
                         port=port+buff
                         client.clientsock.send(buff)
                     elif ((buff=='\x7f' and len(port)>0)):
                         port=port[:-1]
                         client.clientsock.send(buff)
                 if quit:
                     return -1
                     break
                 port=port.strip("\r")
                 print(port)
                 portBusy=False
                 if port in comserver.devices:
                         for i in range (len(comserver.channel_list)):
                            if (port==comserver.channel_list[i].port):
                                client.clientsock.send("\n\r This device is connecting in config-mode by"+str(addr)+"\n\r")
                                portBusy=True
                                break
                         if not portBusy :
                                portFound=True
                                client.clientsock.send("\n\r")
                                return port
                                break
                 else :
                            client.clientsock.send("\n\rport not found\n\r")
def display_channels(client):
        for ch in comserver.channel_list:
            client.clientsock.send("Channel-"+str(ch.id) + " is connecting in config-mode by "+str(ch.admin.addr)+" .\n\r")
def display_ports(client):
      if comserver.devices:
        client.clientsock.send("Connected serial ports : ")
        for port in comserver.devices:
            portBusy=False
            for i in range (len(comserver.channel_list)):
              if (port==comserver.channel_list[i].port):
                client.clientsock.send(port+":Busy\n\r")
                portBusy=True
                break
            if not portBusy :
                    client.clientsock.send(port+":Free\n\r")
      else:
          client.clientsock.send("The are no available ports\n\r")
def choose_channel(client):
        if not comserver.channel_list:
            return -1
        display_channels(client)
        channelFound=False
        quit=False

        while (channelFound==False):
                 client.clientsock.send("Enter a connected channel:")
                 channel=''
                 while ('\r' in channel)==False:
                     buff = client.clientsock.recv(BUFF)
                     if  not buff :
                         quit=True
                         break
                     elif (buff not in unused_caracters):
                         channel=channel+buff
                         client.clientsock.send(buff)
                     elif ((buff=='\x7f' and len(channel)>0)):
                         channel=channel[:-1]
                         client.clientsock.send(buff)
                 if quit:
                     return -1
                     break
                 channel=channel.strip("\r")
                 for i in range (len(comserver.channel_list)):
                      id_ch=str(comserver.channel_list[i].id)
                      if (channel==id_ch):
                        client.clientsock.send("\n\r You are connecting to channel-"+channel+" in display-mode"+"\n\r")
                        client.clientsock.send("Write 'close' to quit \n\r")
                        channelFound=True
                        return comserver.channel_list[i]
                        break
                      if(i==len(comserver.channel_list)-1): client.clientsock.send("\n\r Channel not found \n\r")
if __name__ == '__main__':
    HOST = '127.0.0.1'# must be input parameter @TODO
    PORT = 8881 # must be input parameter @TODO
    BUFF = 1024
    comserver = Server("comserver",HOST,PORT)
    irisb=Labo("IRISIB")
    irisb.server_list.append(comserver)
    serversock = socket(AF_INET, SOCK_STREAM)
    serversock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serversock.bind(comserver.endpoint)
    serversock.listen(5)
    while 1 :
          print ('waiting for connection... listening on port', PORT)
          clientsock, addr = serversock.accept()
          print ('...connected from:', addr)
          thread.start_new_thread(handler, (clientsock, addr))

