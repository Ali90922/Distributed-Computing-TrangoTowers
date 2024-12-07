import socket

# create an INET, STREAMing socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# now connect to the web server on port 80 - the normal http port
s.connect(("127.0.0.1", 2000))

s.sendall(b'This is my message')
data = s.recv(1024)
print('Received:')
# It's in bytes, convert to text
print(data.decode("utf-8") )

s.close()