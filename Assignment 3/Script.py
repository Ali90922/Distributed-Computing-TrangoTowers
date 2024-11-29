import socket
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# List of well-known hosts and ports
PEERS = [
    ("silicon.cs.umanitoba.ca", 8999),
    ("eagle.cs.umanitoba.ca", 8999),
    ("goose.cs.umanitoba.ca", 8999),
    ("hawk.cs.umanitoba.ca", 8999),
    ("goose.cs.umanitoba.ca", 8997),
]


def is_host_active(host, port, timeout=1):
    """
    Check if a host is active by attempting a TCP connection.
    Returns True if successful, False otherwise.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def ping_hosts(peers):
    """
    Ping a list of hosts and report their status.
    """
    logging.info("Pinging well-known hosts...")
    for host, port in peers:
        active = is_host_active(host, port)
        status = "ACTIVE" if active else "INACTIVE"
        logging.info(f"Host: {host}:{port} is {status}")


if __name__ == "__main__":
    ping_hosts(PEERS)
