import socket
import threading
import sys
import os

if len(sys.argv) != 2:
    print("Usage: python server.py <port>")
    sys.exit(1)
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
# nickname : client
nick_to_client = {}
#groupname : [client1, client2, ...]
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



#Run concurrently for each client
def handle_client(connection, address):
    nick_message = ''
    announce_disconnect = True
    # Set client nickname before entering loop
    nick_message_length_raw = connection.recv(HEADER)
    if not nick_message_length_raw:
        connection.close()
        return
    try:
        nick_message_length = int(nick_message_length_raw.decode(FORMAT).strip())
    except ValueError:
        connection.close()
        return
    if nick_message_length:
        nick_message = connection.recv(nick_message_length).decode(FORMAT)
        print(f'{nick_message} has joined the room from {address}!')

    #Update dictionaries
    client_addresses[connection] = address
    client_nicknames[connection] = nick_message
    nick_to_client[nick_message] = connection

    #Send welcome message to client upon connecting
    welcome_message = "SERVER: thank you for connecting!"
    send(welcome_message, (connection))
    # Broadcast join to other clients
    other_clients = [c for c in client_addresses if c != connection]
    if other_clients:
        send(f'{nick_message} has joined', *other_clients)

    #Default mode is broadcast
    client_modes[connection] = 'broadcast'

    #Listen for messages from client
    connected = True
    while connected:
        nick = client_nicknames.get(connection, '')
        message_length_raw = connection.recv(HEADER)
        if not message_length_raw:
            connected = False
            break
        try:
            message_length = int(message_length_raw.decode(FORMAT).strip())
        except ValueError:
            continue
        if message_length == 0:
            connected = False
            break
        message = connection.recv(message_length).decode(FORMAT)
        if message.startswith('!'):
            code = commands(connection, message)
            #If disconnect flag raised
            if code == -1:
                connected = False
                announce_disconnect = False
        else:
            #Server resends client message to target depending on mode
            mode = client_modes[connection]
            if mode == 'broadcast':
                print(client_addresses.values())
                targets = [c for c in client_addresses if c != connection]
                send(f'{nick}: {message}', *targets)
            elif mode[0] == 'group':
                group_name = mode[1]
                targets = [c for c in groups[group_name] if c != connection]
                send(f'[group {group_name}] {nick}: {message}', *targets)
            elif mode[0] == 'whisper':
                target_client = nick_to_client[mode[1]]
                if target_client != connection:
                    send(f'[whisper {mode[1]}] {nick}: {message}', (target_client))


            print(nick, ": ", message, client_modes[connection])
    cleanup_client(connection, nick_message, announce_disconnect)


def cleanup_client(connection, nick, announce=True):
    # clean up tracking dictionaries without re-referencing deleted keys
    if nick in nick_to_client:
        del nick_to_client[nick]
    if connection in client_nicknames:
        del client_nicknames[connection]
    if connection in client_addresses:
        del client_addresses[connection]
    if connection in client_modes:
        del client_modes[connection]
    for group_name, members in list(groups.items()):
        if connection in members:
            members.remove(connection)
            if not members:
                del groups[group_name]
    # Inform remaining clients
    remaining = [c for c in client_addresses]
    if remaining and nick and announce:
        send(f'{nick} has left', *remaining)
    status = 'unexpectedly' if announce else 'gracefully'
    print(f'{nick} has disconnected {status}.')
    connection.close()

def commands(connection, message):
    message_list = message.split()
    command = message_list[0]
    args = message_list[1:] if len(message_list) > 1 else []
    #If user chooses to disconnect we return a flag
    if command == '!disconnect':
        print(f'{client_nicknames[connection]} has disconnected.')
        send('SERVER: You have been disconnected.', (connection))
        # notify others
        others = [c for c in client_addresses if c != connection]
        if others:
            send(f'{client_nicknames[connection]} has left', *others)
        return -1
    #Expecting !joingroup <group>
    elif command == '!joingroup':
        if len(args) != 1:
            send('SERVER: Usage: !joingroup <group>', (connection))
        else:
            group_name = args[0]
            try:
                if group_name in groups:
                    groups[group_name].append(connection)
                else:
                    groups[group_name] = [connection]
                send(f'SERVER: You have joined the group {group_name}', (connection))
                # Notify existing group members (excluding self)
                group_members = [c for c in groups[group_name] if c != connection]
                if group_members:
                    send(f'{client_nicknames[connection]} has joined group {group_name}', *group_members)
            except Exception:
                send('SERVER: Failed to join group: ' + group_name, (connection))
        print(groups)
    #Expecting !leavegroup <group>
    elif command == '!leavegroup':
        if len(args) != 1:
            send('SERVER: Usage: !leavegroup <group>', (connection))
        else:
            group_name = args[0]
            if group_name in groups and connection in groups[group_name]:
                groups[group_name].remove(connection)
                # cleanup if group is empty
                if not groups[group_name]:
                    del groups[group_name]
                    send(f'SERVER: You have left the group {group_name}', (connection))
                else:
                    send(f'SERVER: You have left the group {group_name}', (connection))
                    # Notify remaining group members
                    group_members = groups[group_name]
                    if group_members:
                        send(f'{client_nicknames[connection]} has left group {group_name}', *group_members)
            else:
                send(f'SERVER: You are not part of the group {group_name}', (connection))
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
        shared_folder = 'SharedFiles'
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
        shared_folder = 'SharedFiles'
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
    for target in targets:
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
