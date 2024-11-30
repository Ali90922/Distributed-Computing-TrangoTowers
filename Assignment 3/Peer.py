import socket
import json
import threading
from BlockchainFetcher import BlockchainFetcher
from Blockchain import Blockchain


class Peer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.well_known_peers = [
            ("silicon.cs.umanitoba.ca", 8999),
            ("eagle.cs.umanitoba.ca", 8999),
            ("goose.cs.umanitoba.ca", 8999),
            ("hawk.cs.umanitoba.ca", 8999),
            ("goose.cs.umanitoba.ca", 8997),
        ]
        self.blockchain = Blockchain()  # Initialize the blockchain
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.running = True

    def get_peer_stats(self, peer_host, peer_port):
        """
        Get blockchain stats from a peer.
        """
        message = {"type": "STATS"}
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            sock.sendto(json.dumps(message).encode(), (peer_host, peer_port))
            response, _ = sock.recvfrom(4096)
            stats = json.loads(response.decode())
            return stats
        except socket.timeout:
            print(f"Timeout fetching stats from {peer_host}:{peer_port}.")
            return None
        except Exception as e:
            print(f"Error fetching stats from {peer_host}:{peer_port}: {e}")
            return None
        finally:
            sock.close()

    def perform_consensus(self):
        """
        Perform consensus by fetching blockchain stats from well-known peers,
        and replacing the local blockchain if a longer valid chain is found.
        """
        longest_chain_stats = None
        longest_chain_peer = None

        # Fetch stats from all well-known peers
        for peer_host, peer_port in self.well_known_peers:
            print(f"Fetching stats from {peer_host}:{peer_port}...")
            peer_stats = self.get_peer_stats(peer_host, peer_port)
            if not peer_stats:
                continue

            peer_height = peer_stats.get("height")
            if peer_height is not None:
                if not longest_chain_stats or peer_height > longest_chain_stats["height"]:
                    longest_chain_stats = peer_stats
                    longest_chain_peer = (peer_host, peer_port)

        # Check if a longer chain exists
        if not longest_chain_stats:
            print("Failed to find any valid peers with longer chains. Skipping consensus.")
            return

        if longest_chain_stats["height"] <= len(self.blockchain.chain) - 1:
            print("Local blockchain is already up to date or matches the longest chain.")
            return

        print(f"Peer {longest_chain_peer[0]}:{longest_chain_peer[1]} has the longest chain (height {longest_chain_stats['height']}). Fetching their blockchain...")

        # Clear local chain and fetch the longer one
        self.blockchain.chain = []
        fetcher = BlockchainFetcher(self.blockchain)
        fetcher.fetch_all_blocks(*longest_chain_peer)
        print(f"Consensus complete with blockchain height: {len(self.blockchain.chain) - 1}")

    def handle_message(self, message, addr):
        """
        Handle incoming messages based on their type.
        """
        msg_type = message.get("type")

        if msg_type == "STATS":
            # Respond with local blockchain stats
            response = self.blockchain.get_stats()
            self.send_message(response, addr)

        elif msg_type == "GET_BLOCK":
            # Return a specific block
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
            # Perform consensus triggered by an external request
            print("Performing consensus triggered by external request.")
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
