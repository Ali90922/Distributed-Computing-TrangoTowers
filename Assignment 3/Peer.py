import socket
import json
import threading
from BlockchainFetcher import BlockchainFetcher
from Blockchain import Blockchain


class Peer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.peers = {
            ("goose.cs.umanitoba.ca", 8999),
            ("eagle.cs.umanitoba.ca", 8999),
            ("silicon.cs.umanitoba.ca", 8999),
            ("hawk.cs.umanitoba.ca", 8999),
        }
        self.blockchain = Blockchain()  # Initialize the blockchain
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.running = True

    def perform_consensus(self):
        """
        Fetch the blockchain from peers using BlockchainFetcher and update local blockchain.
        """
        fetcher = BlockchainFetcher(self.blockchain)
        fetcher.fetch_all_blocks()  # Fetch and update the blockchain

    def handle_message(self, message, addr):
        """
        Handle incoming messages based on their type.
        """
        msg_type = message.get("type")

        if msg_type == "STATS":
            response = self.blockchain.get_stats()
            self.send_message(response, addr)

        elif msg_type == "GET_BLOCK":
            height = message.get("height")
            if height is not None and 0 <= height < len(self.blockchain.chain):
                block = self.blockchain.chain[height]
                response = {
                    "type": "GET_BLOCK_REPLY",
                    **block
                }
            else:
                response = {
                    "type": "GET_BLOCK_REPLY",
                    "height": None,
                    "messages": None,
                    "minedBy": None,
                    "nonce": None,
                    "hash": None,
                    "timestamp": None
                }
            self.send_message(response, addr)

        elif msg_type == "CONSENSUS":
            self.perform_consensus()

    def send_message(self, message, destination):
        """
        Send a JSON-encoded message to the given destination.
        """
        try:
            self.sock.sendto(json.dumps(message).encode(), destination)
        except Exception as e:
            print(f"Error sending message to {destination}: {e}")

    def listen(self):
        """
        Listen for incoming UDP messages.
        """
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                message = json.loads(data.decode())
                self.handle_message(message, addr)
            except Exception as e:
                print(f"Error handling message: {e}")

    def start(self):
        """
        Start the peer, including the listener thread and consensus process.
        """
        # Start listening in a separate thread
        threading.Thread(target=self.listen, daemon=True).start()
        print(f"Peer started on {self.host}:{self.port}")

        # Perform initial consensus to synchronize blockchain
        print("Performing initial consensus...")
        self.perform_consensus()
        print("Initial consensus complete.")

    def stop(self):
        """
        Stop the peer gracefully.
        """
        self.running = False
        self.sock.close()
        print("Peer stopped.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Blockchain Peer")
    parser.add_argument("--host", required=True, help="Host for the peer")
    parser.add_argument("--port", type=int, required=True, help="Port for the peer")
    args = parser.parse_args()

    peer = Peer(args.host, args.port)
    try:
        peer.start()
        while True:
            command = input("Enter 'stop' to stop the peer: ").strip().lower()
            if command == "stop":
                break
    finally:
        peer.stop()
