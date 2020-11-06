__author__ = 'ABDERRAZZAK'

import serial

class Channel :
    id = 0
    def __init__(self,port,admin):
         Channel.id += 1
         self.id = Channel.id
         self.port=port
         self.client_list=[]
         self.isConnected=False
         self.admin=admin


    def __del__(self):
        Channel.id -= 1
        self.close()

    def close(self):
        for cl in self.client_list:
            self.client_list.remove(cl)
        self.isConnected=False

    def send(self,message):
        for client in self.client_list:
            client.clientsock.send(message)


