import socket
import threading
#Using threading since we are handling multiple clients

s = socket.socket()

# Bind port to socket
# Empty string for IP makes server listen for requests from any computer
# localhost would mean we can only listen from this computer
PORT = 6767
SERVER = socket.gethostbyname(socket.gethostname())

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', PORT))


print('server bound at ', PORT)

#listen() takes size of request queue
s.listen(9)
print('server listening')

#accept() lets it recieve conenections 
# accepted connection is a new seperate socket
# a forever loop until we interrupt it or 
# an error occurs 
while True: 

# Establish connection with client. 
  client, address = s.accept()     
  print('Got connection from', address )

  # send a thank you message to the client. encoding to send byte type. 
  client.send('Thank you for connecting'.encode()) 

  # Close the connection with the client 
  client.close()
  
  # Breaking once connection closed
  break

