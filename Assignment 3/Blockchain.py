import hashlib
import time
import json


class Blockchain:
    DIFFICULTY = 8  # Difficulty level for proof-of-work
    MAX_MESSAGES = 10
    MAX_MESSAGE_LENGTH = 20
    MAX_NONCE_LENGTH = 40

    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """Create the genesis block (the first block of the chain)."""
        genesis_block = {
            'height': 0,
            'messages': ["Genesis Block"],
            'minedBy': "System",
            'nonce': "0",
            'timestamp': int(time.time()),
            'hash': None,
        }
        genesis_block['hash'] = self.calculate_hash(genesis_block)
        self.chain.append(genesis_block)

    def calculate_hash(self, block):
        """Calculate the hash for a block."""
        hash_base = hashlib.sha256()
        # Add previous block's hash
        if block['height'] > 0:
            last_hash = self.chain[block['height'] - 1]['hash']
            hash_base.update(last_hash.encode())
        # Add miner name
        hash_base.update(block['minedBy'].encode())
        # Add messages
        for msg in block['messages']:
            hash_base.update(msg.encode())
        # Add timestamp
        hash_base.update(block['timestamp'].to_bytes(8, 'big'))
        # Add nonce
        hash_base.update(block['nonce'].encode())
        return hash_base.hexdigest()

    def is_valid_block(self, block, prev_block):
        """Check if a block is valid."""
        if block['height'] != prev_block['height'] + 1:
            return False
        if prev_block['hash'] != block['hash']:
            return False
        if not block['hash'].endswith('0' * self.DIFFICULTY):
            return False
        if self.calculate_hash(block) != block['hash']:
            return False
        return True

    def add_block_from_response(self, response):
        """Add a block to the blockchain from a GET_BLOCK_REPLY response."""
        try:
            block = json.loads(response)
            if block["type"] != "GET_BLOCK_REPLY" or block["height"] is None:
                raise ValueError("Invalid block data.")
            
            if len(self.chain) > 0:
                prev_block = self.chain[-1]
                if not self.is_valid_block(block, prev_block):
                    raise ValueError("Block is invalid or does not match chain.")
            self.chain.append(block)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error adding block from response: {e}")

    def validate_chain(self):
        """Validate the entire blockchain."""
        for i in range(1, len(self.chain)):
            if not self.is_valid_block(self.chain[i], self.chain[i - 1]):
                return False
        return True

    def get_chain(self):
        """Get the entire blockchain."""
        return self.chain

    def get_stats(self):
        """Get statistics about the blockchain."""
        if not self.chain:
            return {"height": 0, "hash": None}
        return {"height": len(self.chain) - 1, "hash": self.chain[-1]['hash']}


# Example usage
if __name__ == "__main__":
    blockchain = Blockchain()

    # Simulate adding a block from an HTTP response
    response = '{"type": "GET_BLOCK_REPLY", "height": 1, "minedBy": "Prof!", "nonce": "4776171179467", "messages": ["test"], "hash": "5c25ae996e712fc8e93c10a1b9fd3b42dd408aaa65f4c3e4dfe8982800000000", "timestamp": 1730974785}'
    blockchain.add_block_from_response(response)

    # Print chain
    print(json.dumps(blockchain.get_chain(), indent=4))

    # Check stats
    print(blockchain.get_stats())
