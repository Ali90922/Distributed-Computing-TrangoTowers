import socket
import json


class BlockchainFetcher:
    def __init__(self, blockchain):
        self.blockchain = blockchain

    def fetch_all_blocks(self, peer_host, peer_port):
        """
        Fetch all blocks from a single peer and update the local blockchain.
        """
        height = 0
        while True:
            message = {"type": "GET_BLOCK", "height": height}
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(5)
                sock.sendto(json.dumps(message).encode(), (peer_host, peer_port))
                response, _ = sock.recvfrom(4096)
                block = json.loads(response.decode())

                if block["height"] is None:  # No more blocks available
                    print(f"No more blocks available from {peer_host}:{peer_port}.")
                    break

                self.blockchain.chain.append(block)
                print(f"Added block {block['height']} from {peer_host}:{peer_port}")
                height += 1

            except socket.timeout:
                print(f"Timeout fetching block {height} from {peer_host}:{peer_port}.")
                break
            except Exception as e:
                print(f"Error fetching block {height}: {e}")
                break
            finally:
                sock.close()
