import socket
import json
import sys
import time
import threading
import uuid
from Blockchain import Blockchain
from message_handler import handle_message

class Peer:
    GOSSIP_INTERVAL = 30  # Gossip every 30 seconds

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.peers = set()  # List of known peers
        self.blockchain = Blockchain()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(5)

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
            self.sock.sendto(json.dumps(message).encode(), peer)

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
        listener = threading.Thread(target=self.listen, daemon=True)
        listener.start()

        while True:
            self.gossip()
            time.sleep(self.GOSSIP_INTERVAL)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python peer.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    peer = Peer(host, port)
    peer.run()

