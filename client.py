import socket
import sys
import threading


HEADER = 64
PORT = int(sys.argv[3])
HOSTNAME = sys.argv[2]
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
ADDRESS = (HOSTNAME, PORT)
NICKNAME = sys.argv[1]


def send(client):
    while True:
        message = input()
        print('sending message: ', message)
        message = message.encode(FORMAT)
        # Get message length for header
        message_length = len(message)
        send_length = str(message_length).encode(FORMAT)

        #Pad to fit 64 byte header
        send_length += b' ' * (HEADER - len(send_length))
        client.send(send_length)
        client.send(message)

def recieve(client):
    while True:
        message_length = client.recv(HEADER).decode(FORMAT)
        if message_length:
            message_length = int(message_length)
            message = client.recv(message_length).decode(FORMAT)
            if message == DISCONNECT_MESSAGE:
                connected = False
            print(": ", message)
        #print('an error occured (recieve)')

def start():
    #Initialise client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDRESS)

    recieve_thread = threading.Thread(target=recieve, args = (client,))
    recieve_thread.start()
    # Get message length for header
    message = NICKNAME
    message = message.encode(FORMAT)
    message_length = len(message)
    send_length = str(message_length).encode(FORMAT)

    #Pad to fit 64 byte header
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)


    send_thread = threading.Thread(target=send, args = (client,))
    send_thread.start()

start()




