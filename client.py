import socket
import sys
import threading


HEADER = 64
PORT = 6767
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = socket.gethostbyname(socket.gethostname())
ADDRESS = (SERVER, PORT)
NICKNAME = sys.argv[1]


print(NICKNAME)
#Initialise client
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDRESS)

def send():
    while True:
        message = input()
        message = message.encode(FORMAT)
        # Get message length for header
        message_length = len(message)
        send_length = str(message_length).encode(FORMAT)

        #Pad to fit 64 byte header
        send_length += b' ' * (HEADER - len(send_length))
        client.send(send_length)
        client.send(message)

def recieve():
    while True:
        message_length = client.recv(HEADER).decode(FORMAT)
        if message_length:
            message_length = int(message_length)
            message = client.recv(message_length).decode(FORMAT)
            if message == DISCONNECT_MESSAGE:
                connected = False
            print("Server: ", message)
        #print('an error occured (recieve)')

recieve_thread = threading.Thread(target=recieve)
recieve_thread.start()
send_thread = threading.Thread(target=send)
send_thread.start()


