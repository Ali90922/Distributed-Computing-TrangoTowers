import hashlib
import time

class Blockchain:
    DIFFICULTY = 8

    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        """Create the first block in the chain."""
        return {
            "height": 0,
            "minedBy": "Genesis",
            "messages": [],
            "nonce": "0",
            "timestamp": int(time.time()),
            "hash": "0" * Blockchain.DIFFICULTY
        }

    def hash_block(self, block):
        """Calculate the hash of a block."""
        hash_base = hashlib.sha256()
        if block["height"] > 0:
            hash_base.update(self.chain[block["height"] - 1]["hash"].encode())
        hash_base.update(block["minedBy"].encode())
        for message in block["messages"]:
            hash_base.update(message.encode())
        hash_base.update(block["timestamp"].to_bytes(8, "big"))
        hash_base.update(block["nonce"].encode())
        return hash_base.hexdigest()

    def mine_block(self, miner_name, messages):
        """Mine a block with proof-of-work."""
        block = {
            "height": len(self.chain),
            "minedBy": miner_name,
            "messages": messages[:10],  # Max 10 messages
            "nonce": "",
            "timestamp": int(time.time())
        }
        while True:
            block["nonce"] = str(int(time.time() * 1000))  # Simple nonce
            block_hash = self.hash_block(block)
            if block_hash.startswith("0" * Blockchain.DIFFICULTY):
                block["hash"] = block_hash
                break
        return block

    def add_block(self, block):
        """Validate and add a block to the chain."""
        if block["height"] != len(self.chain):
            return False
        if self.hash_block(block) != block["hash"]:
            return False
        self.chain.append(block)
        return True

    def validate_chain(self):
        """Validate the entire blockchain."""
        for i in range(1, len(self.chain)):
            if self.hash_block(self.chain[i]) != self.chain[i]["hash"]:
                return False
        return True

    def get_stats(self):
        """Return the height and latest block hash."""
        return {
            "height": len(self.chain) - 1,
            "hash": self.chain[-1]["hash"]
        }

