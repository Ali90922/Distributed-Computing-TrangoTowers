import socket
import json
import time


class BlockchainFetcher:
    def __init__(self, blockchain, max_retries=3, retry_delay=2):
        """
        Initialize the BlockchainFetcher.
        
        Args:
            blockchain: The local blockchain object to update.
            max_retries: Maximum number of retries for each block fetch.
            retry_delay: Delay (in seconds) between retries.
        """
        self.blockchain = blockchain
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def fetch_all_blocks(self, peer_host, peer_port):
        """
        Fetch all blocks from a single peer and update the local blockchain.
        
        Args:
            peer_host: The hostname of the peer to fetch blocks from.
            peer_port: The port of the peer to fetch blocks from.
        """
        height = 0
        while True:
            message = {"type": "GET_BLOCK", "height": height}
            retries = 0

            while retries < self.max_retries:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(5)
                    sock.sendto(json.dumps(message).encode(), (peer_host, peer_port))
                    response, _ = sock.recvfrom(4096)
                    block = json.loads(response.decode())

                    if block["height"] is None:  # No more blocks available
                        print(f"No more blocks available from {peer_host}:{peer_port}.")
                        return

                    # Add the fetched block to the local blockchain
                    self.blockchain.chain.append(block)
                    print(f"Added block {block['height']} from {peer_host}:{peer_port}")
                    height += 1
                    break  # Exit retry loop after successful fetch

                except socket.timeout:
                    retries += 1
                    print(f"Timeout fetching block {height} from {peer_host}:{peer_port}. Retrying {retries}/{self.max_retries}...")
                    time.sleep(self.retry_delay)  # Wait before retrying

                except Exception as e:
                    print(f"Error fetching block {height}: {e}")
                    return  # Exit if a non-recoverable error occurs

                finally:
                    sock.close()

            if retries == self.max_retries:
                print(f"Failed to fetch block {height} after {self.max_retries} attempts. Stopping fetch.")
                return
