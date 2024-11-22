import socket
import json
import time
import uuid


class Peer:
    def __init__(self, host, port, name="Ali Verstappen"):
        self.host = host
        self.port = port
        self.name = name
        self.peers = set()  # Known peers
        self.blockchain = []  # Local blockchain
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(5)  # Set timeout for receiving messages

    def run(self):
        print(f"Peer running at {self.host}:{self.port} with name '{self.name}'")
        self.gossip()
        self.perform_consensus()
        while True:
            try:
                data, sender = self.sock.recvfrom(1024)
                message = json.loads(data)
                self.handle_message(message, sender)
            except socket.timeout:
                print("Error receiving message: timed out")
            except Exception as e:
                print(f"Error receiving message: {e}")

    def gossip(self):
        message = {
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": str(uuid.uuid4()),
            "name": self.name,
        }
        for peer in self.peers:
            try:
                self.sock.sendto(json.dumps(message).encode(), peer)
                print(f"GOSSIP sent to {peer}")
            except Exception as e:
                print(f"Failed to send GOSSIP to {peer}: {e}")

    def handle_message(self, message, sender):
        msg_type = message.get("type")
        if msg_type == "GOSSIP":
            print(f"Received GOSSIP from {sender}: {message}")
            self.peers.add((message["host"], message["port"]))
            reply = {"type": "GOSSIP_REPLY", "host": self.host, "port": self.port, "name": self.name}
            self.sock.sendto(json.dumps(reply).encode(), sender)
        elif msg_type == "GOSSIP_REPLY":
            print(f"Received GOSSIP_REPLY from {sender}: {message}")
            self.peers.add((message["host"], message["port"]))
        elif msg_type == "STATS":
            print(f"Received STATS request from {sender}")
            response = {
                "type": "STATS_REPLY",
                "height": len(self.blockchain),
                "hash": self.hash_block(self.blockchain[-1]) if self.blockchain else None,
            }
            self.sock.sendto(json.dumps(response).encode(), sender)
        elif msg_type == "GET_BLOCK":
            block_height = message.get("height")
            if 0 <= block_height < len(self.blockchain):
                block = self.blockchain[block_height]
                response = {"type": "GET_BLOCK_REPLY", "block": block}
                self.sock.sendto(json.dumps(response).encode(), sender)
        elif msg_type == "GET_BLOCK_REPLY":
            print(f"Received block from {sender}: {message}")
        elif msg_type == "STATS_REPLY":
            print(f"Received STATS_REPLY from {sender}: {message}")

    def perform_consensus(self):
        print("Performing consensus...")
        stats_responses = []

        # Step 1: Send STATS to all peers
        for peer in self.peers:
            try:
                message = {"type": "STATS"}
                self.sock.sendto(json.dumps(message).encode(), peer)
                print(f"Sent STATS to {peer}")
            except Exception as e:
                print(f"Failed to send STATS to {peer}: {e}")

        # Step 2: Collect STATS_REPLY responses
        start_time = time.time()
        while time.time() - start_time < 5:  # Wait for 5 seconds
            try:
                data, sender = self.sock.recvfrom(1024)
                message = json.loads(data)
                if message.get("type") == "STATS_REPLY":
                    stats_responses.append((sender, message))
            except socket.timeout:
                break

        if not stats_responses:
            print("No STATS responses received. Cannot perform consensus.")
            return

        # Step 3: Determine the longest chain
        longest_chain_peer = max(stats_responses, key=lambda x: x[1]["height"])
        target_peer = longest_chain_peer[0]
        target_height = longest_chain_peer[1]["height"]
        print(f"Longest chain found at {target_peer} with height {target_height}")

        # Step 4: Fetch blocks
        self.blockchain = []
        for height in range(target_height):
            block = None
            for peer, stats in stats_responses:
                try:
                    message = {"type": "GET_BLOCK", "height": height}
                    self.sock.sendto(json.dumps(message).encode(), peer)
                    data, sender = self.sock.recvfrom(1024)
                    response = json.loads(data)
                    if response.get("type") == "GET_BLOCK_REPLY":
                        block = response["block"]
                        break
                except Exception as e:
                    print(f"Failed to fetch block {height} from {peer}: {e}")

            if block:
                self.blockchain.append(block)
            else:
                print(f"Block {height} not found. Consensus failed.")
                return

        # Step 5: Verify blockchain
        if self.verify_blockchain():
            print("Blockchain successfully loaded and verified.")
        else:
            print("Blockchain verification failed.")

    def verify_blockchain(self):
        for i in range(1, len(self.blockchain)):
            prev_block = self.blockchain[i - 1]
            current_block = self.blockchain[i]
            if current_block["previous_hash"] != self.hash_block(prev_block):
                return False
            if not self.validate_proof_of_work(current_block):
                return False
        return True

    def hash_block(self, block):
        return json.dumps(block, sort_keys=True)

    def validate_proof_of_work(self, block):
        difficulty = block.get("difficulty", 1)
        block_hash = self.hash_block(block)
        return block_hash.startswith("0" * difficulty)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python Peer.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    peer = Peer(host, port)
    peer.run()
