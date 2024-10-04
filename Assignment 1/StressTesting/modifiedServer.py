import socket
import select
import time
import sys
import psutil
import errno
import sqlite3  # Import SQLite module

host = '0.0.0.0'
port = 55456

# Create a server socket (IPv4 + TCP)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1048576)  # 1MB
server.bind((host, port))
server.listen(500)
server.setblocking(False)

sockets_list = [server]
clients = {}
nicknames = {}

# SQLite setup: Create or connect to an SQLite database
conn = sqlite3.connect('chat_logs.db')
cursor = conn.cursor()

# Create a table to store chat messages (if it doesn't already exist)
cursor.execute('''
CREATE TABLE IF NOT EXISTS chat_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    nickname TEXT,
    message TEXT
)
''')
conn.commit()

def log_message(nickname, message):
    """Log a message to the database."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
    INSERT INTO chat_logs (timestamp, nickname, message)
    VALUES (?, ?, ?)
    ''', (timestamp, nickname, message))
    conn.commit()

def get_last_100_messages():
    """Retrieve the last 100 messages from the database."""
    cursor.execute('''
    SELECT timestamp, nickname, message
    FROM chat_logs
    ORDER BY id DESC
    LIMIT 100
    ''')
    return cursor.fetchall()[::-1]  # Reverse order to show from oldest to newest

def broadcast(message, sender_socket=None):
    """Broadcast a message to all clients except the sender."""
    for client_socket in list(clients.keys()):
        if client_socket == sender_socket:
            continue
        try:
            client_socket.send((message + "\n").encode('ascii'))
        except socket.error as e:
            if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                print(f"Socket buffer full for {clients.get(client_socket, 'Unknown')}. Will retry later.")
                continue
            else:
                print(f"Error sending message to {clients.get(client_socket, 'Unknown')}: {e}")
                remove_client(client_socket)

def remove_client(client_socket):
    """Remove a client from the server and close their connection."""
    if client_socket in sockets_list:
        sockets_list.remove(client_socket)
    if client_socket in clients:
        nickname = clients.pop(client_socket)
        print(f"Client {nickname} has been removed.")
    if client_socket in nicknames:
        nicknames.pop(client_socket)
    client_socket.close()
    leave_message = f'{nickname} has left the chat.'
    broadcast(leave_message)

def run_server():
    """Main server loop to handle connections and messages."""
    print(f"Server is listening on {host}:{port}")

    while True:
        timeout = 0.5

        try:
            read_sockets = sockets_list + [sys.stdin]
            readable, _, _ = select.select(read_sockets, [], [], timeout)
        except Exception as e:
            print(f"Select error: {e}")
            break

        for notified_socket in readable:
            if notified_socket == server:
                try:
                    client_socket, client_address = server.accept()
                    client_socket.setblocking(False)
                    sockets_list.append(client_socket)
                    clients[client_socket] = None
                    client_socket.send("NICK\n".encode('ascii'))  # Ask for nickname
                except Exception as e:
                    print(f"Error accepting new connection: {e}")
            elif notified_socket == sys.stdin:
                command = sys.stdin.readline().strip().lower()
                if command == 'quit':
                    print("Shutdown command received. Shutting down the server.")
                    for sock in sockets_list:
                        sock.close()
                    conn.close()  # Close the database connection
                    return
            else:
                try:
                    message = notified_socket.recv(8192).decode('ascii').strip()
                    if not message:
                        raise Exception("Empty message")

                    if clients[notified_socket] is None:
                        # First message is the nickname
                        nicknames[notified_socket] = message
                        clients[notified_socket] = message  # Set nickname
                        broadcast(f'{message} joined the chat!', notified_socket)

                        # Send last 100 messages to the new client
                        last_messages = get_last_100_messages()
                        for timestamp, nickname, msg in last_messages:
                            client_socket.send(f"[{timestamp}] {nickname}: {msg}\n".encode('ascii'))
                    else:
                        nickname = clients[notified_socket]
                        broadcast(f"{nickname}: {message}", notified_socket)
                        log_message(nickname, message)  # Log message to database

                except Exception as e:
                    nickname = clients.get(notified_socket, "Unknown")
                    print(f"Error with client {nickname}: {e}")
                    remove_client(notified_socket)

run_server()
