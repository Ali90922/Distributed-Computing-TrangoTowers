import socket
import json
import time
import uuid
import hashlib
import random

class Peer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.name = "Ali Verstappen"  # Hardcoded name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.peers = []  # List of known peers
        self.blockchain = []  # Local copy of the blockchain
        self.consensus_target = None

    def gossip(self):
        message = {
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": str(uuid.uuid4()),
            "name": self.name,
        }
        for peer in random.sample(self.peers, min(3, len(self.peers))):
            self.sock.sendto(json.dumps(message).encode(), peer)

    def perform_consensus(self):
        print("Performing consensus...")
        stats_responses = []
        for peer in self.peers:
            self.request_stats(peer)

        time.sleep(1)  # Allow some time for responses

        for _ in range(len(self.peers)):
            try:
                response, _ = self.sock.recvfrom(1024)
                message = json.loads(response.decode())
                if message["type"] == "STATS_REPLY":
                    stats_responses.append((message["height"], message["hash"]))
            except socket.timeout:
                continue

        if stats_responses:
            most_common_chain = max(
                stats_responses, key=lambda x: stats_responses.count(x)
            )
            self.consensus_target = most_common_chain
            print(
                f"Consensus determined chain: Height={most_common_chain[0]}, Hash={most_common_chain[1]}"
            )
            self.fetch_blockchain(most_common_chain[0])
        else:
            print("No STATS responses received. Cannot perform consensus.")

    def fetch_blockchain(self, target_height):
        print(f"Fetching blockchain up to height {target_height}...")
        new_blockchain = []
        for height in range(target_height + 1):
            block = self.get_block(height)
            if block:
                new_blockchain.append(block)
            else:
                print(f"Failed to fetch block at height {height}. Retrying...")
                block = self.get_block(height)  # Retry once
                if block:
                    new_blockchain.append(block)
                else:
                    print(f"Block at height {height} is still missing.")
                    return False

        if self.validate_chain(new_blockchain):
            self.blockchain = new_blockchain
            print("Blockchain successfully synchronized.")
            return True
        else:
            print("Fetched blockchain is invalid. Aborting synchronization.")
            return False

    def get_block(self, height):
        message = {"type": "GET_BLOCK", "height": height}
        for peer in self.peers:
            self.sock.sendto(json.dumps(message).encode(), peer)
            try:
                response, _ = self.sock.recvfrom(1024)
                block = json.loads(response.decode())
                if block["type"] == "GET_BLOCK_REPLY" and block["height"] == height:
                    return block
            except socket.timeout:
                continue
        return None

    def request_stats(self, peer):
        message = {"type": "STATS"}
        self.sock.sendto(json.dumps(message).encode(), peer)

    def validate_chain(self, chain):
        for i in range(1, len(chain)):
            prev_block = chain[i - 1]
            current_block = chain[i]
            if current_block["hash"][:8] != "00000000":
                print(f"Block {i} has insufficient difficulty.")
                return False
            if current_block["hash"] != self.compute_hash(current_block):
                print(f"Block {i} hash mismatch.")
                return False
            if current_block["hash"] != prev_block["hash"]:
                print(f"Block {i} does not chain to previous block.")
                return False
        return True

    def compute_hash(self, block):
        hashBase = hashlib.sha256()
        hashBase.update(block["hash"].encode())
        hashBase.update(block["minedBy"].encode())
        for m in block["messages"]:
            hashBase.update(m.encode())
        hashBase.update(block["timestamp"].to_bytes(8, "big"))
        hashBase.update(block["nonce"].encode())
        return hashBase.hexdigest()

    def run(self):
        print(f"Peer running at {self.host}:{self.port} with name '{self.name}'")
        self.perform_consensus()
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = json.loads(data.decode())
                if message["type"] == "GOSSIP":
                    self.handle_gossip(message, addr)
                elif message["type"] == "STATS":
                    self.handle_stats_request(addr)
                elif message["type"] == "GET_BLOCK":
                    self.handle_get_block(message, addr)
            except Exception as e:
                print(f"Error: {e}")

    def handle_gossip(self, message, addr):
        print(f"Received GOSSIP from {addr}: {message}")
        reply = {
            "type": "GOSSIP_REPLY",
            "host": self.host,
            "port": self.port,
            "name": self.name,
        }
        self.sock.sendto(json.dumps(reply).encode(), (message["host"], message["port"]))
        if (message["host"], message["port"]) not in self.peers:
            self.peers.append((message["host"], message["port"]))

    def handle_stats_request(self, addr):
        stats = {
            "type": "STATS_REPLY",
            "height": len(self.blockchain) - 1,
            "hash": self.blockchain[-1]["hash"] if self.blockchain else None,
        }
        self.sock.sendto(json.dumps(stats).encode(), addr)

    def handle_get_block(self, message, addr):
        height = message.get("height")
        if 0 <= height < len(self.blockchain):
            block = self.blockchain[height]
            reply = {
                "type": "GET_BLOCK_REPLY",
                "height": block["height"],
                "hash": block["hash"],
                "messages": block["messages"],
                "minedBy": block["minedBy"],
                "nonce": block["nonce"],
                "timestamp": block["timestamp"],
            }
        else:
            reply = {
                "type": "GET_BLOCK_REPLY",
                "height": None,
                "hash": None,
                "messages": None,
                "minedBy": None,
                "nonce": None,
                "timestamp": None,
            }
        self.sock.sendto(json.dumps(reply).encode(), addr)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python Peer.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    peer = Peer(host, port)
    peer.run()
