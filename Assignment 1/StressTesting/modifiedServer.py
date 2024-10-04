import socket
import select
import time
import sys
import psutil
import errno

host = '0.0.0.0'  # Update to the public IP of the server if needed
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

# Initialize psutil process and network counters
process = psutil.Process()
net_counters = psutil.net_io_counters()

# Initialize cumulative stats for averages
total_cpu_usage = 0.0
total_memory_usage = 0.0
total_bytes_sent = 0
total_bytes_recv = 0
total_packets_sent = 0
total_packets_recv = 0
interval_count = 0
total_load_avg = [0.0, 0.0, 0.0]
total_cpu_freq = 0.0

# Broadcast message to all connected clients
def broadcast(message, sender_socket=None):
    global message_count, total_message_count
    sender_nickname = nicknames.get(sender_socket, "Unknown")  # Get the nickname associated with the socket

    # Increment message counts
    message_count += 1
    total_message_count += 1

    for client_socket in list(clients.keys()):
        # Don't send the message back to the sender
        if client_socket == sender_socket:
            continue

        try:
            # Attempt to send the message
            client_socket.send((message + "\n").encode('ascii'))
        
        except socket.error as e:
            # If the socket buffer is full, skip and try later
            if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                print(f"Socket buffer full for {clients.get(client_socket, 'Unknown')}. Will retry later.")
                continue  # Skip sending to this client now and try again later
            
            # For other errors, handle disconnection
            else:
                print(f"Error sending message to {clients.get(client_socket, 'Unknown')}: {e}")
                remove_client(client_socket)  # Remove and clean up disconnected client

def remove_client(client_socket):
    """Function to remove a client and clean up its resources."""
    if client_socket in sockets_list:
        sockets_list.remove(client_socket)
    if client_socket in clients:
        nickname = clients.pop(client_socket)
        print(f"Client {nickname} has been removed.")
    if client_socket in nicknames:
        nicknames.pop(client_socket)
    client_socket.close()

    # Optionally, notify other clients of the disconnection
    leave_message = f'{nickname} has left the chat.'
    broadcast(leave_message)


# Main server loop to handle connections, data, and performance logging
def run_server():
    global running, message_count, start_time, total_cpu_usage, total_memory_usage
    global total_bytes_sent, total_bytes_recv, interval_count, total_message_count, net_counters
    global total_packets_sent, total_packets_recv, total_load_avg, total_cpu_freq

    print(f"Server is listening on {host}:{port}")

    interval = 5  # Log every 5 seconds
    last_log_time = time.time()

    while running:
        time_until_log = last_log_time + interval - time.time()
        timeout = 0.5

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
                    remove_client(notified_socket)

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
                packets_sent = new_net_counters.packets_sent - net_counters.packets_sent
                packets_recv = new_net_counters.packets_recv - net_counters.packets_recv
                net_counters = new_net_counters
                bytes_sent_mb = bytes_sent / (1024 * 1024)
                bytes_recv_mb = bytes_recv / (1024 * 1024)

                # System Load Average
                load_avg = psutil.getloadavg()  # Get system load (1m, 5m, 15m)
                total_load_avg = [x + y for x, y in zip(total_load_avg, load_avg)]  # Accumulate load averages

                # CPU Frequency
                cpu_freq = psutil.cpu_freq().current
                total_cpu_freq += cpu_freq

                total_cpu_usage += cpu_usage
                total_memory_usage += memory_usage
                total_bytes_sent += bytes_sent
                total_bytes_recv += bytes_recv
                total_packets_sent += packets_sent
                total_packets_recv += packets_recv
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
                print(f"Packets sent in interval: {packets_sent}")
                print(f"Packets received in interval: {packets_recv}")
                print(f"System Load (1m, 5m, 15m): {load_avg}")
                print(f"CPU Frequency: {cpu_freq:.2f} MHz")
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
        avg_packets_sent = total_packets_sent / interval_count
        avg_packets_recv = total_packets_recv / interval_count
        avg_cpu_freq = total_cpu_freq / interval_count
        avg_load_avg = [x / interval_count for x in total_load_avg]
    else:
        avg_mps = 0
        avg_cpu_usage = 0
        avg_memory_usage = 0
        avg_bytes_sent_mb = 0
        avg_bytes_recv_mb = 0
        avg_packets_sent = 0
        avg_packets_recv = 0
        avg_cpu_freq = 0
        avg_load_avg = [0, 0, 0]

    print(f"\n[Final Performance Summary]")
    print(f"Total messages processed: {total_message_count}")
    print(f"Total elapsed time: {total_elapsed_time:.2f}s")
    print(f"Average messages per second: {avg_mps:.2f}")
    print(f"Average CPU Usage: {avg_cpu_usage:.2f}%")
    print(f"Average Memory Usage: {avg_memory_usage:.2f} MB")
    print(f"Average Bytes Sent per Interval: {avg_bytes_sent_mb:.2f} MB")
    print(f"Average Bytes Received per Interval: {avg_bytes_recv_mb:.2f} MB")
    print(f"Average Packets Sent per Interval: {avg_packets_sent:.2f}")
    print(f"Average Packets Received per Interval: {avg_packets_recv:.2f}")
    print(f"Average CPU Frequency: {avg_cpu_freq:.2f} MHz")
    print(f"Average System Load (1m, 5m, 15m): {avg_load_avg}")
    
    for client_socket in clients.keys():
        client_socket.close()

run_server()
