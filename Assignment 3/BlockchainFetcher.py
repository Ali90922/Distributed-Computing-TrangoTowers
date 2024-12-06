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

    def fetch_all_blocks(self, all_peers, longest_chain_peer, longest_chain_height):
        """
        Fetch all blocks up to the longest chain height.
        
        This method attempts to fetch blocks from the list of all known peers
        in a round-robin fashion to distribute the workload. If a block cannot
        be fetched from any of the known peers, it will attempt to fetch it
        from the longest chain peer (which is guaranteed to have all blocks).
        
        Args:
            all_peers: A list of tuples (host, port) of known peers.
            longest_chain_peer: A tuple (host, port) of the peer with the longest chain.
            longest_chain_height: The height of the longest chain.
        """
        # If there are no peers in all_peers, fallback directly to longest_chain_peer
        if not all_peers:
            all_peers = [longest_chain_peer]

        for height in range(longest_chain_height + 1):  # Assuming longest_chain_height is inclusive
            block_fetched = False

            # Try each known peer (except the longest_chain_peer initially) in a round-robin manner
            # to fetch the block. For example, distribute workloads like:
            # block 0 from all_peers[0], block 1 from all_peers[1], etc.
            # If you want a simpler round-robin: just pick a peer based on height % len(all_peers).
            # If you want to skip the longest_chain_peer in the first attempt, filter it out first.
            
            # We'll first try peers other than the longest_chain_peer:
            peers_to_try = [p for p in all_peers if p != longest_chain_peer]
            # If no other peers, peers_to_try will be empty and we'll go straight to longest_chain_peer after this attempt.

            # Round-robin pick a peer based on height (this ensures distribution)
            if peers_to_try:
                peer_index = height % len(peers_to_try)
                selected_peer = peers_to_try[peer_index]
                if self.try_fetch_block(selected_peer, height):
                    block_fetched = True
                else:
                    # If failed to fetch from the chosen peer, try others in `peers_to_try`:
                    for peer in peers_to_try:
                        if peer == selected_peer:
                            continue
                        if self.try_fetch_block(peer, height):
                            block_fetched = True
                            break

            # If still not fetched, try the longest_chain_peer now
            if not block_fetched:
                if self.try_fetch_block(longest_chain_peer, height):
                    block_fetched = True
                else:
                    print(f"Failed to fetch block {height} from all known peers including longest chain peer. Stopping fetch.")
                    return

    def try_fetch_block(self, peer, height):
        """
        Attempt to fetch a single block from a given peer.
        
        Args:
            peer: Tuple (host, port) of the peer to fetch from.
            height: The height of the block to fetch.
        
        Returns:
            True if the block was successfully fetched and appended to the local blockchain, False otherwise.
        """
        peer_host, peer_port = peer
        message = {"type": "GET_BLOCK", "height": height}
        retries = 0

        while retries < self.max_retries:
            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(5)
                sock.sendto(json.dumps(message).encode(), (peer_host, peer_port))
                response, _ = sock.recvfrom(4096)
                block = json.loads(response.decode())

                if block["height"] is None:  # No more blocks available from this peer
                    # This peer doesn't have the block. Return False so we can try another peer.
                    return False

                # Add the fetched block to the local blockchain
                self.blockchain.chain.append(block)
                print(f"Added block {block['height']} from {peer_host}:{peer_port}")
                return True

            except socket.timeout:
                retries += 1
                print(f"Timeout fetching block {height} from {peer_host}:{peer_port}. Retrying {retries}/{self.max_retries}...")
                time.sleep(self.retry_delay)

            except Exception as e:
                print(f"Error fetching block {height} from {peer_host}:{peer_port}: {e}")
                # This peer failed; don't retry more than max_retries times
                return False

            finally:
                if sock:
                    sock.close()

        # If we exhausted retries, return False
        print(f"Failed to fetch block {height} from {peer_host}:{peer_port} after {self.max_retries} attempts.")
        return False
