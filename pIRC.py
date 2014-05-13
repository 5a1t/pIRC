# pIRC - Context sensitive distributed chat.
# Authors: Rostislav Tsiomenko, Alexander Morrow
# Date: 5/5/14
#
# Proof of concept chat application for context sensitive ordering using hash chains.
# The application supports sending messages between any peers that have the application running using our
# context aware implementation.
#
# P2P base code adopted from Siddhartha Sahu (http://siddharthasahu.in)


from Tkinter import *
from ttk import *
import socket
import thread
import hashlib
import time


class ChatClient(Frame):
  
  def __init__(self, root):
    Frame.__init__(self, root)
    self.root = root
    self.initUI()
    self.serverSoc = None
    self.serverStatus = 0
    self.buffsize = 1024
    self.allClients = {}
    self.counter = 0
    
    self.display_list = []
    self.store_list = dict()
    self.client_list = []
    self.lasthash = 0
    self.lastmessage = ""
    
  
  def initUI(self):
    self.root.title("Simple P2P Chat Client")
    ScreenSizeX = self.root.winfo_screenwidth()
    ScreenSizeY = self.root.winfo_screenheight()
    self.FrameSizeX  = 800
    self.FrameSizeY  = 650
    FramePosX   = (ScreenSizeX - self.FrameSizeX)/2
    FramePosY   = (ScreenSizeY - self.FrameSizeY)/2
    self.root.geometry("%sx%s+%s+%s" % (self.FrameSizeX,self.FrameSizeY,FramePosX,FramePosY))
    self.root.resizable(width=False, height=False)
    
    padX = 10
    padY = 10
    parentFrame = Frame(self.root)
    parentFrame.grid(padx=padX, pady=padY, stick=E+W+N+S)
    
    ipGroup = Frame(parentFrame)
    serverLabel = Label(ipGroup, text="Set: ")
    self.nameVar = StringVar()
    self.nameVar.set("My server")
    nameField = Entry(ipGroup, width=10, textvariable=self.nameVar)
    self.serverIPVar = StringVar()
    self.serverIPVar.set(socket.gethostbyname(socket.gethostname()))
    serverIPField = Entry(ipGroup, width=15, textvariable=self.serverIPVar)
    self.serverPortVar = StringVar()
    self.serverPortVar.set("10000")
    serverPortField = Entry(ipGroup, width=5, textvariable=self.serverPortVar)
    serverSetButton = Button(ipGroup, text="Set", width=10, command=self.handleSetServer)
    addClientLabel = Label(ipGroup, text="Add friend: ")
    self.clientIPVar = StringVar()
    self.clientIPVar.set(socket.gethostbyname(socket.gethostname()))
    clientIPField = Entry(ipGroup, width=15, textvariable=self.clientIPVar)
    self.clientPortVar = StringVar()
    self.clientPortVar.set("10000")
    clientPortField = Entry(ipGroup, width=5, textvariable=self.clientPortVar)
    clientSetButton = Button(ipGroup, text="Add", width=10, command=self.handleAddClientWrapper)
    serverLabel.grid(row=0, column=0)
    nameField.grid(row=0, column=1)
    serverIPField.grid(row=0, column=2)
    serverPortField.grid(row=0, column=3)
    serverSetButton.grid(row=0, column=4, padx=5)
    addClientLabel.grid(row=0, column=5)
    clientIPField.grid(row=0, column=6)
    clientPortField.grid(row=0, column=7)
    clientSetButton.grid(row=0, column=8, padx=5)
    
    readChatGroup = Frame(parentFrame)
    self.receivedChats = Text(readChatGroup, bg="white", width=60, height=30, state=DISABLED)
    self.friends = Listbox(readChatGroup, bg="white", width=30, height=30)
    self.receivedChats.grid(row=0, column=0, sticky=W+N+S, padx = (0,10))
    self.friends.grid(row=0, column=1, sticky=E+N+S)

    writeChatGroup = Frame(parentFrame)
    self.chatVar = StringVar()
    self.chatField = Entry(writeChatGroup, width=80, textvariable=self.chatVar)
    sendChatButton = Button(writeChatGroup, text="Send", width=10, command=self.handleSendChat)
    self.chatField.grid(row=0, column=0, sticky=W)
    sendChatButton.grid(row=0, column=1, padx=5)

    self.statusLabel = Label(parentFrame)
    
    ipGroup.grid(row=0, column=0)
    readChatGroup.grid(row=1, column=0)
    writeChatGroup.grid(row=2, column=0, pady=10)
    self.statusLabel.grid(row=3, column=0)
 
  def handleSetServer(self):
    if self.serverSoc != None:
        self.serverSoc.close()
        self.serverSoc = None
        self.serverStatus = 0
    serveraddr = (self.serverIPVar.get().replace(' ',''), int(self.serverPortVar.get().replace(' ','')))
    try:
        self.serverSoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSoc.bind(serveraddr)
        self.serverSoc.listen(5)
        self.setStatus("Server listening on %s:%s" % serveraddr)
        self.client_list.append(self.serverIPVar.get().replace(' ',''))
        thread.start_new_thread(self.listenClients,())
        thread.start_new_thread(self.checkWaiting,())
        self.serverStatus = 1
        self.name = self.nameVar.get().replace(' ','')
        if self.name == '':
            self.name = "%s:%s" % serveraddr
    except:
        self.setStatus("Error setting up server")
    
  def listenClients(self):
    while 1:
      clientsoc, clientaddr = self.serverSoc.accept()
      self.setStatus("Client connected from %s:%s" % clientaddr)
      self.addClient(clientsoc, clientaddr)
      thread.start_new_thread(self.handleClientMessages, (clientsoc, clientaddr))
    self.serverSoc.close()

  def handleAddClientWrapper(self):
    self.handleAddClient(self.clientIPVar.get().replace(' ',''),int(self.clientPortVar.get().replace(' ','')))
    


  def storeMessage(self, hash, message):
      if hash in self.store_list:
          self.store_list[hash].append(message)
      else:
          self.store_list[hash] = list();
          self.store_list[hash].append(message);



    
  def handleAddClient(self, ip, port):
    if self.serverStatus == 0:
      self.setStatus("Set server address first")
      return
    clientaddr = (ip,port)
    if ip not in self.client_list:
          try:
              self.client_list.append(ip)
              clientsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
              clientsoc.connect(clientaddr)
              self.setStatus("Connected to client on %s:%s" % clientaddr)
              self.addClient(clientsoc, clientaddr)
              thread.start_new_thread(self.handleClientMessages, (clientsoc, clientaddr))
          except:
              self.setStatus("Error connecting to client")

  def handleClientMessages(self, clientsoc, clientaddr):
    while 1:
      try:
        data = clientsoc.recv(self.buffsize)
        if not data:
            break
        if (data[0] == '@'):
                index = data.find('|')
                ip = data[1:index]
                port = data[index+1:len(data)]
                print "addip:" + ip
                print "addport:" + port
                self.handleAddClient(ip,port)
        else:
                index = data.find('|')
                hash = data[0:index]
                message = data[index+1:len(data)]
                self.storeMessage(hash, message);
                print "added "+ hash + " " + message;
      #self.addChat("%s:%s" % clientaddr, data)
      except:
          break
    self.removeClient(clientsoc, clientaddr)
    clientsoc.close()
    self.setStatus("Client disconnected from %s:%s" % clientaddr)


  #Checks waiting list for hashes 
  def checkWaiting(self):
      while 1:
          self.checkLastHashDict(self.lasthash);
                  
 #recursively check message queue.                  
  def checkLastHashDict(self, hash):
       hash = str(hash)
       if hash in self.store_list:
           print "hash in store list"
           for i in self.store_list[hash]:
               print "trying to print:" + i 
               self.addChat("Message", i)
               self.lastmessage = i;
               self.lasthash = hashlib.sha256(str(self.lasthash) + i).hexdigest()
               self.checkLastHashDict(hashlib.sha256(i).hexdigest())
               self.store_list[hash].remove(i);
           del self.store_list[hash]
     
  
  #Send messages to connected peers.
  def handleSendChat(self):
    if self.serverStatus == 0:
      self.setStatus("Set server address first")
      return
    msg = self.chatVar.get().replace(' ','')
    if msg == '':
        return
    #self.addChat("me", msg)
    for client in self.allClients.keys():
      client.send(str(self.lasthash) + "|" + msg)
    self.store_list[self.lasthash].append(msg);

  def addChat(self, client, msg):
    self.receivedChats.config(state=NORMAL)
    self.receivedChats.insert("end",client+": "+msg+"\n")
    self.receivedChats.config(state=DISABLED)
  
  def addClient(self, clientsoc, clientaddr):
    self.allClients[clientsoc]=self.counter
    self.counter += 1
    self.friends.insert(self.counter,"%s:%s" % clientaddr)
  
  def removeClient(self, clientsoc, clientaddr):
      print self.allClients
      self.friends.delete(self.allClients[clientsoc])
      del self.allClients[clientsoc]
      print self.allClients
  
  def setStatus(self, msg):
    self.statusLabel.config(text=msg)
    print msg


    # Test function to determine convergence for node in network.
    def testNetwork(self, msg_count):
        start = time.time()
        for x in range(0, msg_count):
            for client in self.allClients.keys():
                client.send(str(self.lasthash) + "|" + x)
            self.store_list[self.lasthash].append(x);
            while(self.lastmessage != msg_count):
              end = time.time()
        print "Elapsed test time for self node convergence:" + str(end - start)

def main():
  root = Tk()
  app = ChatClient(root)
  root.mainloop()  

if __name__ == '__main__':
  main()  