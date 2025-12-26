import socket
import sys
import threading
import os

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
    while not disconnected.is_set():
        # Receive header for message length
        message_length = client.recv(HEADER).decode(FORMAT)
        if message_length:
            message_length = int(message_length)
            if not expecting_file:
                # Normal message handling
                message = client.recv(message_length).decode(FORMAT)
                # Check if server is about to send a file
                if message.startswith('SERVER: Sending') and '(' in message and 'bytes' in message:
                    # Parse filename and size from server message
                    parts = message.split()
                    filename = parts[2]
                    size_str = message.split('(')[1].split()[0]
                    filesize = int(size_str)
                    print(message)
                    expecting_file = True
                    file_info = (filename, filesize)
                else:
                    # Handle disconnect message
                    if message == DISCONNECT_MESSAGE:
                        disconnected.set()
                    print(message)
            else:
                # Directly receive file bytes, no extra header
                username = NICKNAME
                folder = username
                # Create user folder if it doesn't exist
                if not os.path.exists(folder):
                    os.makedirs(folder)
                filepath = os.path.join(folder, file_info[0])
                #Write file bytes
                with open(filepath, 'wb') as f:
                    bytes_received = 0
                    filesize = file_info[1]
                    while bytes_received < filesize:
                        chunk = client.recv(min(1024, filesize - bytes_received))
                        if not chunk:
                            break
                        f.write(chunk)
                        bytes_received += len(chunk)
                print(f'Downloaded {file_info[0]} ({filesize} bytes) to {folder}/')
                expecting_file = False
                file_info = None
        else:
            print("You have disconnected from the server.")
            disconnected.set()
        #print('an error occured (recieve)')

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






