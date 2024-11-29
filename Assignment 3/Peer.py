import socket
import json
import time
import uuid
import logging

# Constants
RETRY_LIMIT = 20
FETCH_TIMEOUT = 300  # Increased timeout for longer chains
RETRY_DELAY = 0.1
MAX_RETRY_DELAY = 5  # Maximum retry delay
CHUNK_SIZE = 20  # Number of blocks to fetch in each chunk

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
            ("hawk.cs.umanitoba.ca", 8999),
            ("grebe.cs.umanitoba.ca", 8999),
            ("goose.cs.umanitoba.ca", 8999),
        ]
        self.chain = []
        self.pending_blocks = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(1)
        self.fetching = True  # Focus only on fetching initially
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
        logging.info(f"Fetching blockchain up to height {target_height} in chunks of {CHUNK_SIZE}...")
        retries = {height: 0 for height in range(target_height + 1)}
        start_time = time.time()

        for start_height in range(0, target_height + 1, CHUNK_SIZE):
            end_height = min(start_height + CHUNK_SIZE - 1, target_height)
            logging.info(f"Fetching blocks {start_height} to {end_height}...")

            for height in range(start_height, end_height + 1):
                self.request_block(height)

            while len(self.pending_blocks) <= end_height:
                for height in range(start_height, end_height + 1):
                    if height not in self.pending_blocks:
                        retries[height] += 1
                        if retries[height] > RETRY_LIMIT:
                            logging.error(f"Failed to fetch block at height {height}. Aborting.")
                            return False
                        logging.warning(f"Retrying block at height {height}...")
                        self.request_block(height)
                        time.sleep(self.get_retry_delay(retries[height]))

                if time.time() - start_time > FETCH_TIMEOUT:
                    logging.error("Timeout while fetching blockchain. Fetch incomplete.")
                    return False

        self.chain = [self.pending_blocks[height] for height in range(target_height + 1)]
        logging.info(f"Successfully fetched blockchain up to height {target_height}.")
        return True

    def validate_chain(self):
        logging.info("Validating fetched blockchain...")
        for i in range(1, len(self.chain)):
            prev_hash = self.chain[i - 1]["hash"]
            current_hash = self.chain[i]["hash"]

            # Check if the current block references the correct previous hash
            if self.chain[i]["prev_hash"] != prev_hash:
                logging.error(f"Invalid chain at height {i}: mismatched hashes.")
                return False

        logging.info("Blockchain validation successful.")
        return True

    def get_retry_delay(self, attempt):
        return min(RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)

    def handle_gossip(self, message, sender):
        peer_info = (message["host"], message["port"])
        if peer_info not in self.peers:
            self.peers.append(peer_info)
            logging.info(f"Added new peer: {peer_info}")

    def handle_message(self, message, sender):
        if not self.fetching:
            logging.warning(f"Suppressed {message.get('type')} from {sender}.")
            return

        message_type = message.get("type")
        if message_type == "GET_BLOCK_REPLY":
            self.handle_get_block_reply(message)
        elif message_type == "GOSSIP":
            self.handle_gossip(message, sender)
        else:
            logging.info(f"Unhandled message type during fetch: {message_type}")

    def run(self):
        logging.info("Starting peer...")

        # Simulate best chain info (replace with actual consensus logic)
        best_chain = {"height": 50, "hash": "mocked_hash"}  # Mocked for demonstration

        success = self.fetch_chain(best_chain["height"])
        if not success or not self.validate_chain():
            logging.error("Failed to fetch or validate the blockchain.")
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
