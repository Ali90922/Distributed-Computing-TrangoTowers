import socket
import json
import threading
import queue


class BlockchainFetcher:
    def __init__(self, peer_host, peer_port):
        self.peer_host = peer_host
        self.peer_port = peer_port
        self.chain = {}
        self.block_queue = queue.Queue()
        self.max_threads = 10  # Number of concurrent threads

    def send_request(self, request_type, height=None):
        # Prepare the request message
        message = {"type": request_type}
        if height is not None:
            message["height"] = height

        # Create a UDP socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(1)  # Reduced timeout
            try:
                # Send the request to the peer
                sock.sendto(json.dumps(message).encode(), (self.peer_host, self.peer_port))

                # Receive the response
                response, _ = sock.recvfrom(4096)
                return json.loads(response.decode())
            except socket.timeout:
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

    def fetch_block_worker(self):
        while not self.block_queue.empty():
            height = self.block_queue.get()
            block = self.send_request("GET_BLOCK", height=height)
            if block and block.get("type") == "GET_BLOCK_REPLY" and block.get("height") is not None:
                self.chain[height] = block
                print(f"Received block at height {height}")
            else:
                print(f"Failed to retrieve block at height {height}")
            self.block_queue.task_done()

    def fetch_blockchain(self, max_height):
        print(f"Fetching blockchain up to height {max_height}...")

        # Enqueue all block heights
        for height in range(max_height + 1):
            self.block_queue.put(height)

        # Start worker threads
        threads = []
        for _ in range(self.max_threads):
            thread = threading.Thread(target=self.fetch_block_worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Convert chain dictionary to sorted list
        sorted_chain = [self.chain[height] for height in sorted(self.chain)]
        print("Completed fetching blockchain.")
        return sorted_chain

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
