Instant Messenger (Python 3.13)
--------------------------------
Prerequisites:
- Python 3.13 (standard library only; uses the built-in socket module).
- Place any downloadable assets in `SharedFiles` (or point `SERVER_SHARED_FILES` at another folder).

Run the programs (Windows-friendly commands):
- Start server: `python server.py <port>`
- Start client: `python client.py <username> <hostname> <port>`
  Example: `python client.py John 127.0.0.1 12000`

Chat behaviour:
- Each client sends its username to the server on connect and receives a welcome message from the server socket.
- The server logs the client IP/port and announces joins/leaves to other connected clients.
- Default mode is broadcast (send to all other clients).

User commands (type into the client prompt):
- `!disconnect`                          Disconnect cleanly.
- `!switchmode broadcast`                Return to broadcast messaging.
- `!switchmode whisper <username>`       Unicast to a single user.
- `!joingroup <group>`                   Join or create a named group.
- `!leavegroup <group>`                  Leave a named group.
- `!switchmode group <group>`            Send only to members of a joined group.
- `!sharedfiles`                         List files in the server's shared folder.
- `!download <filename> tcp|udp`         Download a file over TCP or UDP (saved under a folder named after your username, file size shown from server-sent metadata).

File sharing notes:
- The server reads files from `SharedFiles` in the project root.
- UDP downloads: the server advertises a UDP port; the client sends a READY datagram before receiving data.
- TCP downloads: the server sends a 64-byte size header followed by file bytes.

Operational notes:
- The server handles multiple clients via threads and tolerates unexpected disconnects without crashing.
- Group memberships are removed on disconnect; empty groups are cleaned up.
- All length-prefixed messages use a 64-byte header (`HEADER = 64`) encoded in UTF-8.

How it works (architecture):
- Server spins up a thread per client from `s.accept()`; each thread stays in a receive loop until a disconnect command or socket drop.
- All messages are length-prefixed (64-byte header) to keep reads aligned; strings are UTF-8 encoded.
- Client modes: broadcast sends to all other sockets; whisper maps a username to a single socket; group mode sends to members of the named group; `!switchmode` swaps between them.
- Groups are stored in-memory; joining creates the group, leaving removes you, and empty groups are deleted; disconnects trigger the same cleanup.
- File sharing: the server lists files from the shared folder and sends size metadata. TCP transfers stream bytes on the existing socket. UDP transfers use a temporary server UDP socket; the client replies with `READY` to the advertised port, then the server streams chunks to that address.
