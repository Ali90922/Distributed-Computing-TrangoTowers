import sys
import json
import socket
import time
import uuid
import hashlib

class Peer:
    def __init__(self, host, port, name="Ali Verstappen"):
        self.host = host
        self.port = int(port)
        self.name = name
        self.peers = []
        self.blockchain = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.fetching_chain = False
        self.last_gossip_time = time.time()

    def run(self):
        print(f"Peer running at {self.host}:{self.port} with name '{self.name}'")
        self.gossip()
        self.perform_consensus()

        while True:
            # Process incoming messages
            try:
                self.sock.settimeout(0.5)
                message, address = self.sock.recvfrom(1024)
                data = json.loads(message.decode())
                self.handle_message(data, address)
            except socket.timeout:
                pass  # No incoming messages, proceed with other tasks
            except Exception as e:
                print(f"Error handling message: {e}")

            # Check if fetching blockchain is pending
            if self.fetching_chain:
                self.fetch_chain()
                self.fetching_chain = False

    def gossip(self):
        message = {
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": str(uuid.uuid4()),
            "name": self.name,
        }
        well_known_peer = ("eagle.cs.umanitoba.ca", 8999)
        self.sock.sendto(json.dumps(message).encode(), well_known_peer)
        print(f"Sent GOSSIP to {well_known_peer}")

    def perform_consensus(self):
        print("Performing consensus...")
        self.fetching_chain = True

    def fetch_chain(self):
        print("Fetching blockchain...")
        max_height = 0
        target_hash = None

        # Request STATS from peers
        for peer in self.peers:
            stats_request = {"type": "STATS"}
            self.sock.sendto(json.dumps(stats_request).encode(), peer)
        
        # Wait for STATS replies and determine the longest chain
        time.sleep(1)  # Allow some time for replies to arrive
        for peer in self.peers:
            if peer.get("height", 0) > max_height:
                max_height = peer["height"]
                target_hash = peer["hash"]
        
        if max_height == 0:
            print("No valid chains received during consensus.")
            return
        
        print(f"Consensus determined chain: Height={max_height}, Hash={target_hash}")

        # Fetch blocks for the determined chain
        for height in range(max_height + 1):
            block_request = {"type": "GET_BLOCK", "height": height}
            for peer in self.peers:
                self.sock.sendto(json.dumps(block_request).encode(), peer)
                try:
                    response, _ = self.sock.recvfrom(1024)
                    block = json.loads(response.decode())
                    if block.get("type") == "GET_BLOCK_REPLY":
                        self.blockchain.append(block)
                        print(f"Added block at height {block['height']} to chain.")
                except socket.timeout:
                    print(f"Timeout while fetching block at height {height}.")

    def handle_message(self, message, address):
        if message["type"] == "GOSSIP":
            self.handle_gossip(message, address)
        elif message["type"] == "STATS":
            self.handle_stats(message, address)
        elif message["type"] == "GET_BLOCK":
            self.handle_get_block(message, address)
        else:
            print(f"Unknown message type: {message['type']}")

    def handle_gossip(self, message, address):
        current_time = time.time()
        if current_time - self.last_gossip_time > 1:  # 1-second delay between replies
            reply = {
                "type": "GOSSIP_REPLY",
                "host": self.host,
                "port": self.port,
                "name": self.name,
            }
            self.sock.sendto(json.dumps(reply).encode(), (message["host"], message["port"]))
            print(f"Sent GOSSIP_REPLY to {address}")
            self.last_gossip_time = current_time

    def handle_stats(self, message, address):
        stats_reply = {
            "type": "STATS_REPLY",
            "height": len(self.blockchain),
            "hash": self.blockchain[-1]["hash"] if self.blockchain else None,
        }
        self.sock.sendto(json.dumps(stats_reply).encode(), address)
        print(f"Sent STATS_REPLY to {address}")

    def handle_get_block(self, message, address):
        height = message.get("height")
        if height is not None and 0 <= height < len(self.blockchain):
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
        self.sock.sendto(json.dumps(reply).encode(), address)
        print(f"Sent GET_BLOCK_REPLY to {address}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python Peer.py <host> <port>")
        sys.exit(1)
    
    host = sys.argv[1]
    port = sys.argv[2]
    peer = Peer(host, port)
    peer.run()
