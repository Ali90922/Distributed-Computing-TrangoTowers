import socket
import json

HOST = 'eagle.cs.umanitoba.ca'    # The remote host
PORT = 42424 # The same port as used by the server

# make the udp socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# listen on all interfaces, use the next available port
udp_socket.bind(('', 0))
# bind the socket to a public host, and a well-known port
hostname = socket.gethostname()
port = udp_socket.getsockname()[1]

print("UDP listening on {}:{} ".format(hostname, port))

returnAddress = {
    "host": hostname,
    "port": port
}

tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.connect((HOST, PORT))
asStr = json.dumps(returnAddress)
asBytes = asStr.encode()
tcp_socket.sendall(asBytes)

#listen on UDP for the word of the day
data = udp_socket.recv(1024)
print('Received', repr(data))
