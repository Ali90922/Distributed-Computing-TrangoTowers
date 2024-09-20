import socket  # Import the socket library for handling networking
import threading  # Import threading for concurrent connections
import os  # Import os for checking file existence and working with files

# Configuration settings
# HOST: '0.0.0.0' means the server will listen on all network interfaces available on the VM
# This could be a public IP, private IP, or localhost (127.0.0.1).
# PORT: 55555 is the port number that both peers will use for communication.
HOST = '0.0.0.0'
PORT = 55555  # Common port where both peers will send/receive data
BUFFER_SIZE = 4096  # Size of the buffer for file transfers (how much data is transferred at once)
PEER_IP = '3.133.97.10'  # IP address of the peer (AWS to Azure or vice versa). Replace with your peer's actual IP.

# Function to receive files from the peer (acts like a server)
# This function gets triggered when a peer connects and starts sending a file.
def receive_file(conn):
    # First, the server receives the file name from the peer
    filename = conn.recv(BUFFER_SIZE).decode('utf-8')
    
    # Open a new file in write-binary mode to store the incoming file
    with open(filename, 'wb') as f:
        print(f'Receiving {filename}')
        
        # Keep receiving file data in chunks (up to BUFFER_SIZE at a time)
        while True:
            data = conn.recv(BUFFER_SIZE)
            # If no more data is received, break out of the loop
            if not data:
                break
            # Write the data to the file
            f.write(data)
    
    print(f'{filename} received successfully.')
    # Close the connection after the file is fully received
    conn.close()

# Function to send a file to the peer (acts like a client)
def send_file(filename, peer_ip):
    # Create a new TCP socket for the client
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Connect to the peer's IP address on the specified PORT
    # The peer should already be listening on this port.
    client_socket.connect((peer_ip, PORT))
    
    # Send the file name to the peer (the receiver needs to know what file it's getting)
    client_socket.send(filename.encode('utf-8'))
    
    # Open the file to send in read-binary mode
    with open(filename, 'rb') as f:
        print(f'Sending {filename}')
        
        # Keep reading chunks from the file and send them to the peer
        while chunk := f.read(BUFFER_SIZE):
            client_socket.send(chunk)
    
    print(f'{filename} sent successfully.')
    # Close the socket after the file is fully sent
    client_socket.close()

# Function that starts listening for incoming connections (this is the server functionality)
def listen_for_connections():
    # Create a new TCP socket for the server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Allow reuse of the address to prevent "address already in use" errors
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind the server socket to the HOST and PORT, so it's ready to accept connections
    server_socket.bind((HOST, PORT))
    
    # Start listening for incoming connections (queue size 1 means max 1 connection waiting)
    server_socket.listen(1)
    print(f"Listening for connections on {HOST}:{PORT}...")
    
    # Keep the server running to accept connections indefinitely
    while True:
        # Accept an incoming connection (this will block until a peer connects)
        conn, addr = server_socket.accept()
        print(f'Connected by {addr}')
        
        # Start a new thread to handle the file reception, so the server can keep listening for more connections
        threading.Thread(target=receive_file, args=(conn,)).start()

# Main peer function: this handles both listening (server) and sending (client) functionality
def peer():
    # Start the listener thread to allow receiving files from peers
    listener_thread = threading.Thread(target=listen_for_connections)
    listener_thread.start()

    # Infinite loop to handle sending files interactively
    while True:
        # Wait for user input: either send a file or exit
        command = input("Enter 'send' to transfer a file or 'exit' to quit: ").strip()
        
        if command == 'send':
            # If user chooses 'send', prompt them for a filename
            filename = input("Enter the filename to send: ").strip()
            
            # Check if the file exists before attempting to send it
            if os.path.exists(filename):
                # If the file exists, call the send_file function to send it to the peer
                send_file(filename, PEER_IP)
            else:
                print("File does not exist.")
        
        elif command == 'exit':
            # Exit the loop if the user enters 'exit'
            break

# This ensures that the peer function only runs if the script is executed directly (not imported as a module)
if __name__ == '__main__':
    peer()
