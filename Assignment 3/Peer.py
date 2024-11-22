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
        self.peers = [("eagle.cs.umanitoba.ca", 8999)]  # Include the eagle peer as a known host
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
        # Gossip to all known peers
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
        # Add other message handlers as needed

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

        # Determine the chain with the highest height
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
        for height in range(best_chain["height"] + 1):
            self.request_block(height)

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
