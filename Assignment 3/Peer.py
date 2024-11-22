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
        self.peers = [("eagle.cs.umanitoba.ca", 8999)]  # Well-known peers
        self.chain = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(1)

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
        if message_type == "GOSSIP":
            self.handle_gossip(message, sender)
        elif message_type == "STATS":
            self.handle_stats_request(sender)
        elif message_type == "GET_BLOCK":
            self.handle_get_block(message, sender)
        elif message_type == "GET_BLOCK_REPLY":
            self.handle_get_block_reply(message)

    def handle_gossip(self, message, sender):
        if sender not in self.peers:
            self.peers.append(sender)
        reply = {
            "type": "GOSSIP_REPLY",
            "host": self.host,
            "port": self.port,
            "name": self.name,
        }
        self.send_message(reply, (message["host"], message["port"]))

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
        for height in range(best_chain["height"] + 1):
            self.request_block(height)

        # Wait for replies and build the chain
        self.build_chain(best_chain["height"])

    def request_block(self, height):
        message = {"type": "GET_BLOCK", "height": height}
        for peer in self.peers:
            self.send_message(message, peer)

    def handle_stats_request(self, sender):
        if self.chain:
            last_block = self.chain[-1]
            reply = {
                "type": "STATS_REPLY",
                "height": len(self.chain) - 1,
                "hash": last_block["hash"],
            }
        else:
            reply = {"type": "STATS_REPLY", "height": 0, "hash": None}
        self.send_message(reply, sender)

    def handle_get_block(self, message, sender):
        height = message.get("height")
        if height is None or height >= len(self.chain):
            reply = {
                "type": "GET_BLOCK_REPLY",
                "height": None,
                "messages": None,
                "nonce": None,
                "minedBy": None,
            }
        else:
            block = self.chain[height]
            reply = {
                "type": "GET_BLOCK_REPLY",
                "height": height,
                "messages": block["messages"],
                "nonce": block["nonce"],
                "minedBy": block["minedBy"],
                "hash": block["hash"],
                "timestamp": block["timestamp"],
            }
        self.send_message(reply, sender)

    def handle_get_block_reply(self, message):
        height = message.get("height")
        if height is not None and height >= 0:
            self.chain.append(message)
            print(f"Added block at height {height} to chain.")

    def build_chain(self, target_height):
        # Verify blocks and rebuild the chain
        self.chain.sort(key=lambda x: x["height"])  # Ensure blocks are in order
        for i in range(len(self.chain)):
            block = self.chain[i]
            if not self.validate_block(block, i):
                print(f"Invalid block detected at height {i}.")
                self.chain = []  # Reset chain on invalid block
                return
        print(f"Chain successfully rebuilt to height {target_height}.")

    def validate_block(self, block, height):
        if height == 0:  # Genesis block
            return True
        # Validate hash and previous hash chaining
        previous_hash = self.chain[height - 1]["hash"]
        expected_hash = self.compute_block_hash(block, previous_hash)
        return block["hash"] == expected_hash

    def compute_block_hash(self, block, previous_hash):
        hash_base = hashlib.sha256()
        hash_base.update(previous_hash.encode())
        hash_base.update(block["minedBy"].encode())
        for msg in block["messages"]:
            hash_base.update(msg.encode())
        hash_base.update(block["timestamp"].to_bytes(8, "big"))
        hash_base.update(block["nonce"].encode())
        return hash_base.hexdigest()

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
