import socket
import select
import sys
import termios
import tty

# Choose a nickname for the user
nickname = input("Choose a Nickname: ")

# Create a client socket (IPv4 + TCP)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 55456))
client.setblocking(False)  # Make the socket non-blocking

# Display the prompt with the nickname immediately after the nickname is chosen
sys.stdout.write(f'{nickname}: ')
sys.stdout.flush()

# Save the original terminal settings
orig_settings = termios.tcgetattr(sys.stdin)

def run_client():
    partial_message = ''  # Store what the user is currently typing
    try:
        # Set the terminal to raw mode to read character by character
        tty.setcbreak(sys.stdin.fileno())
        while True:
            # Use select to monitor the client socket
            sockets_list = [client]
            readable, _, _ = select.select(sockets_list, [], [], 0)

            # Handle incoming messages from the server
            for notified_socket in readable:
                if notified_socket == client:
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
                        print(f"\nAn error occurred: {e}")
                        client.close()
                        sys.exit()

            # Non-blocking read from stdin
            dr, dw, de = select.select([sys.stdin], [], [], 0)
            if dr:
                char = sys.stdin.read(1)
                if char == '\n':
                    # Send the message without including the nickname
                    client.send(partial_message.encode('ascii'))
                    partial_message = ''
                    sys.stdout.write('\n' + f'{nickname}: ')
                    sys.stdout.flush()
                elif char == '\x7f':  # Handle backspace (Delete key)
                    if partial_message:
                        partial_message = partial_message[:-1]
                        sys.stdout.write('\b \b')  # Erase the last character
                        sys.stdout.flush()
                else:
                    partial_message += char
                    sys.stdout.write(char)
                    sys.stdout.flush()

    finally:
        # Restore the original terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)

run_client()
# study the protocol