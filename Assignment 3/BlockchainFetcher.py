import socket
import json
import time


class BlockchainFetcher:
    WELL_KNOWN_HOSTS = [
        ("goose.cs.umanitoba.ca", 8999),
        ("eagle.cs.umanitoba.ca", 8999),
        ("silicon.cs.umanitoba.ca", 8999),
        ("hawk.cs.umanitoba.ca", 8999),
    ]

    def __init__(self, blockchain):
        self.blockchain = blockchain  # Reference to the local blockchain

    def fetch_block(self, host, port, height):
        """Fetch a single block from a specific peer."""
        message = {
            "type": "GET_BLOCK",
            "height": height
        }
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(2)  # Set timeout for the request
                sock.sendto(json.dumps(message).encode(), (host, port))
                data, _ = sock.recvfrom(4096)  # Receive the response
                return json.loads(data.decode())
        except socket.timeout:
            print(f"Timeout fetching block at height {height} from {host}:{port}")
        except Exception as e:
            print(f"Error fetching block at height {height} from {host}:{port}: {e}")
        return None

    def fetch_all_blocks(self):
        """Fetch all blocks from well-known peers and store them in the local blockchain."""
        for host, port in self.WELL_KNOWN_HOSTS:
            print(f"Attempting to fetch blocks from {host}:{port}...")
            height = 0
            while True:
                block_response = self.fetch_block(host, port, height)
                if not block_response or block_response["height"] is None:
                    break
                # Directly append the block to the local blockchain without validation
                self.blockchain.chain.append(block_response)
                print(f"Added block {block_response['height']} from {host}:{port}")
                height += 1

        print("Finished fetching all blocks.")


# Example usage
if __name__ == "__main__":
    from Blockchain import Blockchain

    # Initialize the local blockchain
    blockchain = Blockchain()

    # Create a fetcher to retrieve blocks from well-known peers
    fetcher = BlockchainFetcher(blockchain)

    # Fetch all blocks from the well-known peers
    fetcher.fetch_all_blocks()

    # Print the updated local blockchain
    print(json.dumps(blockchain.get_chain(), indent=4))
