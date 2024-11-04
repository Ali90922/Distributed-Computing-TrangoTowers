import socket
import sqlite3
import select
import sys

host = '0.0.0.0'
port = 8547

# Database connection
conn = sqlite3.connect('chat.db', check_same_thread=False)
cursor = conn.cursor()

# Create table for messages if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT,
        message TEXT
    )
''')
conn.commit()

# Set up the server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((host, port))
server.listen()
server.setblocking(False)

# Lists for sockets and client tracking
sockets_list = [server]
clients = {}
nicknames = {}

def broadcast(message, sender_socket=None, include_nickname=True):
    """Broadcasts a message to all clients and saves it in the database."""
    sender_nickname = nicknames.get(sender_socket, "Server")
    message_to_send = f"{sender_nickname}: {message}" if include_nickname else message

    # Broadcast to all clients
    for client_socket in list(clients.keys()):
        if client_socket != sender_socket:
            try:
                client_socket.send((message_to_send + "\n").encode('ascii'))
            except:
                client_socket.close()
                if client_socket in sockets_list:
                    sockets_list.remove(client_socket)
                del clients[client_socket]

    # Save the message in the database
    cursor.execute('INSERT INTO messages (nickname, message) VALUES (?, ?)', (sender_nickname, message))
    conn.commit()
    print(f"Message saved in database: {sender_nickname}: {message}")

def load_messages(client_socket):
    """Loads the latest 20 messages and sends them to the client."""
    cursor.execute('SELECT nickname, message FROM messages ORDER BY id DESC LIMIT 20')
    messages = cursor.fetchall()
    for nickname, message in reversed(messages):
        client_socket.send(f"{nickname}: {message}\n".encode('ascii'))

def handle_web_request(notified_socket, message):
    """Handles web requests for GET_MESSAGES and SEND_MESSAGE."""
    if message == 'GET_MESSAGES':
        cursor.execute('SELECT nickname, message FROM messages ORDER BY id DESC LIMIT 20')
        messages = cursor.fetchall()
        response = "\n".join([f"{nickname}: {msg}" for nickname, msg in reversed(messages)])
        
        try:
            notified_socket.sendall(response.encode('ascii'))
            notified_socket.shutdown(socket.SHUT_WR)
            notified_socket.close()
            if notified_socket in sockets_list:
                sockets_list.remove(notified_socket)
        except Exception as e:
            if notified_socket in sockets_list:
                sockets_list.remove(notified_socket)
    elif message.startswith('SEND_MESSAGE'):
        msg_content = message[len('SEND_MESSAGE '):].strip()
        if ": " in msg_content:
            nickname, content = msg_content.split(": ", 1)
            nicknames[notified_socket] = nickname.strip()
            broadcast(content, notified_socket)
        else:
            broadcast(msg_content, notified_socket)

def close_all_connections():
    """Gracefully close all client connections and the server."""
    for client_socket in list(clients.keys()):
        try:
            client_socket.send("Server is shutting down.\n".encode('ascii'))
            client_socket.close()
        except:
            pass
    server.close()
    conn.close()
    sys.exit()

def run_server():
    """Main server loop that handles client connections and messages."""
    print(f"Server is listening on {host}:{port}")

    while True:
        readable, _, _ = select.select(sockets_list + [sys.stdin], [], [])

        for notified_socket in readable:
            if notified_socket == server:
                try:
                    client_socket, client_address = server.accept()
                    client_socket.setblocking(False)
                    sockets_list.append(client_socket)
                    clients[client_socket] = None
                    client_socket.send("NICK\n".encode('ascii'))
                except Exception as e:
                    print(f"Error accepting new connection: {e}")

            elif notified_socket == sys.stdin:
                command = sys.stdin.readline().strip()
                if command.lower() == 'quit':
                    close_all_connections()

            else:
                try:
                    message = notified_socket.recv(1024).decode('ascii').strip()
                    if not message:
                        raise Exception("Empty message received")

                    if clients.get(notified_socket) is None:
                        if message.startswith("SEND_MESSAGE") or message == "GET_MESSAGES":
                            handle_web_request(notified_socket, message)
                        else:
                            nicknames[notified_socket] = message
                            clients[notified_socket] = message
                            load_messages(notified_socket)
                    else:
                        # Broadcast the message, ensuring nickname is included only once
                        broadcast(message, notified_socket, include_nickname=False)

                except Exception as e:
                    nickname = clients.pop(notified_socket, None)
                    if notified_socket in sockets_list:
                        sockets_list.remove(notified_socket)
                    notified_socket.close()
                    if nickname:
                        broadcast(f'{nickname} has left the chat.')

run_server()
