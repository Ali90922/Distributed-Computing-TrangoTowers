import socket
import json
import time
import uuid
import logging

# Constants for retries and timeouts
RETRY_LIMIT = 10
FETCH_TIMEOUT = 60  # Increased timeout for fetching
RETRY_DELAY = 0.05  # Delay between retries in seconds

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(message)s")


class Peer:
    def __init__(self, host, port, name):
        self.host = host
        self.port = port
        self.name = name
        self.id = str(uuid.uuid4())
        self.peers = [
            ("silicon.cs.umanitoba.ca", 8999),
            ("eagle.cs.umanitoba.ca", 8999),
            ("goose.cs.umanitoba.ca", 8999),
            ("hawk.cs.umanitoba.ca", 8999),
            ("goose.cs.umanitoba.ca", 8997),
        ]  # Reliable peers
        self.chain = []
        self.pending_blocks = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(2)  # Increased socket timeout
        self.fetching = False  # Indicates fetching phase
        logging.info(f"Peer initialized on {self.host}:{self.port} with ID {self.id}")

    def send_message(self, message, destination):
        try:
            self.sock.sendto(json.dumps(message).encode(), destination)
            logging.info(f"Sent {message['type']} to {destination}")
        except Exception as e:
            logging.error(f"Failed to send {message['type']} to {destination}: {e}")

    def gossip(self):
        """Send GOSSIP message to all peers."""
        message = {
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": self.id,
            "name": self.name,
        }
        for peer in self.peers:
            self.send_message(message, peer)
        logging.info("GOSSIP messages sent to all peers.")

    def handle_message(self, message, sender):
        message_type = message.get("type")

        # Suppress all non-blockchain-related messages during fetch
        if self.fetching and message_type != "GET_BLOCK_REPLY":
            logging.info(f"Suppressed {message_type} during blockchain fetch.")
            return

        logging.info(f"Received {message_type} from {sender}")

        if message_type == "GET_BLOCK_REPLY":
            self.handle_get_block_reply(message)
        elif message_type == "PING":
            self.handle_ping(sender)
        else:
            logging.warning(f"Unhandled message type: {message_type}")

    def handle_ping(self, sender):
        reply = {"type": "PONG", "host": self.host, "port": self.port}
        self.send_message(reply, sender)
        logging.info(f"Responded to PING from {sender}")

    def fetch_chain(self, best_chain):
        logging.info(f"Fetching blockchain up to height {best_chain['height']}...")
        self.fetching = True  # Block distractions during fetch
        retries = {height: 0 for height in range(best_chain["height"] + 1)}

        for height in range(best_chain["height"] + 1):
            self.request_block(height)

        self.build_chain(best_chain["height"], retries)
        self.fetching = False

    def request_block(self, height):
        message = {"type": "GET_BLOCK", "height": height}
        for peer in self.peers:
            self.send_message(message, peer)

    def handle_get_block_reply(self, message):
        height = message.get("height")
        if height is not None and height >= 0:
            if height not in self.pending_blocks:
                self.pending_blocks[height] = message
                logging.info(f"Received block at height {height}.")

    def build_chain(self, target_height, retries):
        start_time = time.time()
        while len(self.pending_blocks) <= target_height:
            for height in range(target_height + 1):
                if height not in self.pending_blocks:
                    retries[height] += 1
                    if retries[height] > RETRY_LIMIT:
                        logging.error(f"Failed to fetch block at height {height}. Aborting.")
                        return
                    logging.warning(f"Retrying block at height {height}...")
                    self.request_block(height)
                    time.sleep(RETRY_DELAY)

            if time.time() - start_time > FETCH_TIMEOUT:
                logging.error("Timeout while fetching blockchain. Fetch incomplete.")
                return

        # Ensure all blocks are fetched
        if sorted(self.pending_blocks.keys()) == list(range(target_height + 1)):
            self.chain = [self.pending_blocks[height] for height in sorted(self.pending_blocks)]
            logging.info(f"Successfully fetched blockchain up to height {target_height}.")
        else:
            missing_blocks = set(range(target_height + 1)) - self.pending_blocks.keys()
            logging.error(f"Missing blocks after fetch: {missing_blocks}")

    def run(self):
        logging.info("Starting peer...")
        self.gossip()

        # Simulate consensus to determine best chain (mocked height here)
        best_chain = {"height": 50, "hash": "mocked_hash"}  # Example mock best chain
        self.fetch_chain(best_chain)

        # Post-fetch operation (if needed)
        while True:
            try:
                data, sender = self.sock.recvfrom(1024)
                message = json.loads(data.decode())
                self.handle_message(message, sender)
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                logging.info("Shutting down peer.")
                break


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python Peer.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    name = "Ali Verstappen"

    peer = Peer(host, port, name)
    peer.run()
