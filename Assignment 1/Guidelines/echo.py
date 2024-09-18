# Multi-threaded Echo server program

import socket        # Import the socket module for network communication
import threading     # Import threading to handle multiple clients concurrently

HOST = ''    # Listen on all available network interfaces
PORT = 5000  # Arbitrary non-privileged port to listen on

def handle_client(conn, addr):
    """
    Function to handle client connection.
    Parameters:
    - conn: The socket object for the client connection.
    - addr: The address of the client.
    """
    print(f"Connected by {addr}")
    conn.settimeout(1)  # Set a timeout of 1 second for blocking socket operations
    try:
        with conn:  # Ensure the connection is properly closed after handling
            while True:
                # Receive data from the client (up to 1024 bytes)
                data = conn.recv(1024)
                if not data:
                    # If no data is received, the client has closed the connection
                    break
                # Echo the received data back to the client
                conn.sendall(data)
                # Decode the received bytes and print the message along with client address
                print(f"Received from {addr}: {data.decode('utf-8')}")
    except socket.timeout:
        # Handle socket timeout exception
        print(f"Connection with {addr} timed out.")
    except Exception as e:
        # Handle any other exceptions
        print(f"An error occurred with {addr}: {e}")
    finally:
        # Inform that the connection with the client has been closed
        print(f"Connection with {addr} closed.")

def main():
    # Create a TCP/IP socket using IPv4 addressing
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Set socket options to allow reusing the address
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to the specified HOST and PORT
        s.bind((HOST, PORT))
        # Listen for incoming connections
        s.listen()
        print(f"Server listening on port {PORT}...")
        while True:
            # Accept a new client connection
            conn, addr = s.accept()
            # Create a new thread to handle the client connection
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()  # Start the client thread

if __name__ == "__main__":
    main()  # Call the main function to start the server
