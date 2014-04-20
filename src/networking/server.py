import socket
import threading
import struct
import string

class clientThread(threading.Thread):
    def __init__(self, serv):
        threading.Thread.__init__(self)
        self.server = serv
        self.clientList = []
        self.running = True
        print("Client thread created. . .")
    def run(self):
        print("Beginning client thread loop. . .")
        while self.running:
            #Need to skip client if buffer is empty or timeout below (recv?)
            #Maybe need to redo for use of poll() or select instead
            #http://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method
            
            for client in self.clientList:
                client.sock.settimeout(1);
                try:
                    message = client.sock.recv(self.server.BUFFSIZE)
                    if message != None and message != "":
                        #Message should not be printed here for long term, for now it's useful for testing.
                        print message
                        for node in self.clientList:
                        	if node != client:
                        		node.update(str(client.address) + ": " + message)
                        # client.update(message)
                except socket.timeout:
                    print "Socket Timeout for " + str(client)
    

class clientObject(object):
    def __init__(self,clientInfo):
        self.sock = clientInfo[0]
        self.address = clientInfo[1]
    def update(self,message):
        self.sock.send(message)

class Server(object):
    def __init__(self):
        self.HOST = '0.0.0.0'
        self.PORT = 8889
        self.BUFFSIZE = 1024
        print("Starting server at " + self.HOST + ":" + str(self.PORT))
        self.ADDRESS = (self.HOST,self.PORT)
        self.clientList = []
        self.running = True
        self.serverSock = socket.socket()
        self.serverSock.bind(self.ADDRESS)
        self.serverSock.listen(2)
        self.clientThread = clientThread(self)
        self.clientThread.start()
        print("Waiting for connection..")
        while self.running:
            clientInfo = self.serverSock.accept()
            print("Client connected from {}.".format(clientInfo[1]))
            self.clientThread.clientList.append(clientObject(clientInfo))
        
        self.serverSock.close()
        print("- end -")

#Just use as a library for now, this is here for testing
if __name__ == "__main__":
    serv = Server()

