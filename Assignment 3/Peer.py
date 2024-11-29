import socket
import json
import time
import uuid
import logging

# Constants
RETRY_LIMIT = 20
FETCH_TIMEOUT = 120
RETRY_DELAY = 0.1

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


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
        self.sock.settimeout(1)
        self.fetching = True  # Only focus on fetching
        logging.info(f"Peer initialized on {self.host}:{self.port} with ID {self.id}")

    def send_message(self, message, destination):
        try:
            self.sock.sendto(json.dumps(message).encode(), destination)
            logging.info(f"Sent {message['type']} to {destination}")
        except Exception as e:
            logging.error(f"Failed to send {message['type']} to {destination}: {e}")

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

    def fetch_chain(self, target_height):
        logging.info(f"Fetching blockchain up to height {target_height}...")
        retries = {height: 0 for height in range(target_height + 1)}

        for height in range(target_height + 1):
            self.request_block(height)

        start_time = time.time()
        while len(self.pending_blocks) <= target_height:
            for height in range(target_height + 1):
                if height not in self.pending_blocks:
                    retries[height] += 1
                    if retries[height] > RETRY_LIMIT:
                        logging.error(f"Failed to fetch block at height {height}. Aborting.")
                        return False
                    logging.warning(f"Retrying block at height {height}...")
                    self.request_block(height)
                    time.sleep(RETRY_DELAY)

            if time.time() - start_time > FETCH_TIMEOUT:
                logging.error("Timeout while fetching blockchain. Fetch incomplete.")
                return False

        self.chain = [self.pending_blocks[height] for height in range(target_height + 1)]
        logging.info(f"Successfully fetched blockchain up to height {target_height}.")
        return True

    def handle_message(self, message, sender):
        if not self.fetching:
            logging.warning(f"Suppressed {message.get('type')} from {sender}.")
            return

        message_type = message.get("type")
        if message_type == "GET_BLOCK_REPLY":
            self.handle_get_block_reply(message)
        else:
            logging.info(f"Unhandled message type during fetch: {message_type}")

    def run(self):
        logging.info("Starting peer...")

        # Simulate best chain info (replace with actual consensus logic)
        best_chain = {"height": 50, "hash": "mocked_hash"}  # Mocked for demonstration

        success = self.fetch_chain(best_chain["height"])
        if not success:
            logging.error("Failed to fetch the complete blockchain.")
            return

        # Post-fetch handling
        self.fetching = False
        logging.info("Blockchain fetch complete. Ready for normal operation.")

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
