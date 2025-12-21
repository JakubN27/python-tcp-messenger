import socket
import threading
#Using threading since we are handling multiple clients

s = socket.socket()

# Bind port to socket
# Empty string for IP makes server listen for requests from any computer
# localhost would mean we can only listen from this computer
PORT = 6767
SERVER = socket.gethostbyname(socket.gethostname())
HEADER = 64     #64 byte header for each message
ADDRESS = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

client_addresses = {}
client_nicknames = {}
groups = {}

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(ADDRESS)


print('server bound at ', PORT)

#listen() takes size of request queue
s.listen(9)
print('server listening')



#Rund concurrently for each client
def handle_client(connection, address):
    # Set client nickname before entering loop
    nick_message_length = connection.recv(HEADER).decode(FORMAT)
    if nick_message_length:
        nick_message_length = int(nick_message_length)
        nick_message = connection.recv(nick_message_length).decode(FORMAT)
        print(f'{nick_message} has joined the room!')

    #Update dictionaries
    client_addresses[connection] = address
    client_nicknames[connection] = nick_message

    #Send welcome message to client upon connecting
    welcome_message = "thank you for connecting!"
    send(welcome_message, (connection))

    #Listen for messages fro client
    connected = True
    while connected:
        message_length = connection.recv(HEADER).decode(FORMAT)
        if message_length:
            message_length = int(message_length)
            message = connection.recv(message_length).decode(FORMAT)
            if message == DISCONNECT_MESSAGE:
                connected = False
            print(client_nicknames[connection], ": ", message)
    connection.close()
        
def send(message, *targets):
    for target in targets:
        message = message.encode(FORMAT)
        # get message length for header
        message_length = len(message)
        send_length = str(message_length).encode(FORMAT)

        #pad to fit 64 byte header
        send_length += b' ' * (HEADER - len(send_length))
        target.send(send_length)
        target.send(message)

def start():
    while True: 
        #Establish connection with client. 
        connection, address = s.accept()    
        thread = threading.Thread(target = handle_client, args = (connection,address))
        thread.start()
        print("Active connections: ", (threading.activeCount() -1))
        print('Got connection from', address )

        # send a thank you message to the client. encoding to send byte type. 

start()
