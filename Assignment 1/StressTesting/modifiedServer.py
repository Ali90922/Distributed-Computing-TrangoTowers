import socket
import sqlite3
import select
import time
import threading

host = '127.0.0.1'
port = 55456

# Connect to SQLite database
conn = sqlite3.connect('chat.db', check_same_thread=False)
cursor = conn.cursor()

# Create table for storing messages
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT,
        message TEXT
    )
''')
conn.commit()

# Create a server socket (IPv4 + TCP)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((host, port))
server.listen()

# Set server socket to non-blocking
server.setblocking(False)

# List of sockets to monitor for incoming data
sockets_list = [server]
clients = {}
nicknames = {}

# Performance tracking variables
message_count = 0
start_time = time.time()

# Total performance tracking variables
total_message_count = 0
server_start_time = time.time()
lock = threading.Lock()

# Running flag to control the server loop
running = True

# Broadcast message to all connected clients and save to the database
def broadcast(message, sender_socket=None):
    global message_count, total_message_count
    sender_nickname = nicknames.get(sender_socket, "Unknown")  # Get the nickname associated with the socket

    # Increment message counts safely
    with lock:
        message_count += 1
        total_message_count += 1

    for client_socket in list(clients.keys()):
        if client_socket != sender_socket:  # Don't send the message back to the sender
            try:
                client_socket.send((message + "\n").encode('ascii'))  # Ensure each message ends with a newline
            except:
                client_socket.close()
                sockets_list.remove(client_socket)
                del clients[client_socket]
                nickname = nicknames.pop(client_socket, "Unknown")
                broadcast(f'{nickname} has left the chat.')

    # Save message to database with the sender's nickname
    cursor.execute('INSERT INTO messages (nickname, message) VALUES (?, ?)', (sender_nickname, message))
    conn.commit()

# Load the last few messages from the database
def load_messages(client_socket):
    cursor.execute('SELECT nickname, message FROM messages ORDER BY id DESC LIMIT 20')
    messages = cursor.fetchall()
    for nickname, message in reversed(messages):
        try:
            client_socket.send(f"{nickname}: {message}\n".encode('ascii'))  # Ensure each message ends with a newline
        except:
            client_socket.close()
            sockets_list.remove(client_socket)
            del clients[client_socket]
            nickname = nicknames.pop(client_socket, "Unknown")
            broadcast(f'{nickname} has left the chat.')

# Function to log performance
def log_performance():
    global message_count, start_time
    while running:
        time.sleep(5)  # Log every 5 seconds
        with lock:
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:
                mps = message_count / elapsed_time
                client_count = len(clients)
                print(f"Messages processed: {message_count}, Elapsed time: {elapsed_time:.2f}s, Messages per second: {mps:.2f}, Clients connected: {client_count}")
                # Reset counters
                message_count = 0
                start_time = time.time()

# Function to listen for server commands (e.g., 'quit')
def listen_for_commands():
    global running
    while running:
        command = input()
        if command.strip().lower() == 'quit':
            print("Shutdown command received. Shutting down the server.")
            running = False
            # Close the server socket to unblock accept()
            server.close()
            break

# Main server loop to handle connections and data
def run_server():
    global running
    print(f"Server is listening on {host}:{port}")

    # Start the performance logging thread
    performance_thread = threading.Thread(target=log_performance)
    performance_thread.start()

    # Start the command listening thread
    command_thread = threading.Thread(target=listen_for_commands)
    command_thread.start()

    while running:
        # Use select to wait for readable sockets
        try:
            readable, _, _ = select.select(sockets_list, [], [], 1)
        except Exception as e:
            break  # Exit the loop if select fails, likely due to server socket being closed

        for notified_socket in readable:
            if notified_socket == server:
                # Handle new connection
                try:
                    client_socket, client_address = server.accept()
                    client_socket.setblocking(False)
                    sockets_list.append(client_socket)
                    clients[client_socket] = None  # Placeholder for the nickname

                    client_socket.send("NICK\n".encode('ascii'))  # Ask for nickname
                except:
                    pass  # If server socket is closed, accept() will fail

            else:
                # Handle data from existing clients
                try:
                    message = notified_socket.recv(1024).decode('ascii').strip()
                    if not message:
                        raise Exception("Empty message")

                    # If the client hasn't sent a nickname yet
                    if clients[notified_socket] is None:
                        nicknames[notified_socket] = message
                        clients[notified_socket] = message  # Set nickname
                        broadcast(f'{message} joined the chat!', notified_socket)
                        load_messages(notified_socket)
                    else:
                        # Otherwise, broadcast the message to others
                        broadcast(f"{clients[notified_socket]}: {message}", notified_socket)

                except:
                    # Remove the client on failure
                    nickname = clients.pop(notified_socket, None)
                    sockets_list.remove(notified_socket)
                    notified_socket.close()
                    if nickname:
                        broadcast(f'{nickname} has left the chat.')

    # Wait for threads to finish
    performance_thread.join()
    command_thread.join()

    # Calculate total performance summary
    total_elapsed_time = time.time() - server_start_time
    if total_elapsed_time > 0:
        avg_mps = total_message_count / total_elapsed_time
    else:
        avg_mps = 0
    print(f"\nServer shutting down.")
    print(f"Total messages processed: {total_message_count}")
    print(f"Total elapsed time: {total_elapsed_time:.2f}s")
    print(f"Average messages per second: {avg_mps:.2f}")

    # Close all client sockets
    for client_socket in clients.keys():
        client_socket.close()

    # Close the database connection
    conn.close()

run_server()
