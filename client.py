import socket
import threading

s = socket.socket()
print('created socket')

PORT = 6767

#Bind port to socket
SERVER = socket.gethostbyname(socket.gethostname())
print(SERVER)
print(socket.gethostname())
