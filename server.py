import socket
import threading
import sys
#Using threading since we are handling multiple clients


# Bind port to socket
# Empty string for IP makes server listen for requests from any computer
# localhost would mean we can only listen from this computer
PORT = int(sys.argv[1])
SERVER = ''
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
            if message.startswith('!'):
                code = commands(connection, message)
                #If disconnect flag raised
                if code == -1:
                    connected = False
            else:
                print(client_nicknames[connection], ": ", message)
        #If forced diconnect, we will recieve empty length
        else:
            connected = False
            print(f'{client_nicknames[connection]} has disconnected unexpectedly.')

    connection.close()

def commands(connection, message):
    message_list = message.split()
    command = message_list[0]
    if len(message_list) > 1:
        args = message_list[1:]
    #If user chooses to disconenct we return a flag
    if command == '!disconnect':
        print(f'{client_nicknames[connection]} has disconnected.')
        return -1
    #Expecting !joingroup <group>
    elif command == '!joingroup':
        if args and len(args) != 1:
            send(f'Wrong number of arguments for {command}, expecting 1', (connection))
        else:
            try:
                if args[0] in groups:
                    groups[args[0]].append(connection)
                else:
                    groups[args[0]] = [connection]
                send(f'You have joined the group {args[0]}', (connection))
            except:
                send('Failed to join group: ', args[0])
        print(groups)
    #Expecting !leavegroup <group>
    elif command == '!leavegroup':
        if args and len(args) != 1:
            send(f'Wrong number of arguments for {command}, expecting 1', (connection))
        else:
            if args[0] in groups:
                groups[args[0]].remove(connection)
                send(f'You have left the group {args[0]}', (connection))
            else:
                send(f'You are not part of the group {args[0]}', (connection))
        print(groups)

    elif command == '!switchmode':
        pass
    else:
        send("invalid command", (connection))
        
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
