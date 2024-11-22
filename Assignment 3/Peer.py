import socket
import json
import sys
import time
import threading
import uuid
from blockchain import Blockchain
from message_handler import handle_message


class Peer:
    GOSSIP_INTERVAL = 30  # Gossip every 30 seconds

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.peers = set()  # List of known peers
        self.blockchain = Blockchain()  # Initialize blockchain
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(5)

    def join_network(self):
        """Send an initial GOSSIP message to the well-known host."""
        well_known_host = ("eagle.cs.umanitoba.ca", 8999)
        message = {
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": str(uuid.uuid4()),
            "name": f"Peer_{self.host}_{self.port}"
        }
        self.sock.sendto(json.dumps(message).encode(), well_known_host)
        print(f"Sent GOSSIP to well-known host {well_known_host}")

    def gossip(self):
        """Send GOSSIP messages to known peers."""
        message = {
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": str(uuid.uuid4()),
            "name": f"Peer_{self.host}_{self.port}"
        }
        for peer in list(self.peers)[:3]:  # Send to up to 3 peers
            try:
                self.sock.sendto(json.dumps(message).encode(), peer)
                print(f"Sent GOSSIP to {peer}")
            except Exception as e:
                print(f"Failed to send GOSSIP to {peer}: {e}")

    def listen(self):
        """Listen for incoming messages."""
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = json.loads(data.decode())
                response = handle_message(message, self, addr)
                if response:
                    self.sock.sendto(json.dumps(response).encode(), addr)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error handling message: {e}")

    def run(self):
        """Run the peer."""
        print(f"Peer running at {self.host}:{self.port}")
        # Start listening for messages
        listener = threading.Thread(target=self.listen, daemon=True)
        listener.start()

        # Join the network
        self.join_network()

        # Main loop for gossiping
        while True:
            self.gossip()
            time.sleep(self.GOSSIP_INTERVAL)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python Peer.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    peer = Peer(host, port)
    peer.run()
