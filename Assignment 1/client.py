import socket
import select
import sys

# Choose a nickname for the user
nickname = input("Choose a Nickname: ")

# Create a client socket (IPv4 + TCP)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 55456))
client.setblocking(False)  # Make the socket non-blocking

# Main loop to handle sending and receiving messages
def run_client():
    while True:
        # Use select to monitor stdin (keyboard input) and the client socket
        sockets_list = [sys.stdin, client]
        readable, _, _ = select.select(sockets_list, [], [])

        for notified_socket in readable:
            if notified_socket == client:
                # Incoming message from the server
                try:
                    message = client.recv(1024).decode('ascii')
                    if message == 'NICK':
                        client.send(nickname.encode('ascii'))  # Send nickname when asked
                    else:
                        print(message)  # Display the message from the server
                except:
                    print("An error occurred!")
                    client.close()
                    sys.exit()

            else:
                # User input (keyboard)
                message = sys.stdin.readline().strip()
                if message:
                    client.send(f'{nickname}: {message}'.encode('ascii'))

run_client()
