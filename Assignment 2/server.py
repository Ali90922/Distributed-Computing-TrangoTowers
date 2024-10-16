# ----------------------------------------------------------------------------------------------
# Name: Ali Nawaz
# Student number: 7951458
# Course: COMP 3010, Distributed Computing
# Instructor: Saulo Santos 
# Assignment: Assignment 1, server.py
# 
# Remarks:
# - Implements a TCP server for chat communication on a specified port.
# - Utilizes SQLite to store and retrieve chat messages persistently.
# - Manages clients' connections and nicknames using non-blocking sockets and `select`.
# - Broadcasts messages to all clients, including joining/leaving notifications.
# - Gracefully handles server shutdown and client disconnection.
#-------------------------------------------------------------------------------------------------

import socket
import sqlite3
import select
import sys

# Server's host and port configuration
host = '0.0.0.0'  # Listen on all interfaces
port = 8547      # Port to listen on

# Connect to SQLite database (used for message storage)
# check_same_thread=False allows multiple threads to use the same connection
conn = sqlite3.connect('chat.db', check_same_thread=False)
cursor = conn.cursor()

# Create a table for storing messages.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT,
        message TEXT
    )
''')
conn.commit()

# Create a TCP server socket (IPv4)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Following line bypasses the Time Wait state :
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allows re-binding to the same address/port if the server is restarted
server.bind((host, port))  # Bind the server to the host and port
server.listen()  # Start listening for incoming connections

# Set the server socket to non-blocking mode
server.setblocking(False)

# List of sockets to monitor for incoming data (including the server socket)
sockets_list = [server]
clients = {}  # Dictionary to keep track of client sockets and nicknames
nicknames = {}  # Dictionary to map client sockets to nicknames

# Broadcast a message to all connected clients and save it to the database
def broadcast(message, sender_socket=None):
    sender_nickname = nicknames.get(sender_socket, "Unknown")  # Get the nickname associated with the socket
    for client_socket in clients.keys():
        if client_socket != sender_socket:  # Do not send the message back to the sender
            try:
                client_socket.send((message + "\n").encode('ascii'))  # Send message to all other clients
            except:
                # If sending fails, close the client socket and remove it
                client_socket.close()
                sockets_list.remove(client_socket)
                del clients[client_socket]

    # Save the message to the SQLite database
    cursor.execute('INSERT INTO messages (nickname, message) VALUES (?, ?)', (sender_nickname, message))
    conn.commit()

# Load the last few messages from the database and send them to a client
def load_messages(client_socket):
    cursor.execute('SELECT nickname, message FROM messages ORDER BY id DESC LIMIT 20')
    messages = cursor.fetchall()  # Fetch the last 20 messages from the database
    for nickname, message in reversed(messages):  # Send the messages in the correct order
        client_socket.send(f"{nickname}: {message}\n".encode('ascii'))

# Gracefully close all connections when shutting down the server
def close_all_connections():
    print("Shutting down the server...")
    for client_socket in clients.keys():
        try:
            client_socket.send("Server is shutting down.\n".encode('ascii'))
            client_socket.close()  # Close each client connection
        except:
            pass  # Ignore errors if clients have already disconnected
    server.close()  # Close the server socket
    conn.close()  # Close the database connection
    print("Server shut down.")
    sys.exit()  # Exit the program

# Main server loop to handle connections and data
def run_server():
    print(f"Server is listening on {host}:{port}")

    while True:
        # Use select to wait for readable sockets (including stdin for server commands)
        readable, _, _ = select.select(sockets_list + [sys.stdin], [], [])

        for notified_socket in readable:
            if notified_socket == server:
                # Handle new incoming connection
                try:
                    client_socket, client_address = server.accept()
                    client_socket.setblocking(False)  # Set the new client socket to non-blocking
                    sockets_list.append(client_socket)  # Add the new socket to the list of sockets to monitor
                    clients[client_socket] = None  # Placeholder for the nickname

                    client_socket.send("NICK\n".encode('ascii'))  # Ask the client for a nickname
                except Exception as e:
                    print(f"Error accepting new connection: {e}")

            elif notified_socket == sys.stdin:
                # Handle command line input (e.g., to shut down the server)
                command = sys.stdin.readline().strip()
                if command.lower() == 'quit':
                    close_all_connections()  # Shut down the server if 'quit' is entered

            else:
                # Handle incoming messages from clients
                try:
                    message = notified_socket.recv(1024).decode('ascii').strip()
                    if not message:
                        raise Exception("Empty message received")

                    # If the client hasn't sent a nickname yet
                    if clients[notified_socket] is None:
                        # The first message is the nickname
                        nicknames[notified_socket] = message  # Assign the nickname to the client
                        clients[notified_socket] = message  # Store the nickname in the clients dict
                        broadcast(f'{message} joined the chat!', notified_socket)
                        load_messages(notified_socket)  # Send the last few messages to the new client
                    else:
                        # Broadcast the message from the client to others
                        broadcast(f"{clients[notified_socket]}: {message}", notified_socket)

                except:
                    # Handle client disconnection or failure
                    nickname = clients.pop(notified_socket, None)
                    sockets_list.remove(notified_socket)
                    notified_socket.close()
                    if nickname:
                        broadcast(f'{nickname} has left the chat.')

# Run the server
run_server()

