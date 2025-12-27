import socket
import threading
import sys
import os
#Using threading since we are handling multiple clients


# Bind port to socket
# Empty string for SERVER makes server listen for requests from any computer
# localhost would mean we can only listen from this computer
PORT = int(sys.argv[1])
SERVER = ''
HEADER = 64     #64 byte header for each message
ADDRESS = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

#Client : address
client_addresses = {}
#Client : nickname
client_nicknames = {}
# nickanme : client
nick_to_client = {}
#groupname : [client1, clien2, ...]
groups = {}
#Client : messaging mode
client_modes = {}


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
    nick_to_client[nick_message] = connection

    #Send welcome message to client upon connecting
    welcome_message = "SERVER: thank you for connecting!"
    send(welcome_message, (connection))

    #Default mode is broadcast
    client_modes[connection] = 'broadcast'

    #Listen for messages fro client
    connected = True
    while connected:
        nick = client_nicknames[connection]
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
                #Server resends client message to target depending on mode
                if client_modes[connection] == 'broadcast':
                    print(client_addresses.values())
                    targets = [c for c in client_addresses if c != connection]
                    send(f'{nick}: {message}', *targets)
                elif client_modes[connection][0] == 'group':
                    group_name = client_modes[connection][1]
                    targets = [c for c in groups[group_name] if c != connection]
                    send(f'{nick}: {message}', *targets)
                elif client_modes[connection][0] == 'whisper':
                    target_client = nick_to_client[client_modes[connection][1]]
                    if target_client != connection:
                        send(f'{nick}: {message}', (target_client))


                print(nick, ": ", message, client_modes[connection])
        #If forced diconnect, we will recieve empty length
        else:
            del nick_to_client[nick]
            del client_nicknames[connection]

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
        send('SERVER: You have been disconnected.', (connection))
        return -1
    #Expecting !joingroup <group>
    elif command == '!joingroup':
        if args and len(args) != 1:
            send(f'SERVER: Wrong number of arguments for {command}, expecting 1', (connection))
        else:
            try:
                if args[0] in groups:
                    groups[args[0]].append(connection)
                else:
                    groups[args[0]] = [connection]
                send(f'SERVER: You have joined the group {args[0]}', (connection))
            except:
                send('SERVER: Failed to join group: ' + args[0], (connection))
        print(groups)
    #Expecting !leavegroup <group>
    elif command == '!leavegroup':
        if args and len(args) != 1:
            send(f'SERVER: Wrong number of arguments for {command}, expecting 1', (connection))
        else:
            if args[0] in groups:
                groups[args[0]].remove(connection)
                # cleanup if group is empty
                if not groups[args[0]]:
                    del groups[args[0]]
                send(f'SERVER: You have left the group {args[0]}', (connection))
            else:
                send(f'SERVER: You are not part of the group {args[0]}', (connection))
        print(groups)
    #Expecting !switchmode <mode>
    elif command == '!switchmode':
        # Expecting !switchmode broadcast
        if args and len(args) == 1 and args[0] == 'broadcast':
            client_modes[connection] = 'broadcast'
        # Expecting !switchmode group <groupname>
        elif args and len(args) == 2 and args[0] == 'group':
            group_name = args[1]
            if group_name not in groups:
                send(f'Group {group_name} does not exist!', (connection))
            elif connection not in groups[group_name]:
                send(f'You are not part of the group {group_name}', (connection))
            else:
                client_modes[connection] = ('group', group_name)
        # Expecting !switchmode whisper <user>
        elif args and len(args) == 2 and args[0] == 'whisper':
            target_user = args[1]
            if target_user not in nick_to_client:
                send(f'User {target_user} does not exist!', (connection))
            else:
                client_modes[connection] = ('whisper', target_user)
        else:
            send(f'SERVER: Wrong usage of {command}', (connection))
    elif command == '!sharedfiles':
        shared_folder = os.environ.get('SERVER_SHARED_FILES', 'SharedFiles')
        try:
            files = os.listdir(shared_folder)
            file_count = len(files)
            if file_count == 0:
                send('SERVER: Access granted. No files available in the shared folder.', (connection))
            else:
                send(f'SERVER: Access granted. {file_count} files in folder.', (connection))
                send('SERVER: Files: ' + ', '.join(files), (connection))
        except Exception as e:
            send('SERVER: Failed to access shared folder.', (connection))
    elif command == '!download':
        shared_folder = os.environ.get('SERVER_SHARED_FILES', 'SharedFiles')
        if not args or len(args) != 2:
            send('SERVER: Usage: !download <filename> <tcp|udp>', (connection))
        else:
            filename = args[0]
            protocol = args[1].lower()
            filepath = os.path.join(shared_folder, filename)
            if not os.path.isfile(filepath):
                send('SERVER: File not found.', (connection))
            elif protocol == 'tcp':
                try:
                    filesize = os.path.getsize(filepath)
                    send(f'SERVER: Sending {filename} ({filesize} bytes).', (connection))
                    # Send 64-byte header with file size before file data
                    file_size_header = str(filesize).encode(FORMAT)
                    file_size_header += b' ' * (HEADER - len(file_size_header))
                    connection.send(file_size_header)
                    with open(filepath, 'rb') as f:
                        # Send file data in chunks
                        bytes_sent = 0
                        while True:
                            data = f.read(1024)
                            if not data:
                                break
                            connection.send(data)
                            bytes_sent += len(data)
                    send(f'SERVER: File transfer complete for {filename} ({filesize} bytes) via TCP.', (connection))
                except Exception as e:
                    send('SERVER: Error sending file.', (connection))
            elif protocol == 'udp':
                try:
                    filesize = os.path.getsize(filepath)
                    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    udp_sock.bind(('', 0)) # Bind to any free port
                    udp_port = udp_sock.getsockname()[1]
                    send(f'SERVER: UDPPORT {udp_port} {filename} {filesize}', (connection))
                    udp_sock.settimeout(5)
                    try:
                        # Wait for client to signal readiness; use that address for replies
                        _, client_addr = udp_sock.recvfrom(1024)
                    except socket.timeout:
                        send('SERVER: UDP download timed out waiting for client.', (connection))
                        udp_sock.close()
                        return
                    with open(filepath, 'rb') as f:
                        bytes_sent = 0
                        while True:
                            data = f.read(1024)
                            if not data:
                                break
                            udp_sock.sendto(data, client_addr)
                            bytes_sent += len(data)
                    udp_sock.close()
                    send(f'SERVER: File transfer complete for {filename} ({filesize} bytes) via UDP.', (connection))
                except Exception as e:
                    send('SERVER: Error sending file via UDP.', (connection))
            else:
                send('SERVER: Invalid protocol. Use tcp or udp.', (connection))
    else:
        send("SERVER: invalid command", (connection))
            
def send(message, *targets):
    message = message.encode(FORMAT)
    # get message length for header
    message_length = len(message)
    send_length = str(message_length).encode(FORMAT)
    for target in targets:
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
