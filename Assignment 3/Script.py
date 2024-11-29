import socket
import pandas as pd

# List of well-known hosts and ports
well_known_hosts = [
    ("silicon.cs.umanitoba.ca", 8999),
    ("eagle.cs.umanitoba.ca", 8999),
    ("hawk.cs.umanitoba.ca", 8999),
    ("grebe.cs.umanitoba.ca", 8999),
    ("goose.cs.umanitoba.ca", 8999),
]

def check_host_availability(host, port, timeout=5):
    """
    Check if a UDP host is active by attempting to send a test packet.

    Args:
    host (str): The hostname or IP address of the host.
    port (int): The port number to check.
    timeout (int): Timeout in seconds for the connection.

    Returns:
    bool: True if the host is active, False otherwise.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.settimeout(timeout)
            message = b"TEST"
            udp_socket.sendto(message, (host, port))
            response, _ = udp_socket.recvfrom(1024)
            return True
    except (socket.timeout, socket.error):
        return False

# Test each host and print results
results = []
for host, port in well_known_hosts:
    is_active = check_host_availability(host, port)
    results.append((host, port, is_active))

# Print results in tabular format
results_df = pd.DataFrame(results, columns=["Host", "Port", "Is Active"])
print(results_df.to_string(index=False))
