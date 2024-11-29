import socket
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler("host_status.log"),
        logging.StreamHandler()
    ],
)

# List of well-known hosts and ports
PEERS = [
    ("silicon.cs.umanitoba.ca", 8999),
    ("eagle.cs.umanitoba.ca", 8999),
    ("goose.cs.umanitoba.ca", 8999),
    ("hawk.cs.umanitoba.ca", 8999),
    ("goose.cs.umanitoba.ca", 8997),
]

RETRY_COUNT = 3
TIMEOUT = 1


def is_host_active(host, port, timeout=TIMEOUT):
    """
    Check if a host is active by attempting a TCP connection.
    Returns True if successful, False otherwise.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def check_host(host, port):
    """
    Check the status of a host with retries.
    """
    for attempt in range(RETRY_COUNT):
        if is_host_active(host, port):
            logging.info(f"Host: {host}:{port} is ACTIVE (Attempt {attempt + 1})")
            return "ACTIVE"
        logging.debug(f"Host: {host}:{port} is INACTIVE (Attempt {attempt + 1})")
    logging.info(f"Host: {host}:{port} is INACTIVE after {RETRY_COUNT} attempts")
    return "INACTIVE"


def ping_hosts(peers):
    """
    Ping a list of hosts and report their status.
    """
    logging.info("Pinging well-known hosts...")
    results = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(check_host, host, port) for host, port in peers]
        for future in futures:
            results.append(future.result())
    
    # Generate a summary
    active_count = results.count("ACTIVE")
    inactive_count = results.count("INACTIVE")
    logging.info("Summary:")
    logging.info(f"Total Hosts: {len(peers)}")
    logging.info(f"Active Hosts: {active_count}")
    logging.info(f"Inactive Hosts: {inactive_count}")


if __name__ == "__main__":
    ping_hosts(PEERS)
