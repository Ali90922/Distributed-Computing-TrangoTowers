import socket
import select
import sys
import termios
import tty

# Check if the correct number of command-line arguments were provided
# Expecting the user to input the host IP as a command-line argument
if len(sys.argv) != 2:
    print("Usage: python client.py <HOST_IP>")
    sys.exit()

# Extract the host IP from the command-line argument
host = sys.argv[1]
port = 8547  # Hardcoded port number for the server connection

# Ask the user to choose a nickname that will be used in the chatroom
nickname = input("Choose a Nickname: ")

# Create a client socket (IPv4 + TCP) to connect to the chat server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    # Connect the client socket to the given host and port
    client.connect((host, port))
    client.setblocking(False)  # Set the socket to non-blocking mode
except Exception as e:
    # If there's any error during connection (e.g., wrong host), exit the program
    print(f"Could not connect to the server: {e}")
    sys.exit()

# Display the prompt with the nickname immediately after the nickname is chosen
sys.stdout.write(f'{nickname}: ')  # Shows the prompt in the format "nickname: "
sys.stdout.flush()  # Flush the buffer to ensure the prompt is displayed immediately

# Save the original terminal settings to restore later
orig_settings = termios.tcgetattr(sys.stdin)

# Function to run the chat client
def run_client():
    partial_message = ''  # Store what the user is currently typing but hasn't sent yet
    try:
        # Set the terminal to raw mode to read character by character without waiting for Enter
        tty.setcbreak(sys.stdin.fileno())
        
        # The main loop that will keep running the client
        while True:
            # Use select to monitor the client socket for incoming data
            sockets_list = [client]
            readable, _, _ = select.select(sockets_list, [], [], 0)  # No blocking

            # Handle any incoming messages from the server
            for notified_socket in readable:
                if notified_socket == client:
                    try:
                        # Receive the message from the server
                        message = client.recv(1024)
                        if not message:
                            # If no message (empty string), the server has shut down
                            print("\nServer has shut down or disconnected. Exiting...")
                            client.close()
                            sys.exit()  # Exit the program

                        # Try to decode the message, handling non-ASCII characters
                        try:
                            message = message.decode('ascii').strip()
                        except UnicodeDecodeError:
                            print("\nReceived malformed message (non-ASCII). Ignoring it.")
                            continue

                        # If the server requests a nickname (NICK), send the client's nickname
                        if message == 'NICK':
                            client.send(nickname.encode('ascii'))
                        else:
                            # Move the cursor to the start of the line, clear it, and display the new message
                            sys.stdout.write(f'\r\033[K{message}\n')  # \033[K clears the line
                            # Re-display the prompt with the current partial message
                            sys.stdout.write(f'{nickname}: {partial_message}')
                            sys.stdout.flush()
                    except socket.error as e:
                        # Handle socket errors (e.g., connection reset or closed)
                        print(f"\nSocket error: {e}")
                        client.close()
                        sys.exit()  # Exit the program on error
                    except Exception as e:
                        # Catch any other unexpected errors
                        print(f"\nAn unexpected error occurred: {e}")
                        client.close()
                        sys.exit()  # Exit the program

            # Non-blocking read from stdin (user input)
            dr, dw, de = select.select([sys.stdin], [], [], 0)
            if dr:
                # Read one character at a time from stdin
                char = sys.stdin.read(1)
                if char == '\n':  # If Enter is pressed
                    if partial_message.lower() == "quit":  # Check if the user typed 'quit'
                        # Inform the server that the user is leaving
                        client.send(f'{nickname} has left the chat.\n'.encode('ascii'))
                        print("\nExiting the chatroom...")
                        client.close()
                        sys.exit()  # Exit the program

                    # Send the message to the server (without the nickname)
                    client.send(partial_message.encode('ascii'))
                    partial_message = ''  # Reset the partial message
                    sys.stdout.write('\n' + f'{nickname}: ')  # Re-display the prompt
                    sys.stdout.flush()
                elif char == '\x7f':  # Handle backspace (Delete key)
                    if partial_message:
                        partial_message = partial_message[:-1]  # Remove the last character from the partial message
                        sys.stdout.write('\b \b')  # Erase the last character on the terminal
                        sys.stdout.flush()
                else:
                    # Add the character to the partial message and display it
                    partial_message += char
                    sys.stdout.write(char)
                    sys.stdout.flush()

    finally:
        # Restore the original terminal settings when the program exits
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)

# Run the client function
run_client()
