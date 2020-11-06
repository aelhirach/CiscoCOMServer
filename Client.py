__author__ = 'ABDERRAZZAK'


class Client :
    id=0
    def __init__(self,clientsock,addr):
        Client.id += 1
        self.id=Client.id
        self.isAdmin=False
        self.clientsock=clientsock
        self.addr=addr
        self.channel=None

    def __del__(self):
        Client.id -= 1






