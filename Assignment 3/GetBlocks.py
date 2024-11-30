import socket
import json
import time


class BlockchainFetcher:
    def __init__(self, peer_host, peer_port):
        self.peer_host = peer_host
        self.peer_port = peer_port
        self.chain = []

    def send_request(self, height):
        # Prepare the GET_BLOCK request
        message = json.dumps({
            "type": "GET_BLOCK",
            "height": height
        })

        # Create a UDP socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(2)  # Timeout for responses
            try:
                # Send the request to the peer
                sock.sendto(message.encode(), (self.peer_host, self.peer_port))
                print(f"Sent request for block at height {height} to {self.peer_host}:{self.peer_port}")

                # Receive the response
                response, _ = sock.recvfrom(4096)
                block = json.loads(response.decode())
                return block
            except socket.timeout:
                print(f"Timeout while waiting for block at height {height}")
                return None
            except Exception as e:
                print(f"Error while fetching block at height {height}: {e}")
                return None

    def fetch_blockchain(self, max_height):
        print(f"Fetching blockchain up to height {max_height}...")

        for height in range(max_height + 1):
            block = self.send_request(height)
            if block and block.get("type") == "GET_BLOCK_REPLY" and block.get("height") is not None:
                self.chain.append(block)
                print(f"Received block at height {height}: {block}")
            else:
                print(f"Failed to retrieve block at height {height}, stopping fetch.")
                break

            # Add a delay to avoid overwhelming the server
            time.sleep(0.5)

        print("Completed fetching blockchain.")
        return self.chain


if __name__ == "__main__":
    peer_host = "goose.cs.umanitoba.ca"  # Well-known host
    peer_port = 8999  # Port number
    max_height = 10  # Set a max height for the blockchain to fetch

    fetcher = BlockchainFetcher(peer_host, peer_port)
    blockchain = fetcher.fetch_blockchain(max_height)

    print("Final Blockchain:")
    for block in blockchain:
        print(block)
