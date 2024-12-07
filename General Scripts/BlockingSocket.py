import socket

# Creating a server with blocking sockets
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 8080))
server_socket.listen(5)

print("Blocking server is running...")

while True:
    # Blocking call - wait for a client to connect
    client_socket, addr = server_socket.accept()
    print(f"Connected to {addr}")

    # Blocking call - wait for data to be received
    data = client_socket.recv(1024)
    if data:
        print(f"Received: {data.decode()}")
        # Blocking call - send data
        client_socket.sendall(b"Hello from server!")

    client_socket.close()  # Close connection after responding

