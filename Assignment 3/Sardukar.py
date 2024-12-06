import socket
import json
import threading
import time
import uuid
import multiprocessing
from threading import Lock
from BlockchainFetcher import BlockchainFetcher
from Blockchain import Blockchain


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
        ]  # Removed goose.cs.umanitoba.ca
        self.tracked_peers = set()  # Dynamically track peers
        self.blockchain = Blockchain()  # Initialize the blockchain
        self.blockchain_lock = Lock()  # Lock for thread-safe blockchain access
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.running = True
        self.gossip_seen = set()  # Keep track of seen GOSSIP IDs

        self.name = "Baron Harkonen"

        self.CONSENSUS_INTERVAL = 60  # Perform consensus every 60 seconds

    # -------------------- Mining Methods --------------------

    def create_new_block(self, messages, miner_name):
        """Create a new block with messages and miner's name."""
        if len(messages) > self.blockchain.MAX_MESSAGES:
            raise ValueError("Too many messages. Maximum is {}".format(self.blockchain.MAX_MESSAGES))
        for msg in messages:
            if len(msg) > self.blockchain.MAX_MESSAGE_LENGTH:
                raise ValueError("Message exceeds maximum length of 20 characters.")

        with self.blockchain_lock:
            height = len(self.blockchain.chain)
        new_block = {
            'type': 'GET_BLOCK_REPLY',
            'height': height,
            'messages': messages,
            'minedBy': miner_name,
            'nonce': '',  # To be determined during mining
            'timestamp': int(time.time()),
            'hash': ''  # To be determined during mining
        }
        return new_block

    def mine_block(self, block):
        """Mine the block to meet the difficulty requirement using multiprocessing."""
        print(f"Mining block with height {block['height']} using multiprocessing...")

        num_processes = multiprocessing.cpu_count()
        print(f"Starting mining with {num_processes} processes...")
        manager = multiprocessing.Manager()
        return_dict = manager.dict()  # Shared dict to store the result
        stop_event = multiprocessing.Event()

        def worker(start_nonce, step, block, return_dict, stop_event):
            nonce = start_nonce
            while not stop_event.is_set():
                block_copy = block.copy()
                block_copy['nonce'] = str(nonce)
                block_copy['hash'] = self.blockchain.calculate_hash(block_copy)
                if block_copy['hash'].endswith('0' * self.blockchain.DIFFICULTY):
                    # Found a valid nonce
                    print(f"Process {multiprocessing.current_process().name} found nonce: {nonce}")
                    return_dict['block'] = block_copy
                    stop_event.set()
                    break
                nonce += step
                if nonce % 100000 == 0:
                    print(f"Process {multiprocessing.current_process().name} still mining... Current nonce: {nonce}")

        processes = []
        for i in range(num_processes):
            p = multiprocessing.Process(target=worker, args=(i, num_processes, block, return_dict, stop_event))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

        if 'block' in return_dict:
            print(f"Block mined! Nonce: {return_dict['block']['nonce']}, Hash: {return_dict['block']['hash']}")
            return return_dict['block']
        else:
            print("Failed to mine block.")
            return None

    def add_block(self, block):
        """Add a mined block to the blockchain."""
        with self.blockchain_lock:
            previous_block = self.blockchain.chain[-1] if self.blockchain.chain else None
            if self.blockchain.is_valid_block(block, previous_block):
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
        with self.blockchain_lock:
            # Check if the block is already in the chain
            if any(b['hash'] == block['hash'] for b in self.blockchain.chain):
                # Duplicate block, ignore
                return

            # Check if the block extends the current chain
            if block['height'] == len(self.blockchain.chain):
                previous_block = self.blockchain.chain[-1] if self.blockchain.chain else None
                if self.blockchain.is_valid_block(block, previous_block):
                    self.blockchain.chain.append(block)
                    print(f"Block announced by {message['minedBy']} added to the blockchain.")
                else:
                    print(f"Invalid block announced by {message['minedBy']} rejected.")
            else:
                # The announced block doesn't fit directly; trigger consensus
                print("Received a block that doesn't fit the current chain. Triggering consensus...")
                self.perform_consensus()

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
            # Duplicate GOSSIP, ignore
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

    # -------------------- Consensus Methods --------------------

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

        with self.blockchain_lock:
            local_height = len(self.blockchain.chain)
        if longest_chain_stats["height"] <= local_height - 1:
            print("Local blockchain is already up to date or matches the longest chain.")
            return

        print(f"Peer {longest_chain_peer[0]}:{longest_chain_peer[1]} has the longest chain (height {longest_chain_stats['height']}). Fetching their blockchain...")

        # Clear local chain and fetch the longer one
        with self.blockchain_lock:
            self.blockchain.chain = []
        fetcher = BlockchainFetcher(self.blockchain)
        fetcher.fetch_all_blocks(*longest_chain_peer)

        # Validate the fetched chain and print stats
        with self.blockchain_lock:
            fetched_chain = self.blockchain.chain
            is_valid = self.blockchain.validate_fetched_chain(fetched_chain)
        if is_valid:
            print(f"Consensus complete. Blockchain synchronized with height: {len(fetched_chain)}")
        else:
            print("Fetched blockchain is invalid. Keeping local blockchain.")

    def periodic_consensus(self):
        """Periodically perform consensus to synchronize with the network."""
        while self.running:
            time.sleep(self.CONSENSUS_INTERVAL)
            print("Performing periodic consensus...")
            self.perform_consensus()

    # -------------------- Other Methods --------------------

    def handle_message(self, message, addr):
        """Handle incoming messages based on their type."""
        msg_type = message.get("type")

        if msg_type == "STATS":
            # Respond with local blockchain stats
            with self.blockchain_lock:
                response = {
                    "type": "STATS_REPLY",
                    "height": len(self.blockchain.chain),
                    "hash": self.blockchain.chain[-1]["hash"] if self.blockchain.chain else None,
                }
            self.send_message(response, addr)

        elif msg_type == "GET_BLOCK":
            # Return a specific block
            height = message.get("height")
            with self.blockchain_lock:
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

    def is_chain_synced(self):
        """Check if the local chain height matches the network's height."""
        max_peer_height = self.get_max_peer_height()
        with self.blockchain_lock:
            local_height = len(self.blockchain.chain)
        return local_height >= max_peer_height

    def get_max_peer_height(self):
        """Get the maximum chain height among known peers."""
        max_height = 0
        for peer_host, peer_port in self.well_known_peers:
            peer_stats = self.get_peer_stats(peer_host, peer_port)
            if peer_stats and 'height' in peer_stats:
                if peer_stats['height'] > max_height:
                    max_height = peer_stats['height']
        return max_height

    def start(self):
        """Start the peer, including the listener thread and consensus process."""
        threading.Thread(target=self.listen, daemon=True).start()
        print(f"Peer started on {self.host}:{self.port}")

        threading.Thread(target=self.periodic_gossip, daemon=True).start()

        threading.Thread(target=self.periodic_consensus, daemon=True).start()

        # Perform initial consensus
        print("Performing initial consensus...")
        self.perform_consensus()
        print("Initial consensus complete.")

        # Continuous mining loop
        try:
            while self.running:
                # Check if local chain is synchronized before mining
                if self.is_chain_synced():
                    messages = ["Jihan", "Park", "Mirha"]  # Example messages
                    new_block = self.create_new_block(messages, self.name)
                    mined_block = self.mine_block(new_block)
                    if mined_block:
                        self.add_block(mined_block)
                else:
                    print("Local chain is not synchronized. Waiting before mining...")
                    time.sleep(self.CONSENSUS_INTERVAL)
        except KeyboardInterrupt:
            pass
        finally:
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