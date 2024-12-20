import socket
import json
import threading
import time
import uuid
import hashlib
import multiprocessing
import os
from BlockchainFetcher import BlockchainFetcher
from Blockchain import Blockchain


# Define the mining function outside the class to make it picklable
def mine_nonce_range(block_data, start_nonce, end_nonce, difficulty, result_queue):
    """Function to mine a nonce range."""
    pid = os.getpid()
    target = '0' * difficulty

    for nonce in range(start_nonce, end_nonce):
        # Check if a result has already been found
        if not result_queue.empty():
            return
        block_data['nonce'] = str(nonce)
        block_hash = hashlib.sha256(json.dumps(block_data, sort_keys=True).encode()).hexdigest()
        if block_hash.endswith(target):
            # Put the result in the queue
            result_queue.put((nonce, block_hash))
            print(f"Process {pid} found nonce: {nonce}, Hash: {block_hash}")
            return
        if nonce % 100000 == 0:
            print(f"Process {pid} still mining... Current nonce: {nonce}")


class Peer:
    GOSSIP_INTERVAL = 30  # Re-GOSSIP every 30 seconds
    MAX_PEERS_TO_GOSSIP = 3  # Repeat GOSSIP to 3 tracked peers

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.well_known_peers = [
            ("silicon.cs.umanitoba.ca", 8999),
            ("eagle.cs.umanitoba.ca", 8999),
            ("hawk.cs.umanitoba.ca", 8999),
        ]
        self.tracked_peers = set()  # Dynamically track peers
        self.blockchain = Blockchain()  # Initialize the blockchain
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.running = True
        self.gossip_seen = set()  # Keep track of seen GOSSIP IDs

        self.name = "Nico Rosberg"
        self.mining_enabled = True  # Flag to control mining

    # -------------------- Mining Methods --------------------

    def create_new_block(self, messages, miner_name):
        """Create a new block with messages and miner's name."""
        if len(messages) > self.blockchain.MAX_MESSAGES:
            raise ValueError("Too many messages. Maximum is {}".format(self.blockchain.MAX_MESSAGES))
        for msg in messages:
            if len(msg) > self.blockchain.MAX_MESSAGE_LENGTH:
                raise ValueError("Message exceeds maximum length of 20 characters.")

        new_block = {
            'type': 'GET_BLOCK_REPLY',
            'height': len(self.blockchain.chain),
            'messages': messages,
            'minedBy': miner_name,
            'nonce': '',  # To be determined during mining
            'timestamp': int(time.time()),
            'hash': ''  # To be determined during mining
        }
        return new_block

    def mine_block(self, block):
        """Mine the block to meet the difficulty requirement using multi-processing."""
        print(f"Mining block with height {block['height']} using multi-processing...")
        difficulty = self.blockchain.DIFFICULTY

        manager = multiprocessing.Manager()
        result_queue = manager.Queue()
        num_processes = multiprocessing.cpu_count()
        nonce_range_per_process = 1000000  # Adjust as needed

        # Prepare block data without the nonce and hash
        block_data = {
            'type': block['type'],
            'height': block['height'],
            'messages': block['messages'],
            'minedBy': block['minedBy'],
            'timestamp': block['timestamp']
        }

        processes = []
        start_nonce = 0
        found = False

        while not found and self.running and self.mining_enabled:
            processes = []  # Reset processes list each iteration
            for i in range(num_processes):
                process_start_nonce = start_nonce + i * nonce_range_per_process
                process_end_nonce = process_start_nonce + nonce_range_per_process
                p = multiprocessing.Process(
                    target=mine_nonce_range,
                    args=(block_data.copy(), process_start_nonce, process_end_nonce, difficulty, result_queue)
                )
                processes.append(p)
                p.start()

            # Wait for a result or processes to finish
            nonce_found = False
            while self.running and self.mining_enabled:
                if not result_queue.empty():
                    nonce, block_hash = result_queue.get()
                    nonce_found = True
                    found = True
                    break
                if all(not p.is_alive() for p in processes):
                    break
                time.sleep(0.1)

            # Terminate all processes
            for p in processes:
                p.terminate()
                p.join()

            if nonce_found:
                # Set the nonce and hash
                block['nonce'] = str(nonce)
                block['hash'] = block_hash
                print(f"Block mined! Nonce: {block['nonce']}, Hash: {block['hash']}")
                return block
            else:
                if self.mining_enabled:
                    print(f"Still mining... Checked nonces up to {start_nonce + num_processes * nonce_range_per_process}")
                start_nonce += num_processes * nonce_range_per_process

        return None

    def add_block(self, block):
        """Add a mined block to the blockchain."""
        if self.blockchain.is_valid_block(block, self.blockchain.chain[-1]):
            self.blockchain.chain.append(block)
            print(f"Block added to the blockchain! Height: {block['height']}, Hash: {block['hash']}")
            self.announce_block(block)
        else:
            print("Mined block is invalid and was not added.")

    def announce_block(self, block):
        """Announce the new block to peers."""
        message = {
            "type": "ANNOUNCE",
            "height": block['height'],
            "minedBy": block['minedBy'],
            "nonce": block['nonce'],
            "messages": block['messages'],
            "hash": block['hash'],
            "timestamp": block['timestamp']
        }
        peers_copy = list(self.tracked_peers)  # Prevent modification during iteration
        for peer in peers_copy:
            self.send_message(message, peer)
        print("Block announcement sent to peers.")

    def handle_announce(self, message):
        """Handle a block announcement from another peer."""
        block = {
            "height": message["height"],
            "minedBy": message["minedBy"],
            "nonce": message["nonce"],
            "messages": message["messages"],
            "hash": message["hash"],
            "timestamp": message["timestamp"],
        }
        if self.blockchain.is_valid_block(block, self.blockchain.chain[-1]):
            self.blockchain.chain.append(block)
            print(f"Block announced by {message['minedBy']} added to the blockchain.")
        else:
            print(f"Invalid block announced by {message['minedBy']} rejected.")

    # -------------------- Gossip Methods --------------------

    def send_gossip(self):
        """Send a GOSSIP message to well-known peers and tracked peers."""
        message_id = str(uuid.uuid4())
        gossip_message = {
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": message_id,
            "name": self.name,
        }

        # Send GOSSIP to well-known peers
        for peer in self.well_known_peers:
            self.send_message(gossip_message, peer)

        # Forward GOSSIP to tracked peers
        peers_copy = list(self.tracked_peers)
        for peer in peers_copy[:self.MAX_PEERS_TO_GOSSIP]:
            self.send_message(gossip_message, peer)

    def handle_gossip(self, message, addr):
        """Handle incoming GOSSIP messages."""
        gossip_id = message.get("id")
        if gossip_id in self.gossip_seen:
            return
        self.gossip_seen.add(gossip_id)
        self.tracked_peers.add((message["host"], message["port"]))

        # Reply to the sender with GOSSIP-REPLY
        gossip_reply = {
            "type": "GOSSIP_REPLY",
            "host": self.host,
            "port": self.port,
            "name": self.name,
        }
        self.send_message(gossip_reply, addr)

    def periodic_gossip(self):
        """Periodically send GOSSIP messages."""
        while self.running:
            self.send_gossip()
            time.sleep(self.GOSSIP_INTERVAL)

    # -------------------- Other Methods --------------------

    def get_peer_stats(self, peer_host, peer_port):
        """Get blockchain stats from a peer."""
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
        """Perform consensus by fetching blockchain stats from well-known peers."""
        # Temporarily pause mining while performing consensus
        self.mining_enabled = False

        try:
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

            # If our local chain is already as long or longer, no need to fetch
            if longest_chain_stats["height"] <= len(self.blockchain.chain) - 1:
                print("Local blockchain is already up to date or matches the longest chain.")
                return

            print(f"Peer {longest_chain_peer[0]}:{longest_chain_peer[1]} has the longest chain (height {longest_chain_stats['height']}). Fetching their blockchain...")

            # Clear local chain
            self.blockchain.chain = []

            # Prepare a list of all peers (well-known + tracked) for workload distribution
            all_peers = self.well_known_peers + list(self.tracked_peers)

            # Instantiate the fetcher and fetch all blocks
            fetcher = BlockchainFetcher(self.blockchain)
            fetcher.fetch_all_blocks(all_peers, longest_chain_peer, longest_chain_stats["height"])

            # Validate the fetched chain
            if self.blockchain.validate_fetched_chain(self.blockchain.chain):
                print(f"Consensus complete. Blockchain synchronized with height: {len(self.blockchain.chain) - 1}")
            else:
                print("Fetched blockchain is invalid. Keeping local blockchain.")
        finally:
            # Re-enable mining after consensus if still running
            if self.running:
                self.mining_enabled = True

    def handle_message(self, message, addr):
        """Handle incoming messages based on their type."""
        msg_type = message.get("type")

        if msg_type == "STATS":
            # Respond with local blockchain stats
            response = {
                "type": "STATS_REPLY",
                "height": len(self.blockchain.chain),
                "hash": self.blockchain.chain[-1]["hash"] if self.blockchain.chain else None,
            }
            print(f"Sending STATS_REPLY: {response}")
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

        elif msg_type == "GOSSIP":
            self.handle_gossip(message, addr)

        elif msg_type == "ANNOUNCE":
            self.handle_announce(message)

    def send_message(self, message, destination):
        """Send a JSON-encoded message to the given destination."""
        try:
            self.sock.sendto(json.dumps(message).encode(), destination)
        except Exception as e:
            print(f"Error sending message to {destination}: {e}")

    def listen(self):
        """Listen for incoming UDP messages."""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                message = json.loads(data.decode())
                self.handle_message(message, addr)
            except Exception as e:
                print(f"Error handling message: {e}")

    def start_mining_loop(self):
        """Continuously mine new blocks without user input."""
        while self.running:
            # If mining is disabled, wait until it's enabled again
            if not self.mining_enabled:
                time.sleep(1)
                continue

            messages = ["Jihan", "Park", "Mirha"]  # Example messages
            new_block = self.create_new_block(messages, self.name)
            mined_block = self.mine_block(new_block)
            if mined_block:
                self.add_block(mined_block)
            # Add a small delay to prevent rapid-fire mining loops
            time.sleep(1)

    def start(self):
        """Start the peer, including the listener thread and consensus process."""
        threading.Thread(target=self.listen, daemon=True).start()
        print(f"Peer started on {self.host}:{self.port}")

        threading.Thread(target=self.periodic_gossip, daemon=True).start()

        # Perform initial consensus
        print("Performing initial consensus...")
        self.perform_consensus()
        print("Initial consensus complete.")

        # Start mining automatically in a separate thread
        # so that the main thread can handle other tasks.
        threading.Thread(target=self.start_mining_loop, daemon=True).start()

        # Keep the main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the peer gracefully."""
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
    peer.start()
