import socket
import sys
import threading
import os

if len(sys.argv) != 4:
    print("Usage: python client.py <username> <hostname> <port>")
    sys.exit(1)

HEADER = 64
PORT = int(sys.argv[3])
HOSTNAME = sys.argv[2]
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
ADDRESS = (HOSTNAME, PORT)
NICKNAME = sys.argv[1]


def send(client):
    while not disconnected.is_set():
        message = input()
        if not message.startswith('!'):
            print('sending message: ', message)
        #Handle disconnect directly due to race cases
        elif message == "!disconnect":
            disconnected.set()
        message = message.encode(FORMAT)
        # Get message length for header
        message_length = len(message)
        send_length = str(message_length).encode(FORMAT)

        #Pad to fit 64 byte header
        send_length += b' ' * (HEADER - len(send_length))
        client.send(send_length)
        client.send(message)
        
       
            

def recieve(client):
    expecting_file = False
    file_info = None
    udp_mode = False
    udp_params = None
    while not disconnected.is_set():
        if expecting_file:
            username = NICKNAME
            folder = username
            if not os.path.exists(folder):
                os.makedirs(folder)
            if udp_mode:
                udp_port, filename, filesize = udp_params
                filepath = os.path.join(folder, filename)
                udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    udp_sock.sendto(b'READY', (HOSTNAME, udp_port))
                    with open(filepath, 'wb') as f:
                        bytes_received = 0
                        while bytes_received < filesize:
                            chunk, sender_addr = udp_sock.recvfrom(min(1024, filesize - bytes_received))
                            if not chunk:
                                break
                            f.write(chunk)
                            bytes_received += len(chunk)
                finally:
                    udp_sock.close()
                print(f'Downloaded {filename} ({filesize} bytes) to {folder}/')
                expecting_file = False
                udp_mode = False
                udp_params = None
                file_info = None
            else:
                # For TCP, expect a 64-byte header with file size before file data
                file_size_header = client.recv(HEADER)
                if not file_size_header:
                    print("You have disconnected from the server.")
                    disconnected.set()
                    continue
                file_size_str = file_size_header.decode(FORMAT).strip()
                filesize = int(file_size_str)
                filepath = os.path.join(folder, file_info[0])
                with open(filepath, 'wb') as f:
                    bytes_received = 0
                    while bytes_received < filesize:
                        chunk = client.recv(min(1024, filesize - bytes_received))
                        if not chunk:
                            break
                        f.write(chunk)
                        bytes_received += len(chunk)
                print(f'Downloaded {file_info[0]} ({filesize} bytes) to {folder}/')
                expecting_file = False
                file_info = None
            continue

        # Receive header for message length
        message_length_raw = client.recv(HEADER)
        if not message_length_raw:
            print("You have disconnected from the server.")
            disconnected.set()
            continue
        message_length = int(message_length_raw.decode(FORMAT))
        message = client.recv(message_length).decode(FORMAT)
        # Check if server is about to send a file via TCP
        if message.startswith('SERVER: Sending') and '(' in message and 'bytes' in message:
            # Parse filename and size from server message
            parts = message.split()
            filename = parts[2]
            size_str = message.split('(')[1].split()[0]
            filesize = int(size_str)
            print(message)
            expecting_file = True
            file_info = (filename, filesize)
            udp_mode = False
        # Check if server is about to send a file via UDP
        elif message.startswith('SERVER: UDPPORT'):
            # Format: SERVER: UDPPORT <port> <filename> <filesize>
            parts = message.split()
            udp_port = int(parts[2])
            filename = parts[3]
            filesize = int(parts[4])
            print(f'SERVER: Sending {filename} ({filesize} bytes) via UDP on port {udp_port}.')
            expecting_file = True
            udp_mode = True
            udp_params = (udp_port, filename, filesize)
        else:
            # Handle disconnect message
            if message == DISCONNECT_MESSAGE:
                disconnected.set()
            print(message)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDRESS)
disconnected = threading.Event()

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



