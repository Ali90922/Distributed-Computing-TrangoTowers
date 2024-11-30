import socket
import json
import threading
import argparse
from Blockchain import Blockchain
from BlockchainFetcher import BlockchainFetcher


class Peer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.peers = {
            ("goose.cs.umanitoba.ca", 8999),
            ("eagle.cs.umanitoba.ca", 8999),
            ("silicon.cs.umanitoba.ca", 8999),
            ("hawk.cs.umanitoba.ca", 8999),
        }  # Well-known peers
        self.blockchain = Blockchain()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))

    def send_message(self, message, destination):
        """Send a JSON-encoded message to the given destination."""
        try:
            self.sock.sendto(json.dumps(message).encode(), destination)
            print(f"Sent {message['type']} to {destination}")
        except Exception as e:
            print(f"Failed to send {message['type']} to {destination}: {e}")

    def handle_message(self, message, addr):
        """Process incoming messages."""
        if message["type"] == "GOSSIP":
            self.peers.add((message["host"], message["port"]))
            return {
                "type": "GOSSIP_REPLY",
                "host": self.host,
                "port": self.port,
                "name": f"Peer_{self.host}_{self.port}"
            }

        elif message["type"] == "STATS":
            return self.blockchain.get_stats()

        elif message["type"] == "GET_BLOCK":
            height = message.get("height")
            if 0 <= height < len(self.blockchain.chain):
                return self.blockchain.chain[height]
            return {"type": "GET_BLOCK_REPLY", "height": None}

        elif message["type"] == "CONSENSUS":
            self.perform_consensus()
            return {"type": "CONSENSUS_REPLY", "status": "triggered"}

        return None

    def perform_consensus(self):
        """Fetch the blockchain from peers using BlockchainFetcher."""
        if not self.peers:
            print("No dynamic peers found. Falling back to well-known peers.")
            self.peers = {
                ("goose.cs.umanitoba.ca", 8999),
                ("eagle.cs.umanitoba.ca", 8999),
                ("silicon.cs.umanitoba.ca", 8999),
                ("hawk.cs.umanitoba.ca", 8999),
            }

        print(f"Available peers for consensus: {self.peers}")
        if not self.peers:
            print("Still no peers available for consensus.")
            return

        # Fetch chains from available peers using BlockchainFetcher
        longest_chain = None
        for peer_host, peer_port in self.peers:
            print(f"Fetching blockchain from {peer_host}:{peer_port}...")
            fetcher = BlockchainFetcher(peer_host, peer_port)
            fetched_chain = fetcher.run()

            if fetched_chain is None:
                print(f"Failed to fetch chain from {peer_host}:{peer_port}.")
                continue

            # Validate and compare chains
            fetched_blockchain = Blockchain()
            fetched_blockchain.chain = fetched_chain
            if fetched_blockchain.validate_chain():
                if longest_chain is None or len(fetched_blockchain.chain) > len(longest_chain.chain):
                    longest_chain = fetched_blockchain
                    print(f"New longest valid chain from {peer_host}:{peer_port}.")

        # Replace local chain if a longer valid chain is found
        if longest_chain and len(longest_chain.chain) > len(self.blockchain.chain):
            self.blockchain = longest_chain
            print(f"Replaced local chain with fetched chain of height {len(self.blockchain.chain) - 1}.")
        else:
            print("Consensus completed. No valid longer chain found.")

    def listen(self):
        """Listen for incoming UDP messages."""
        while True:
            try:
                data, addr = self.sock.recvfrom(4096)
                message = json.loads(data.decode())
                print(f"Received {message['type']} from {addr}")

                # Handle the message
                response = self.handle_message(message, addr)
                if response:
                    self.send_message(response, addr)

            except Exception as e:
                print(f"Error handling message: {e}")

    def run(self):
        """Start the peer."""
        print(f"Peer started on {self.host}:{self.port}")
        threading.Thread(target=self.listen, daemon=True).start()

        while True:
            command = input("Enter command (gossip, stats, mine, consensus, exit): ").strip().lower()
            if command == "gossip":
                message = {
                    "type": "GOSSIP",
                    "host": self.host,
                    "port": self.port
                }
                for peer in self.peers:
                    self.send_message(message, peer)

            elif command == "stats":
                print(self.blockchain.get_stats())

            elif command == "mine":
                miner_name = input("Enter miner name: ")
                messages = input("Enter messages (comma-separated): ").split(",")
                block = self.blockchain.mine_block(miner_name, messages)
                self.blockchain.add_block(block)
                print(f"Mined new block: {block}")

            elif command == "consensus":
                self.perform_consensus()

            elif command == "exit":
                print("Shutting down peer...")
                break

            else:
                print("Unknown command.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Blockchain Peer")
    parser.add_argument("--host", required=True, help="Host for the peer")
    parser.add_argument("--port", type=int, required=True, help="Port for the peer")
    args = parser.parse_args()

    peer = Peer(args.host, args.port)
    peer.run()
