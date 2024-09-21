import socket
import select
import sys

# Choose a nickname for the user
nickname = input("Choose a Nickname: ")

# Create a client socket (IPv4 + TCP)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 55456))
client.setblocking(False)  # Make the socket non-blocking

# Display the prompt with the nickname immediately after the nickname is chosen
sys.stdout.write(f'{nickname}: ')
sys.stdout.flush()

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
                    message = client.recv(1024).decode('ascii').strip()
                    if message == 'NICK':
                        client.send(nickname.encode('ascii'))  # Send nickname when asked
                    else:
                        print(f'\n{message}')  # Display the message from the server with a newline
                        sys.stdout.write(f'{nickname}: ')  # Re-display the input prompt after incoming message
                        sys.stdout.flush()
                except:
                    print("An error occurred!")
                    client.close()
                    sys.exit()

            else:
                # Show the prompt with the nickname and let the user type their message
                message = sys.stdin.readline().strip()
                if message:
                    # Send the message as is
                    client.send(f'{nickname}: {message}'.encode('ascii'))

                    # Show the prompt again after sending the message
                    sys.stdout.write(f'{nickname}: ')
                    sys.stdout.flush()

run_client()
