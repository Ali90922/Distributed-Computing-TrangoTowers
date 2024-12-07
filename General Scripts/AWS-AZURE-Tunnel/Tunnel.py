import socket
import threading
import os

# Configuration
HOST = '0.0.0.0'  # Bind to all available interfaces (this will be your Azure/AWS VM)
PORT = 55000      # Common port for both peers
BUFFER_SIZE = 4096
PEER_IP = 'PEER_VM_IP'  # Replace with the IP of the peer VM

# Function to receive files
def receive_file(conn):
    filename = conn.recv(BUFFER_SIZE).decode('utf-8')
    with open(filename, 'wb') as f:
        print(f'Receiving {filename}')
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            f.write(data)
    print(f'{filename} received successfully.')
    conn.close()

# Function to send a file to the peer
def send_file(filename, peer_ip):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((peer_ip, PORT))
    
    client_socket.send(filename.encode('utf-8'))
    with open(filename, 'rb') as f:
        print(f'Sending {filename}')
        while chunk := f.read(BUFFER_SIZE):
            client_socket.send(chunk)
    print(f'{filename} sent successfully.')
    client_socket.close()

# Listening for incoming connections (server functionality)
def listen_for_connections():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Listening for connections on {HOST}:{PORT}...")

    while True:
        conn, addr = server_socket.accept()
        print(f'Connected by {addr}')
        threading.Thread(target=receive_file, args=(conn,)).start()

# Peer functionality
def peer():
    # Start the listener thread to receive files
    listener_thread = threading.Thread(target=listen_for_connections)
    listener_thread.start()

    # Example: Sending a file after some time
    while True:
        command = input("Enter 'send' to transfer a file or 'exit' to quit: ").strip()
        if command == 'send':
            filename = input("Enter the filename to send: ").strip()
            if os.path.exists(filename):
                send_file(filename, PEER_IP)
            else:
                print("File does not exist.")
        elif command == 'exit':
            break

if __name__ == '__main__':
    peer()

