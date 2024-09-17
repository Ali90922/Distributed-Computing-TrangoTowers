import socket
import threading
import sqlite3

host = '127.0.0.1'  # Local host IP address
# host = socket.gethostbyname(socket.gethostname())    --- Determines the local machines ip address automatically instead of typing it in !

port = 55456

# Create a server socket using IPv4 and TCP protocols
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

server.bind((host, port))  # Bind the server to the specified host and port
server.listen()  # Server starts listening for incoming connections

clients = []
Nicknames = []

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('chat.db', check_same_thread=False)
cursor = conn.cursor()

# Create a table for storing messages if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT,
        message TEXT
    )
''')
conn.commit()

# Broadcast function to send a message to all connected clients and save to database
def Broadcast(message, nickname):
    for client in clients:
        client.send(f"{nickname}: {message}".encode('ascii'))
    # Save the message to the database
    cursor.execute('INSERT INTO messages (nickname, message) VALUES (?, ?)', (nickname, message))
    conn.commit()

# Handle individual client connections
def handle(client):
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            index = clients.index(client)
            nickname = Nicknames[index]
            Broadcast(message, nickname)
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = Nicknames[index]
            Broadcast(f'{nickname} has left the chat !!', 'Server')
            Nicknames.remove(nickname)
            break

# Load the last few messages from the database
def load_messages(client):
    cursor.execute('SELECT nickname, message FROM messages ORDER BY id DESC LIMIT 20')
    messages = cursor.fetchall()
    for nickname, message in reversed(messages):
        client.send(f"{nickname}: {message}".encode('ascii'))

# Receive incoming connections and manage clients
def receive():
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")
        client.send("NICK".encode('ascii'))
        nickname = client.recv(1024).decode('ascii')
        Nicknames.append(nickname)
        clients.append(client)

        print(f'Nickname of the client is {nickname}!')
        Broadcast(f'{nickname} joined the chat!', 'Server')
        client.send('You are connected to the server!'.encode('ascii'))

        # Load recent messages for the newly connected client
        load_messages(client)

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

print("Server is listening ......")
receive()
