import socket
import json
import threading
import time
import uuid
from Blockchain import Blockchain

class Peer:
    GOSSIP_INTERVAL = 30  # Seconds between gossip messages

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.name = "Ali Verstappen"
        self.peers = set()
        self.blockchain = Blockchain()

        # Create a UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(5)  # Timeout for socket operations

    def gossip(self):
        """Send gossip messages to peers."""
        message = {
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": str(uuid.uuid4()),
            "name": self.name,
        }
        for peer in list(self.peers):
            try:
                self.sock.sendto(json.dumps(message).encode(), peer)
                print(f"GOSSIP sent to {peer}")
            except Exception as e:
                print(f"Failed to send GOSSIP to {peer}: {e}")

    def join_network(self):
        """Join the network by gossiping to the well-known host."""
        well_known_host = ("eagle.cs.umanitoba.ca", 8999)
        message = {
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": str(uuid.uuid4()),
            "name": self.name,
        }
        try:
            self.sock.sendto(json.dumps(message).encode(), well_known_host)
            print(f"Sent GOSSIP to {well_known_host}")
        except Exception as e:
            print(f"Failed to send GOSSIP to {well_known_host}: {e}")

    def request_stats(self):
        """Request STATS from all peers."""
        stats_responses = {}
        message = {"type": "STATS"}

        for peer in list(self.peers):
            try:
                self.sock.sendto(json.dumps(message).encode(), peer)
                print(f"Sent STATS request to {peer}")
            except Exception as e:
                print(f"Failed to send STATS to {peer}: {e}")

            try:
                data, addr = self.sock.recvfrom(1024)  # Wait for a response
                response = json.loads(data.decode())
                if response["type"] == "STATS_REPLY":
                    stats_responses[addr] = response
            except socket.timeout:
                print(f"Timed out waiting for STATS reply from {peer}")
            except json.JSONDecodeError:
                print(f"Invalid JSON from {peer}")
        return stats_responses

    def find_most_agreed_chain(self, stats_responses):
        """Determine the most-agreed-upon chain from STATS responses."""
        chain_votes = {}  # (height, hash) -> count
        chain_peers = {}  # (height, hash) -> list of peers

        for peer, stats in stats_responses.items():
            chain_key = (stats["height"], stats["hash"])
            chain_votes[chain_key] = chain_votes.get(chain_key, 0) + 1
            chain_peers.setdefault(chain_key, []).append(peer)

        # Find the chain with the most votes
        most_agreed_chain = max(chain_votes, key=chain_votes.get, default=None)
        return most_agreed_chain, chain_peers.get(most_agreed_chain, [])

    def fetch_chain(self, chain_peers, height):
        """Fetch the full chain from peers."""
        downloaded_blocks = {}
        for block_height in range(height + 1):  # Download from 0 to height
            success = False
            for peer in chain_peers:
                message = {"type": "GET_BLOCK", "height": block_height}
                try:
                    self.sock.sendto(json.dumps(message).encode(), peer)
                    print(f"Sent GET_BLOCK request for height {block_height} to {peer}")

                    data, addr = self.sock.recvfrom(1024)
                    response = json.loads(data.decode())
                    if response["type"] == "GET_BLOCK_REPLY" and response["height"] == block_height:
                        downloaded_blocks[block_height] = response
                        success = True
                        break  # Stop asking once we get the block
                except socket.timeout:
                    print(f"Timed out waiting for block {block_height} from {peer}")
                except json.JSONDecodeError:
                    print(f"Invalid JSON received from {peer}")
            if not success:
                print(f"Failed to fetch block {block_height} from peers")
                return None
        return downloaded_blocks

    def validate_chain(self, blocks):
        """Validate the chain from genesis to the top."""
        for height, block in sorted(blocks.items()):
            if height > 0:
                previous_hash = blocks[height - 1]["hash"]
                calculated_hash = self.blockchain.calculate_hash(block, previous_hash)
                if block["hash"][:8] != "0" * 8 or block["hash"] != calculated_hash:
                    print(f"Invalid block at height {height}")
                    return False
        return True

    def replace_chain(self, new_blocks):
        """Replace the current chain with a new chain."""
        new_chain = [block for _, block in sorted(new_blocks.items())]
        self.blockchain.chain = new_chain
        print("Replaced local chain with the most-agreed-upon chain.")

    def perform_consensus(self):
        """Perform a full consensus operation."""
        print("Performing consensus...")
        stats_responses = self.request_stats()

        if not stats_responses:
            print("No STATS responses received. Cannot perform consensus.")
            return

        most_agreed_chain, chain_peers = self.find_most_agreed_chain(stats_responses)

        if not most_agreed_chain:
            print("No consensus found. Cannot perform consensus.")
            return

        height, _ = most_agreed_chain
        print(f"Most agreed-upon chain: height={height}")

        downloaded_blocks = self.fetch_chain(chain_peers, height)

        if downloaded_blocks is None:
            print("Failed to download the full chain.")
            return

        if not self.validate_chain(downloaded_blocks):
            print("Downloaded chain is invalid.")
            return

        print("Chain validated successfully. Updating local blockchain.")
        self.replace_chain(downloaded_blocks)

    def listen(self):
        """Listen for incoming messages."""
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = json.loads(data.decode())
                print(f"Received message from {addr}: {message}")
                self.peers.add(addr)
            except json.JSONDecodeError:
                print(f"Invalid JSON received from {addr}: {data.decode()}")
            except Exception as e:
                print(f"Error receiving message: {e}")

    def run(self):
        """Run the peer."""
        print(f"Peer running at {self.host}:{self.port} with name '{self.name}'")

        # Start listening for messages in a separate thread
        listener = threading.Thread(target=self.listen, daemon=True)
        listener.start()

        # Join the network
        self.join_network()

        # Perform consensus after joining
        self.perform_consensus()

        # Main loop for periodic gossiping
        while True:
            self.gossip()
            time.sleep(self.GOSSIP_INTERVAL)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python Peer.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    peer = Peer(host, port)
    peer.run()
