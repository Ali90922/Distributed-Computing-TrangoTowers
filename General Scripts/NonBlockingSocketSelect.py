import socket
import select

# Create a TCP/IP server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 8080))
server_socket.listen(5)

# Set the server socket to non-blocking mode
server_socket.setblocking(False)

# Keep track of sockets
inputs = [server_socket]
outputs = []

print("Non-blocking server running...")

while inputs:
    # Monitor sockets using select (non-blocking I/O)
    readable, writable, exceptional = select.select(inputs, outputs, inputs)

    for s in readable:
        if s is server_socket:
            # Accept a new connection (non-blocking)
            client_socket, addr = s.accept()
            print(f"New connection from {addr}")
            client_socket.setblocking(False)
            inputs.append(client_socket)
        else:
            # Receive data from existing client (non-blocking)
            data = s.recv(1024)
            if data:
                print(f"Received: {data.decode()}")
                if s not in outputs:
                    outputs.append(s)
            else:
                # No data means client has closed the connection
                if s in outputs:
                    outputs.remove(s)
                inputs.remove(s)
                s.close()

    for s in writable:
        # Send data to clients that are ready to write
        s.sendall(b"Hello from server!")
        outputs.remove(s)

    for s in exceptional:
        # Handle errors
        inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()

