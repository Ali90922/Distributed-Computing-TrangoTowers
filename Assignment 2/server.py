import socket
import sqlite3
import select
import sys

host = '0.0.0.0'
port = 8547

conn = sqlite3.connect('chat.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT,
        message TEXT
    )
''')
conn.commit()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((host, port))
server.listen()
server.setblocking(False)

sockets_list = [server]
clients = {}
nicknames = {}

def broadcast(message, sender_socket=None):
    sender_nickname = nicknames.get(sender_socket, "Server")
    for client_socket in clients.keys():
        if client_socket != sender_socket:
            try:
                client_socket.send((message + "\n").encode('ascii'))
            except:
                client_socket.close()
                sockets_list.remove(client_socket)
                del clients[client_socket]

    cursor.execute('INSERT INTO messages (nickname, message) VALUES (?, ?)', (sender_nickname, message))
    conn.commit()

def load_messages(client_socket):
    cursor.execute('SELECT nickname, message FROM messages ORDER BY id DESC LIMIT 20')
    messages = cursor.fetchall()
    for nickname, message in reversed(messages):
        client_socket.send(f"{nickname}: {message}\n".encode('ascii'))

def handle_web_request(notified_socket, message):
    if message == 'GET_MESSAGES':
        cursor.execute('SELECT nickname, message FROM messages ORDER BY id DESC LIMIT 20')
        messages = cursor.fetchall()
        response = "\n".join([f"{nickname}: {message}" for nickname, message in reversed(messages)])
        notified_socket.send(response.encode('ascii'))
    elif message.startswith('SEND_MESSAGE'):
        msg_content = message[len('SEND_MESSAGE '):].strip()
        if ": " in msg_content:  # Ensure message has a nickname
            nickname, content = msg_content.split(": ", 1)
            nicknames[notified_socket] = nickname.strip()
            broadcast(content, notified_socket)
        else:
            broadcast(msg_content, notified_socket)

def close_all_connections():
    print("Shutting down the server...")
    for client_socket in clients.keys():
        try:
            client_socket.send("Server is shutting down.\n".encode('ascii'))
            client_socket.close()
        except:
            pass
    server.close()
    conn.close()
    sys.exit()

def run_server():
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
                            broadcast(f'{message} joined the chat!', notified_socket)
                            load_messages(notified_socket)
                    else:
                        broadcast(f"{clients[notified_socket]}: {message}", notified_socket)

                except Exception as e:
                    nickname = clients.pop(notified_socket, None)
                    sockets_list.remove(notified_socket)
                    notified_socket.close()
                    if nickname:
                        broadcast(f'{nickname} has left the chat.')

run_server()