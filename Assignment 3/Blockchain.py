import hashlib
import json
import os
import time


class Blockchain:
    def __init__(self, blockchain_file="blockchain.json"):
        self.chain = []
        self.blockchain_file = blockchain_file

        # Load blockchain from file or initialize with genesis block
        if os.path.exists(self.blockchain_file):
            self.load_from_file()
        else:
            self.chain.append(self.create_genesis_block())
            self.save_to_file()

    def create_genesis_block(self):
        """Create the first block in the chain (genesis block)."""
        return {
            "height": 0,
            "minedBy": "Genesis",
            "messages": ["Welcome to the Blockchain!"],
            "nonce": "0",
            "timestamp": int(time.time()),
            "hash": "0" * 64,  # A dummy genesis hash
        }

    def add_block(self, block):
        """
        Add a new block to the blockchain.
        Args:
            block (dict): A block to add.
        """
        self.chain.append(block)
        print(f"Block {block['height']} added successfully.")
        self.save_to_file()

    def get_block_reply(self, height):
        """
        Retrieve a block in the `GET_BLOCK_REPLY` format.
        Args:
            height (int): The height of the block to retrieve.
        Returns:
            dict: A dictionary in `GET_BLOCK_REPLY` format or an error message if not found.
        """
        if 0 <= height < len(self.chain):
            block = self.chain[height]
            return {
                "type": "GET_BLOCK_REPLY",
                "hash": block["hash"],
                "height": block["height"],
                "messages": block["messages"],
                "minedBy": block["minedBy"],
                "nonce": block["nonce"],
                "timestamp": block["timestamp"],
            }
        return {"type": "GET_BLOCK_REPLY", "height": None, "error": "Block not found"}

    def validate_chain(self):
        """
        Validate the entire blockchain.
        Returns:
            bool: True if the chain is valid, False otherwise.
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block["height"] != i:
                print(f"Invalid height at block {i}.")
                return False
            if current_block.get("previous_hash") != previous_block["hash"]:
                print(f"Invalid chain at block {i}.")
                return False
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

    def get_stats(self):
        """
        Get the current stats of the blockchain.
        Returns:
            dict: The height and hash of the last block.
        """
        if not self.chain:
            return {"height": -1, "hash": None}
        last_block = self.chain[-1]
        return {"height": last_block["height"], "hash": last_block["hash"]}

    def __len__(self):
        """Get the length of the blockchain."""
        return len(self.chain)


if __name__ == "__main__":
    # Test the Blockchain class
    blockchain = Blockchain()

    # Display current stats
    print("Blockchain Stats:", blockchain.get_stats())

    # Add a block
    block = {
        "hash": "2483cc5c0d2fdbeeba3c942bde825270f345b2e9cd28f22d12ba347300000000",
        "height": 1,
        "messages": [
            "3010 rocks",
            "Warning:",
            "Procrastinators",
            "will be sent back",
            "in time to start",
            "early.",
        ],
        "minedBy": "Prof!",
        "nonce": "7965175207940",
        "timestamp": 1699293749,
    }
    blockchain.add_block(block)

    # Fetch block reply
    response = blockchain.get_block_reply(1)
    print("GET_BLOCK_REPLY:", response)

    # Validate the blockchain
    is_valid = blockchain.validate_chain()
    print(f"Blockchain is valid: {is_valid}")
