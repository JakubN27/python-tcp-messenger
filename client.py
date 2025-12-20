import socket


HEADER = 64
PORT = 6767
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = socket.gethostbyname(socket.gethostname())
ADDRESS = (SERVER, PORT)

#Initialise client
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDRESS)

def send(message):
    message = message.encode(FORMAT)
    # Get message length for header
    message_length = len(message)
    send_length = str(message_length).encode(FORMAT)

    #Pad to fit 64 byte header
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)

send('hello world')
send('HELLO WORLD')
send(DISCONNECT_MESSAGE)
