import socket
import select
import sys
import termios
import tty

# Check if the correct number of command-line arguments were provided
if len(sys.argv) != 2:
    print("Usage: python client.py <HOST_IP>")
    sys.exit()

host = sys.argv[1]
port = 8547

nickname = input("Choose a Nickname: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect((host, port))
    client.setblocking(False)
except Exception as e:
    print(f"Could not connect to the server: {e}")
    sys.exit()

sys.stdout.write(f'{nickname}: ')
sys.stdout.flush()

orig_settings = termios.tcgetattr(sys.stdin)

def run_client():
    partial_message = ''
    try:
        tty.setcbreak(sys.stdin.fileno())
        
        while True:
            sockets_list = [client]
            readable, _, _ = select.select(sockets_list, [], [], 0)

            for notified_socket in readable:
                if notified_socket == client:
                    try:
                        message = client.recv(1024)
                        if not message:
                            print("\nServer has shut down or disconnected. Exiting...")
                            client.close()
                            sys.exit()

                        message = message.decode('ascii').strip()

                        if message == 'NICK':
                            client.send(nickname.encode('ascii'))
                        else:
                            sys.stdout.write(f'\r\033[K{message}\n')
                            sys.stdout.write(f'{nickname}: {partial_message}')
                            sys.stdout.flush()
                    except Exception as e:
                        print(f"\nAn unexpected error occurred: {e}")
                        client.close()
                        sys.exit()

            dr, dw, de = select.select([sys.stdin], [], [], 0)
            if dr:
                char = sys.stdin.read(1)
                if char == '\n':
                    if partial_message.lower() == "quit":
                        client.send(f'{nickname} has left the chat.\n'.encode('ascii'))
                        print("\nExiting the chatroom...")
                        client.close()
                        sys.exit()

                    client.send(partial_message.encode('ascii'))  # Send only the message content
                    partial_message = ''
                    sys.stdout.write('\n' + f'{nickname}: ')
                    sys.stdout.flush()
                elif char == '\x7f':
                    if partial_message:
                        partial_message = partial_message[:-1]
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                else:
                    partial_message += char
                    sys.stdout.write(char)
                    sys.stdout.flush()

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)

run_client()
