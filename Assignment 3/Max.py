import socket
import json
import time


class BlockchainFetcher:
    def __init__(self, peer_host, peer_port):
        self.peer_host = peer_host
        self.peer_port = peer_port
        self.chain = []

    def send_request(self, request_type, height=None):
        # Prepare the request message
        message = {"type": request_type}
        if height is not None:
            message["height"] = height

        # Create a UDP socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(2)  # Timeout for responses
            try:
                # Send the request to the peer
                sock.sendto(json.dumps(message).encode(), (self.peer_host, self.peer_port))
                print(f"Sent {request_type} request to {self.peer_host}:{self.peer_port}")

                # Receive the response
                response, _ = sock.recvfrom(4096)
                return json.loads(response.decode())
            except socket.timeout:
                print(f"Timeout while waiting for {request_type} response.")
                return None
            except Exception as e:
                print(f"Error during {request_type} request: {e}")
                return None

    def fetch_chain_length(self):
        print("Fetching blockchain length using STATS request...")
        stats_reply = self.send_request("STATS")
        if stats_reply and stats_reply.get("type") == "STATS_REPLY" and "height" in stats_reply:
            chain_length = stats_reply["height"]
            print(f"Determined blockchain height: {chain_length}")
            return chain_length
        else:
            print("Failed to retrieve blockchain length.")
            return None

    def fetch_blockchain(self, max_height):
        print(f"Fetching blockchain up to height {max_height}...")
        for height in range(max_height + 1):
            block = self.send_request("GET_BLOCK", height=height)
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

    def run(self):
        # Step 1: Fetch the blockchain length
        chain_length = self.fetch_chain_length()
        if chain_length is None:
            print("Could not determine blockchain length. Exiting.")
            return

        # Step 2: Fetch the blockchain up to the determined length
        blockchain = self.fetch_blockchain(chain_length)

        # Display the final blockchain
        print("\nFinal Blockchain:")
        for block in blockchain:
            print(block)


if __name__ == "__main__":
    peer_host = "goose.cs.umanitoba.ca"  # Well-known host
    peer_port = 8999  # Port number

    fetcher = BlockchainFetcher(peer_host, peer_port)
    fetcher.run()
