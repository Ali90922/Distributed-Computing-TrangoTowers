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
    partial_message = ''  # Store what the user is currently typing
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
                        # Move the cursor back to the start of the line, clear the line, and display the message
                        sys.stdout.write(f'\r\033[K{message}\n')  # \033[K clears from the cursor to the end of the line

                        # Re-display the prompt and restore the partially typed message
                        sys.stdout.write(f'{nickname}: {partial_message}')
                        sys.stdout.flush()

                except Exception as e:
                    print(f"An error occurred: {e}")
                    client.close()
                    sys.exit()

            else:
                # Capture what the user is typing, and handle Enter key press
                new_input = sys.stdin.readline().strip()
                if new_input:
                    # Send the message
                    client.send(f'{nickname}: {new_input}'.encode('ascii'))
                    partial_message = ''  # Clear the buffer after sending
                else:
                    # Add new input to the buffer
                    partial_message += new_input

                # Show the prompt again after sending the message
                sys.stdout.write(f'{nickname}: {partial_message}')
                sys.stdout.flush()

run_client()
