import socket
import json
import time
import uuid
import hashlib


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
        self.fetching = False  # To prevent distractions during fetch

    def send_message(self, message, destination):
        try:
            self.sock.sendto(json.dumps(message).encode(), destination)
            print(f"Sent {message['type']} to {destination}")
        except Exception as e:
            print(f"Failed to send {message['type']} to {destination}: {e}")

    def gossip(self):
        message = {
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": self.id,
            "name": self.name,
        }
        for peer in self.peers:
            self.send_message(message, peer)

    def handle_message(self, message, sender):
        message_type = message.get("type")

        # Always respond to PING messages
        if message_type == "PING":
            self.handle_ping(sender)
            return

        # Ignore other messages if fetching blocks
        if self.fetching and message_type != "GET_BLOCK_REPLY":
            return

        if message_type == "GOSSIP":
            return  # Suppressed during fetch
        elif message_type == "STATS":
            return  # Suppressed during fetch
        elif message_type == "GET_BLOCK":
            return  # Suppressed during fetch
        elif message_type == "GET_BLOCK_REPLY":
            self.handle_get_block_reply(message)

    def handle_ping(self, sender):
        reply = {"type": "PONG", "host": self.host, "port": self.port}
        self.send_message(reply, sender)
        print(f"Responded to PING from {sender}")

    def perform_consensus(self):
        print("Performing consensus...")
        stats_responses = []

        for peer in self.peers:
            self.request_stats(peer)

        start_time = time.time()
        while time.time() - start_time < 5:
            try:
                response, _ = self.sock.recvfrom(1024)
                message = json.loads(response.decode())
                if message["type"] == "STATS_REPLY":
                    stats_responses.append(message)
            except socket.timeout:
                continue

        if not stats_responses:
            print("No STATS responses received. Cannot perform consensus.")
            return

        # Find the best chain (longest height and matching hash)
        best_chain = max(
            stats_responses,
            key=lambda x: (x["height"], x["hash"]),
        )
        print(
            f"Consensus determined chain: Height={best_chain['height']}, Hash={best_chain['hash']}"
        )
        self.fetch_chain(best_chain)

    def request_stats(self, peer):
        message = {"type": "STATS"}
        self.send_message(message, peer)

    def fetch_chain(self, best_chain):
        print(f"Fetching chain up to height {best_chain['height']}...")
        self.fetching = True  # Block distractions during fetch
        retries = {}

        for height in range(best_chain["height"] + 1):
            retries[height] = 0
            self.request_block(height)
            time.sleep(0.01)  # Small delay to allow message handling

        # Wait for replies and build the chain
        self.build_chain(best_chain["height"], retries)
        self.fetching = False  # Allow normal handling after fetch

    def request_block(self, height):
        message = {"type": "GET_BLOCK", "height": height}
        for peer in self.peers:
            self.send_message(message, peer)

    def handle_get_block_reply(self, message):
        height = message.get("height")
        if height is not None and height >= 0:
            self.pending_blocks[height] = message
            print(f"Received block at height {height}.")

    def build_chain(self, target_height, retries):
        start_time = time.time()
        while len(self.pending_blocks) <= target_height:
            for height in range(target_height + 1):
                if height not in self.pending_blocks:
                    retries[height] += 1
                    if retries[height] > 3:  # Retry limit
                        print(f"Failed to fetch block at height {height}. Aborting.")
                        return
                    print(f"Block at height {height} missing, retrying...")
                    self.request_block(height)

            # Timeout mechanism
            if time.time() - start_time > 30:  # Stop after 30 seconds
                print("Timeout while fetching blockchain.")
                return

        # Build the full chain
        self.chain = [self.pending_blocks[height] for height in sorted(self.pending_blocks)]
        print(f"Successfully fetched blockchain up to height {target_height}.")

    def run(self):
        self.gossip()
        self.perform_consensus()

        while True:
            try:
                data, sender = self.sock.recvfrom(1024)
                message = json.loads(data.decode())
                self.handle_message(message, sender)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error handling message: {e}")


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
