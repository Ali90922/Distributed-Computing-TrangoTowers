import socket
import select
import sys
import time

# Check if a nickname is provided via command line arguments
if len(sys.argv) < 2:
    print("Usage: python3 SpamClient.py <nickname>")
    sys.exit()

nickname = sys.argv[1]  # Use the first command-line argument as the nickname

# Create a client socket (IPv4 + TCP)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 55456))
client.setblocking(False)  # Make the socket non-blocking

# Main loop to handle sending and receiving messages
def run_spam_client():
    counter = 0
    buffer = ""  # Buffer to accumulate partial messages
    while True:
        sockets_list = [client]
        readable, _, _ = select.select(sockets_list, [], [], 0.01)

        for notified_socket in readable:
            try:
                data = notified_socket.recv(1024).decode('ascii')
                if data:
                    buffer += data  # Add received data to the buffer
                    if '\n' in buffer:
                        # Split messages at newline and process them
                        messages = buffer.split('\n')
                        for message in messages[:-1]:
                            print(message.strip())  # Print the complete message
                        buffer = messages[-1]  # Keep the last partial message
                else:
                    print("Connection closed by the server.")
                    client.close()
                    sys.exit()
            except:
                print("An error occurred!")
                client.close()
                sys.exit()

        # Send spam messages to the server
        message = f'{nickname}: Spam Message {counter}'
        try:
            client.send(message.encode('ascii'))
            print(f'Sent: {message}')
        except:
            print("Failed to send message")
            client.close()
            sys.exit()

        counter += 1
        time.sleep(0.01)  # Adjust the delay as needed for testing


run_spam_client()




# This version of the script is meant to be run with the bash scripting file !
