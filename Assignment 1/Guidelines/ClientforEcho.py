# Client program to connect to the echo server

import socket  # Import the socket module for network communication

# Define the server's hostname or IP address and the port number
HOST = '127.0.0.1'  # Replace with the server's IP address if connecting remotely
PORT = 5000         # The port used by the server

def main():
    # Create a TCP/IP socket using IPv4 addressing
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            # Connect to the server at the specified HOST and PORT
            s.connect((HOST, PORT))
            print(f"Connected to server at {HOST}:{PORT}")
            while True:
                # Prompt the user to enter a message to send
                message = input("Enter message to send (or 'quit' to exit): ")
                if message.lower() == 'quit':
                    # If the user types 'quit', close the connection and exit
                    print("Closing connection.")
                    break
                # Send the message to the server after encoding it to bytes
                s.sendall(message.encode('utf-8'))
                # Receive data from the server (up to 1024 bytes)
                data = s.recv(1024)
                if not data:
                    # If no data is received, the server has closed the connection
                    print("Disconnected from server.")
                    break
                # Decode the received bytes back to a string and display the echoed message
                print(f"Received echo: {data.decode('utf-8')}")
        except ConnectionRefusedError:
            # Handle the case where the server is not running or cannot be reached
            print(f"Could not connect to server at {HOST}:{PORT}")
        except KeyboardInterrupt:
            # Allow the user to exit the client using Ctrl+C
            print("\nConnection closed by user.")

if __name__ == "__main__":
    main()  # Call the main function to start the client

