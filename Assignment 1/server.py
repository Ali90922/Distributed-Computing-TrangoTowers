import socket
import sqlite3
import select

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

# Broadcast message to all connected clients and save to the database
def broadcast(message, sender_socket=None):
    sender_nickname = nicknames.get(sender_socket, "Unknown")  # Get the nickname associated with the socket
    for client_socket in clients.keys():
        if client_socket != sender_socket:  # Don't send the message back to the sender
            try:
                client_socket.send((message + "\n").encode('ascii'))  # Ensure each message ends with a newline
            except:
                client_socket.close()
                sockets_list.remove(client_socket)
                del clients[client_socket]

    # Save message to database with the sender's nickname
    cursor.execute('INSERT INTO messages (nickname, message) VALUES (?, ?)', (sender_nickname, message))
    conn.commit()

# Load the last few messages from the database
def load_messages(client_socket):
    cursor.execute('SELECT nickname, message FROM messages ORDER BY id DESC LIMIT 20')
    messages = cursor.fetchall()
    for nickname, message in reversed(messages):
        client_socket.send(f"{nickname}: {message}\n".encode('ascii'))  # Ensure each message ends with a newline

# Main server loop to handle connections and data
def run_server():
    print(f"Server is listening on {host}:{port}")
    while True:
        # Use select to wait for readable sockets
        readable, _, _ = select.select(sockets_list, [], [])

        for notified_socket in readable:
            if notified_socket == server:
                # Handle new connection
                client_socket, client_address = server.accept()
                client_socket.setblocking(False)
                sockets_list.append(client_socket)
                clients[client_socket] = None  # Placeholder for the nickname

                client_socket.send("NICK\n".encode('ascii'))  # Ask for nickname

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

run_server()
