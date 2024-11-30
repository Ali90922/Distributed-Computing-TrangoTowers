import hashlib
import json
import os
import time


class Blockchain:
    DIFFICULTY = 4  # Reduced difficulty for quicker testing

    def __init__(self, blockchain_file="blockchain.json"):
        self.chain = []
        self.blockchain_file = blockchain_file

        # Load blockchain from file or create a genesis block
        if os.path.exists(self.blockchain_file):
            self.load_from_file()
        else:
            self.chain = [self.create_genesis_block()]
            self.save_to_file()

    def create_genesis_block(self):
        """Create the first block in the chain (genesis block)."""
        return {
            "height": 0,
            "minedBy": "Genesis",
            "messages": [],
            "nonce": "0",
            "timestamp": int(time.time()),
            "hash": "0" * Blockchain.DIFFICULTY,
        }

    def hash_block(self, block):
        """Calculate the hash of a block."""
        hash_base = hashlib.sha256()
        # Hash depends on the previous block's hash (if not genesis)
        if block["height"] > 0:
            hash_base.update(self.chain[block["height"] - 1]["hash"].encode())
        hash_base.update(block["minedBy"].encode())
        for message in block["messages"]:
            hash_base.update(message.encode())
        hash_base.update(str(block["timestamp"]).encode())
        hash_base.update(block["nonce"].encode())
        return hash_base.hexdigest()

    def mine_block(self, miner_name, messages):
        """Mine a new block using proof-of-work."""
        block = {
            "height": len(self.chain),
            "minedBy": miner_name,
            "messages": messages[:10],  # Allow max 10 messages per block
            "nonce": "",
            "timestamp": int(time.time()),
        }
        while True:
            block["nonce"] = str(int(time.time() * 1000))  # A simple nonce generator
            block_hash = self.hash_block(block)
            if block_hash.startswith("0" * Blockchain.DIFFICULTY):
                block["hash"] = block_hash
                break
        return block

    def add_block(self, block):
        """Validate and add a block to the chain."""
        # Validate block height
        if block["height"] != len(self.chain):
            print(f"Block {block['height']} height mismatch. Expected {len(self.chain)}.")
            return False

        # Validate block hash
        if self.hash_block(block) != block["hash"]:
            print(f"Block {block['height']} hash mismatch.")
            return False

        self.chain.append(block)
        self.save_to_file()
        print(f"Block {block['height']} added successfully.")
        return True

    def validate_chain(self):
        """Validate the entire blockchain."""
        for i in range(1, len(self.chain)):
            # Verify each block's hash
            if self.hash_block(self.chain[i]) != self.chain[i]["hash"]:
                print(f"Blockchain validation failed at block {i}.")
                return False
        print("Blockchain validation succeeded.")
        return True

    def save_to_file(self):
        """Save the blockchain to a JSON file."""
        try:
            with open(self.blockchain_file, "w") as f:
                json.dump({"chain": self.chain}, f, indent=4)
            print(f"Blockchain saved to {self.blockchain_file}.")
        except Exception as e:
            print(f"Error saving blockchain: {e}")

    def load_from_file(self):
        """Load the blockchain from a JSON file."""
        try:
            with open(self.blockchain_file, "r") as f:
                data = json.load(f)
                self.chain = data.get("chain", [])
            print(f"Blockchain loaded from {self.blockchain_file}. Height: {len(self.chain) - 1}")
        except Exception as e:
            print(f"Error loading blockchain: {e}")

    def get_block(self, height):
        """Retrieve a specific block by its height."""
        if 0 <= height < len(self.chain):
            return self.chain[height]
        print(f"Block {height} not found.")
        return None

    def get_stats(self):
        """Return the height and hash of the latest block."""
        return {
            "height": len(self.chain) - 1,
            "hash": self.chain[-1]["hash"] if self.chain else None,
        }


if __name__ == "__main__":
    # Test the Blockchain class
    blockchain = Blockchain()

    # Display current stats
    print("Blockchain Stats:", blockchain.get_stats())

    # Mine a new block
    print("Mining a new block...")
    new_block = blockchain.mine_block("Alice", ["Hello", "Blockchain", "World"])
    blockchain.add_block(new_block)

    # Validate the blockchain
    blockchain.validate_chain()

    # Retrieve a specific block
    block = blockchain.get_block(1)
    if block:
        print("Block 1:", block)
