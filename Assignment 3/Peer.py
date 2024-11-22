import json
import socket
import time
import uuid
import hashlib

class Peer:
    def __init__(self, host, port, name):
        self.host = host
        self.port = port
        self.name = name
        self.peers = set()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(5)
        self.blockchain = []

    def send_message(self, message, peer):
        try:
            self.sock.sendto(json.dumps(message).encode(), peer)
        except Exception as e:
            print(f"Failed to send message to {peer}: {e}")

    def receive_message(self):
        try:
            message, addr = self.sock.recvfrom(1024)
            return json.loads(message.decode()), addr
        except socket.timeout:
            return None, None
        except Exception as e:
            print(f"Error receiving message: {e}")
            return None, None

    def handle_gossip(self, data, addr):
        self.peers.add((data['host'], data['port']))
        self.send_message({
            "type": "GOSSIP_REPLY",
            "host": self.host,
            "port": self.port,
            "name": self.name
        }, (data['host'], data['port']))

    def handle_stats(self, addr):
        if not self.blockchain:
            height = 0
            hash_val = None
        else:
            height = len(self.blockchain) - 1
            hash_val = self.blockchain[-1]['hash']
        self.send_message({
            "type": "STATS_REPLY",
            "height": height,
            "hash": hash_val
        }, addr)

    def handle_get_block(self, data, addr):
        height = data.get('height')
        if height is not None and 0 <= height < len(self.blockchain):
            block = self.blockchain[height]
            self.send_message({
                "type": "GET_BLOCK_REPLY",
                **block
            }, addr)
        else:
            self.send_message({
                "type": "GET_BLOCK_REPLY",
                "height": None,
                "messages": None,
                "nonce": None,
                "minedBy": None
            }, addr)

    def perform_consensus(self):
        print("Performing consensus...")
        stats_responses = {}

        for peer in self.peers:
            self.send_message({"type": "STATS"}, peer)

        start_time = time.time()
        while time.time() - start_time < 10:
            message, addr = self.receive_message()
            if message and message['type'] == "STATS_REPLY":
                stats_responses[addr] = message

        if not stats_responses:
            print("No STATS responses received. Cannot perform consensus.")
            return None

        chain_stats = {}
        for response in stats_responses.values():
            key = (response['height'], response['hash'])
            chain_stats[key] = chain_stats.get(key, 0) + 1

        best_chain = max(chain_stats, key=chain_stats.get)
        print(f"Consensus determined chain: Height={best_chain[0]}, Hash={best_chain[1]}")
        return best_chain

    def fetch_block(self, height):
        for peer in self.peers:
            self.send_message({"type": "GET_BLOCK", "height": height}, peer)
            start_time = time.time()
            while time.time() - start_time < 5:
                message, addr = self.receive_message()
                if message and message['type'] == "GET_BLOCK_REPLY" and message['height'] == height:
                    print(f"Fetched block {height} from {addr}")
                    return message
        return None

    def fetch_blockchain(self, chain_height):
        print("Fetching blockchain...")
        blockchain = []
        for height in range(chain_height + 1):
            block = self.fetch_block(height)
            if block:
                blockchain.append(block)
            else:
                print(f"Failed to fetch block at height {height}")
                return None
        print("Successfully fetched the blockchain")
        return blockchain

    def validate_blockchain(self, blockchain):
        for i, block in enumerate(blockchain):
            if i == 0:
                continue
            calculated_hash = self.calculate_block_hash(block)
            if calculated_hash != block['hash']:
                print(f"Invalid hash for block {i}")
                return False
            if block['hash'] != blockchain[i - 1]['hash']:
                print(f"Invalid previous hash for block {i}")
                return False
        print("Blockchain is valid.")
        return True

    def calculate_block_hash(self, block):
        hashBase = hashlib.sha256()
        hashBase.update(block['previous_hash'].encode())
        hashBase.update(block['minedBy'].encode())
        for message in block['messages']:
            hashBase.update(message.encode())
        hashBase.update(block['timestamp'].to_bytes(8, 'big'))
        hashBase.update(block['nonce'].encode())
        return hashBase.hexdigest()

    def run(self):
        print(f"Peer running at {self.host}:{self.port} with name '{self.name}'")
        self.send_message({
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": str(uuid.uuid4()),
            "name": self.name
        }, ("eagle.cs.umanitoba.ca", 8999))

        while True:
            message, addr = self.receive_message()
            if message:
                if message['type'] == "GOSSIP":
                    self.handle_gossip(message, addr)
                elif message['type'] == "STATS":
                    self.handle_stats(addr)
                elif message['type'] == "GET_BLOCK":
                    self.handle_get_block(message, addr)
                elif message['type'] == "CONSENSUS":
                    self.perform_consensus()


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
