import socket  # Import the socket library to create TCP connections
import sys  # Import sys to handle system-related functions, like exiting
import select  # Import select to monitor multiple I/O streams (sockets)
import traceback  # Import traceback to display detailed error messages

HOST = ''  # Empty string means the server will listen on all available interfaces (e.g., 0.0.0.0)
PORT = 50007  # The port on which the server will listen for incoming connections

lastWord = "F1rst p0st"  # This variable holds the last message received, initialized with a default value

# Create a TCP socket using IPv4 (AF_INET) and the SOCK_STREAM (TCP) type
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Set socket option to allow address reuse, ensuring smoother server restarts on the same port
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the socket to the provided HOST and PORT, making it ready to accept connections
    s.bind((HOST, PORT))
    
    # Set the socket to listen for incoming connections; the default backlog is sufficient for this example
    s.listen()

    clients = []  # A list to keep track of all connected clients (their socket objects)

    # Infinite loop to keep the server running and handling connections
    while True:
        try:
            # Create a list of input streams to monitor: the server socket and all connected clients
            inputs = [s] + clients

            # Use select() to check which sockets are ready for reading (input), with no timeouts for blocking
            readable, _, exceptional = select.select(inputs, [], inputs)

            # Iterate over all sockets that are ready for reading
            for client in readable:
                if client is s:  # If the readable socket is the server socket (s), a new client is trying to connect
                    conn, addr = s.accept()  # Accept the connection from the client
                    print('Connected by', addr)  # Print the address of the newly connected client
                    clients.append(conn)  # Add the new client socket to the list of connected clients

                else:  # If the socket is one of the clients, that client is sending data
                    data = client.recv(1024)  # Receive up to 1024 bytes of data from the client

                    if data:  # If data is received (non-empty):
                        print('swapping')  # Log the message swap action
                        currWord = lastWord  # Store the previous message (lastWord) in currWord
                        lastWord = data.strip()  # Update lastWord with the newly received message, stripping whitespace

                        # Send the last message (currWord) back to the client as a response
                        client.sendall(currWord)

                        # Send a "Bye!" message to the client, indicating the connection will close
                        client.sendall(b'Bye!')

                        # Close the connection with the client
                        client.close()

                        # Remove the client from the list of connected clients, as the connection is now closed
                        clients.remove(client)

        # Handle graceful shutdown if the server is interrupted by a KeyboardInterrupt (Ctrl+C)
        except KeyboardInterrupt:
            print("Server shut down")  # Log the shutdown message
            sys.exit(0)  # Exit the script cleanly

        # Catch any other exceptions that occur during runtime
        except Exception as e:
            print("An error occurred:")  # Log that an error occurred
            print(e)  # Print the error message itself
            traceback.print_exc()  # Print a full traceback of the error for debugging purposes

