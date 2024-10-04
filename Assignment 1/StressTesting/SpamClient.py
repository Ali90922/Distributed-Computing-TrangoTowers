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

# Set the buffer size (adjust the size in bytes to what you need)
send_buffer_size = 16384 # You can adjust this to a higher value
recv_buffer_size = 34768  # You can adjust this to a higher value

# Set the socket options for the send and receive buffer sizes
client.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, send_buffer_size)
client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, recv_buffer_size)

client.connect(('130.179.28.122', 55456))
client.setblocking(False)  # Make the socket non-blocking

# Main loop to handle sending and receiving messages
def run_spam_client():
    counter = 0
    buffer = ""  # Buffer to accumulate partial messages
    nickname_sent = False  # To track if the nickname has been sent to the server already

    while True:
        sockets_list = [client]
        readable, _, _ = select.select(sockets_list, [], [], 0.01)

        for notified_socket in readable:
            try:
                data = notified_socket.recv(8192).decode('ascii')  # You can adjust the buffer size here too
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

        # Send the nickname only once when the client connects
        if not nickname_sent:
            try:
                client.send(nickname.encode('ascii'))
                nickname_sent = True  # Mark nickname as sent
            except:
                print("Failed to send nickname")
                client.close()
                sys.exit()

        # Send spam messages to the server
        message = f'Spam Message {counter}'
        try:
            client.send(message.encode('ascii'))
            print(f'Sent: {message}')
        except:
            print("Failed to send message")
            client.close()
            sys.exit()

        counter += 1
        time.sleep(0.07)  # Slowing down the spam rate to avoid overwhelming the server

run_spam_client()

