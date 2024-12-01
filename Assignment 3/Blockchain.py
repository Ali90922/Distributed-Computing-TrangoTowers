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
        """Create the predefined genesis block."""
        genesis_block = {
            'type': 'GET_BLOCK_REPLY',
            'height': 0,
            'messages': ['Keep it', 'simple.', 'Veni', 'vidi', 'vici'],
            'minedBy': 'Prof!',
            'nonce': '663135608617883',
            'timestamp': 1730910874,
            'hash': '75977fa09516d028befa0695e16c93be20271b66630236d38718e35700000000'
        }
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
        print(f"Validating block with height {block['height']} (previous block height {prev_block['height']})")
        if block['height'] == 0:  # Skip validation for genesis block
            return True
        if block['height'] != prev_block['height'] + 1:
            print(f"Invalid block height: {block['height']} (expected {prev_block['height'] + 1})")
            return False
        if prev_block['hash'] != block['hash']:
            print(f"Previous block hash mismatch: {prev_block['hash']} != {block['hash']}")
            return False
        if not block['hash'].endswith('0' * self.DIFFICULTY):
            print(f"Block hash does not meet difficulty: {block['hash']}")
            return False
        if self.calculate_hash(block) != block['hash']:
            print(f"Hash mismatch: calculated {self.calculate_hash(block)} != {block['hash']}")
            return False
        return True

    def validate_fetched_chain(self, fetched_chain):
        """
        Validate the entire fetched chain and print verification stats.
        """
        print(f"Local Genesis Block: {self.chain[0]}")
        print(f"Fetched Genesis Block: {fetched_chain[0]}")

        # Check if genesis blocks match
        if fetched_chain[0] != self.chain[0]:
            print("Fetched chain's genesis block does not match local genesis block!")
            return False

        valid = True
        for i in range(1, len(fetched_chain)):
            if not self.is_valid_block(fetched_chain[i], fetched_chain[i - 1]):
                print(f"Fetched chain is invalid at block {i} (Height: {fetched_chain[i]['height']})")
                valid = False
                break
        if valid:
            print("The entire fetched blockchain is verified successfully.")
            print(f"Blockchain Stats:")
            print(f"- Total Blocks: {len(fetched_chain)}")
            print(f"- Last Block Hash: {fetched_chain[-1]['hash']}")
            print(f"- Last Block Height: {fetched_chain[-1]['height']}")
            print(f"- Mined By: {fetched_chain[-1]['minedBy']}")
        return valid

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


if __name__ == "__main__":
    blockchain = Blockchain()

    # Simulate adding a block from an HTTP response
    response = '{"type": "GET_BLOCK_REPLY", "height": 1, "minedBy": "Prof!", "nonce": "4776171179467", "messages": ["test"], "hash": "5c25ae996e712fc8e93c10a1b9fd3b42dd408aaa65f4c3e4dfe8982800000000", "timestamp": 1730974785}'
    blockchain.add_block_from_response(response)

    # Print chain
    print(json.dumps(blockchain.get_chain(), indent=4))

    # Check stats
    print(blockchain.get_stats())
