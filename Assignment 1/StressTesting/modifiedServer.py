import socket
import select
import time
import sys
import psutil

host = '127.0.0.1'  # Update to the public IP of the server if needed
port = 55456

# Create a server socket (IPv4 + TCP)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1048576)  # 1MB

server.bind((host, port))
server.listen(500)  # Set the backlog to 500 to allow more pending connections

# Set server socket to non-blocking
server.setblocking(False)

# List of sockets to monitor for incoming data
sockets_list = [server]
clients = {}
nicknames = {}

# Performance tracking variables
message_count = 0
start_time = time.time()

# Total performance tracking variables
total_message_count = 0
server_start_time = time.time()

# Running flag to control the server loop
running = True

# Messages sent and received per client
client_stats = {}  # Key: client_socket, Value: {'sent': int, 'received': int}

# Initialize psutil process and network counters
process = psutil.Process()
net_counters = psutil.net_io_counters()

# Initialize cumulative stats for averages
total_cpu_usage = 0.0
total_memory_usage = 0.0
total_bytes_sent = 0
total_bytes_recv = 0
interval_count = 0

# Broadcast message to all connected clients
def broadcast(message, sender_socket=None):
    global message_count, total_message_count
    sender_nickname = nicknames.get(sender_socket, "Unknown")  # Get the nickname associated with the socket

    # Increment message counts
    message_count += 1
    total_message_count += 1
    # Update sender's sent message count
    if sender_socket in client_stats:
        client_stats[sender_socket]['sent'] += 1

    for client_socket in list(clients.keys()):
        try:
            client_socket.send((message + "\n").encode('ascii'))  # Ensure each message ends with a newline
            # Update receiver's received message count
            if client_socket != sender_socket and client_socket in client_stats:
                client_stats[client_socket]['received'] += 1
        except Exception as e:
            print(f"Error sending message to {clients.get(client_socket, 'Unknown')}: {e}")
            # Remove the client on failure
            if client_socket in sockets_list:
                sockets_list.remove(client_socket)
            if client_socket in clients:
                nickname = clients.pop(client_socket)
                print(f"Client {nickname} has been removed.")
            if client_socket in nicknames:
                nicknames.pop(client_socket)
            if client_socket in client_stats:
                client_stats.pop(client_socket)
            client_socket.close()
            # Avoid recursive call to broadcast
            # Optionally, notify remaining clients
            leave_message = f'{nickname} has left the chat.'
            print(leave_message)
            # You can choose to queue leave messages to be sent later to avoid recursion

# Main server loop to handle connections, data, and performance logging
def run_server():
    global running, message_count, start_time, total_cpu_usage, total_memory_usage
    global total_bytes_sent, total_bytes_recv, interval_count, total_message_count, net_counters

    print(f"Server is listening on {host}:{port}")

    interval = 5  # Log every 5 seconds
    last_log_time = time.time()

    while running:
        time_until_log = last_log_time + interval - time.time()
        timeout = max(0, time_until_log)

        try:
            read_sockets = sockets_list + [sys.stdin]
            readable, _, _ = select.select(read_sockets, [], [], timeout)
        except Exception as e:
            print(f"Select error: {e}")
            break

        for notified_socket in readable:
            if notified_socket == server:
                try:
                    client_socket, client_address = server.accept()
                    client_socket.setblocking(False)
                    sockets_list.append(client_socket)
                    clients[client_socket] = None  # Placeholder for the nickname
                    client_stats[client_socket] = {'sent': 0, 'received': 0}
                    client_socket.send("NICK\n".encode('ascii'))  # Ask for nickname
                except Exception as e:
                    print(f"Error accepting new connection: {e}")
            elif notified_socket == sys.stdin:
                command = sys.stdin.readline().strip().lower()
                if command == 'quit':
                    print("Shutdown command received. Shutting down the server.")
                    running = False
                    server.close()
                    break
            else:
                try:
                    message = notified_socket.recv(8192).decode('ascii').strip()
                    if not message:
                        raise Exception("Empty message")
                    if clients[notified_socket] is None:
                        nicknames[notified_socket] = message
                        clients[notified_socket] = message  # Set nickname
                        broadcast(f'{message} joined the chat!', notified_socket)
                    else:
                        broadcast(f"{clients[notified_socket]}: {message}", notified_socket)
                except Exception as e:
                    nickname = clients.get(notified_socket, "Unknown")
                    print(f"Error with client {nickname}: {e}")
                    # Remove the client on failure
                    if notified_socket in sockets_list:
                        sockets_list.remove(notified_socket)
                    if notified_socket in clients:
                        clients.pop(notified_socket)
                    if notified_socket in nicknames:
                        nicknames.pop(notified_socket)
                    if notified_socket in client_stats:
                        client_stats.pop(notified_socket)
                    notified_socket.close()
                    # Optionally, notify remaining clients
                    leave_message = f'{nickname} has left the chat.'
                    print(leave_message)
                    # You can choose to queue leave messages to be sent later to avoid recursion

        if time.time() - last_log_time >= interval:
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:
                mps = message_count / elapsed_time
                client_count = len(clients)

                cpu_usage = process.cpu_percent(interval=None)
                memory_info = process.memory_info()
                memory_usage = memory_info.rss / (1024 * 1024)

                new_net_counters = psutil.net_io_counters()
                bytes_sent = new_net_counters.bytes_sent - net_counters.bytes_sent
                bytes_recv = new_net_counters.bytes_recv - net_counters.bytes_recv
                net_counters = new_net_counters
                bytes_sent_mb = bytes_sent / (1024 * 1024)
                bytes_recv_mb = bytes_recv / (1024 * 1024)

                total_cpu_usage += cpu_usage
                total_memory_usage += memory_usage
                total_bytes_sent += bytes_sent
                total_bytes_recv += bytes_recv
                interval_count += 1

                print(f"\n[Performance Log]")
                print(f"Time Interval: {elapsed_time:.2f}s")
                print(f"Messages processed in interval: {message_count}")
                print(f"Messages per second: {mps:.2f}")
                print(f"Total clients connected: {client_count}")
                print(f"CPU Usage: {cpu_usage:.2f}%")
                print(f"Memory Usage: {memory_usage:.2f} MB")
                print(f"Bytes sent in interval: {bytes_sent_mb:.2f} MB")
                print(f"Bytes received in interval: {bytes_recv_mb:.2f} MB")
                print(f"Clients Stats:")
                for client_socket, stats in client_stats.items():
                    nickname = clients.get(client_socket, "Unknown")
                    sent = stats['sent']
                    received = stats['received']
                    print(f" - {nickname}: Sent: {sent}, Received: {received}")
                print("-" * 50)
                message_count = 0
                start_time = time.time()
                last_log_time = time.time()

    # Final performance log at shutdown
    total_elapsed_time = time.time() - server_start_time
    if total_elapsed_time > 0 and interval_count > 0:
        avg_mps = total_message_count / total_elapsed_time
        avg_cpu_usage = total_cpu_usage / interval_count
        avg_memory_usage = total_memory_usage / interval_count
        avg_bytes_sent_mb = (total_bytes_sent / interval_count) / (1024 * 1024)
        avg_bytes_recv_mb = (total_bytes_recv / interval_count) / (1024 * 1024)
    else:
        avg_mps = 0
        avg_cpu_usage = 0
        avg_memory_usage = 0
        avg_bytes_sent_mb = 0
        avg_bytes_recv_mb = 0

    print(f"\n[Final Performance Summary]")
    print(f"Total messages processed: {total_message_count}")
    print(f"Total elapsed time: {total_elapsed_time:.2f}s")
    print(f"Average messages per second: {avg_mps:.2f}")
    print(f"Average CPU Usage: {avg_cpu_usage:.2f}%")
    print(f"Average Memory Usage: {avg_memory_usage:.2f} MB")
    print(f"Average Bytes Sent per Interval: {avg_bytes_sent_mb:.2f} MB")
    print(f"Average Bytes Received per Interval: {avg_bytes_recv_mb:.2f} MB")

    for client_socket in clients.keys():
        client_socket.close()

run_server()
