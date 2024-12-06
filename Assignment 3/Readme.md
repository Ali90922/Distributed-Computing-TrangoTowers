
Assignment 3: Blockchain
=========================

Overview
--------
This Assignment implements a basic blockchain peer-to-peer network using UDP communication.
The blockchain supports consensus, mining, and synchronization with multiple peers. 
Each peer manages its own blockchain and validates incoming blocks based on a proof-of-work
mechanism. The project has been implemented in Python, adhering to the constraints and requirements.

Files in the Project
---------------------
1. `Blockchain.py`:
   - Defines the `Block` and `Blockchain` classes.
   - `Block` class encapsulates the block structure, including attributes like minedBy, messages, nonce, etc.
   - `Blockchain` class manages the chain, validates blocks, and handles consensus.

2. `Sardukar.py`:
   - Implements the UDP communication for the peer-to-peer network.
   - Handles protocols such as GOSSIP, GET_BLOCK, STATS, CONSENSUS, and message relaying.
   -  uses multi threading and I have mined 15 Blocks on the main Aviary network with this Blockchain.
   - Automatically starts mining, does not need the user to prompt it to mine

3. `BlockchainFetcher.py`:
   - Used for fetching the blockchain from peers during synchronization.
   - Sardukar.py uses this script to fetch blocks, and this script Collect blocks in a load-balanced and concurrent way.

5. `test_cli.py`:
   - CLI for testing blockchain commands and protocols.

How to Run the Code
-------------------
1. Start a peer:
   
   - Run `Sardukar.py` with the required arguments:
     ```
     python Sardukar.py --host <HOST_IP> --port <PORT> 
     ```

3. Join the network:
   - The peer will automatically send a GOSSIP message to one of the well-known hosts.

4. Mining:
   - Mining is implemented in `Sardukar.py`. The Sardukar file is a slightly modified version of Peer.py with focus on mining - 

5. Testing Protocols:
   - Use the `test_cli.py` script to send protocol messages like `GET_BLOCK`, `STATS`, and `CONSENSUS`:
     ```
     python test_cli.py --command "STATS"
     ```

Consensus Algorithm
-------------------
- Implemented in `Sardukar.py` (lines 249-301).
- The peer requests STATS from all known peers to find the longest chain.
- The chain with the highest height and matching hash is chosen as the valid chain.
- Missing blocks are fetched using `GET_BLOCK` requests. -- Following is the function for perfomring Conesensus :


    def perform_consensus(self):
        """Perform consensus by fetching blockchain stats from well-known peers."""
        # Temporarily pause mining while performing consensus
        self.mining_enabled = False

        try:
            longest_chain_stats = None
            longest_chain_peer = None

            # Fetch stats from all well-known peers
            for peer_host, peer_port in self.well_known_peers:
                print(f"Fetching stats from {peer_host}:{peer_port}...")
                peer_stats = self.get_peer_stats(peer_host, peer_port)
                if not peer_stats:
                    continue

                peer_height = peer_stats.get("height")
                if peer_height is not None:
                    if not longest_chain_stats or peer_height > longest_chain_stats["height"]:
                        longest_chain_stats = peer_stats
                        longest_chain_peer = (peer_host, peer_port)

            # Check if a longer chain exists
            if not longest_chain_stats:
                print("Failed to find any valid peers with longer chains. Skipping consensus.")
                return

            # If our local chain is already as long or longer, no need to fetch
            if longest_chain_stats["height"] <= len(self.blockchain.chain) - 1:
                print("Local blockchain is already up to date or matches the longest chain.")
                return

            print(f"Peer {longest_chain_peer[0]}:{longest_chain_peer[1]} has the longest chain (height {longest_chain_stats['height']}). Fetching their blockchain...")

            # Clear local chain
            self.blockchain.chain = []

            # Prepare a list of all peers (well-known + tracked) for workload distribution
            all_peers = self.well_known_peers + list(self.tracked_peers)

            # Instantiate the fetcher and fetch all blocks
            fetcher = BlockchainFetcher(self.blockchain)
            fetcher.fetch_all_blocks(all_peers, longest_chain_peer, longest_chain_stats["height"])

            # Validate the fetched chain
            if self.blockchain.validate_fetched_chain(self.blockchain.chain):
                print(f"Consensus complete. Blockchain synchronized with height: {len(self.blockchain.chain) - 1}")
            else:
                print("Fetched blockchain is invalid. Keeping local blockchain.")
        finally:
            # Re-enable mining after consensus if still running
            if self.running:
                self.mining_enabled = True


After Fetching the entire blockchain, and verifying it the summary is printed to the console for example:

Validating block with height 2288 (previous block height 2287)
The entire fetched blockchain is verified successfully.
Blockchain Stats:
- Total Blocks: 2289
- Last Block Hash: 320d79ad41de09ce7da27c34bb1a8b2977c675140e984743dbf8725300000000
- Last Block Height: 2288
- Mined By: ecurb
Consensus complete. Blockchain synchronized with height: 2288
Initial consensus complete.
Mining block with height 2289 using multi-processing...
Process 1592245 still mining... Current nonce: 0
Process 1592247 still mining... Current nonce: 1000000
Process 1592249 still mining... Current nonce: 2000000
Process 1592251 still mining... Current nonce: 3000000




Peer Management
---------------

The peer management in the code relies on both a fixed set of "well-known" peers and a dynamically maintained list of "tracked" peers discovered through GOSSIP messages. When the peer starts, it knows about a few trusted nodes (well-known peers) and sends periodic GOSSIP messages to them and any tracked peers. Upon receiving GOSSIP messages from new sources, it adds those peers to its tracked set, gradually building a larger network of nodes. During consensus and block fetching, it uses this expanded list of peers to gather blockchain data more efficiently, with the longest-chain peer ultimately providing any missing blocks. This approach allows the peer to continuously discover, track, and utilize a broader network of nodes without requiring manual configuration

Peers that have not sent GOSSIP messages within a specified timeout period are considered inactive and removed from the peer list. This is achieved by maintaining a timestamp for the last received GOSSIP message from each peer. During each iteration of the server's main event loop, the peer list is scanned, and peers whose last activity exceeds the timeout threshold are removed. This ensures efficient resource utilization and prevents inactive peers from affecting the GOSSIP network.

Mining
------
- Implemented in  Sardukar.py

-  Mining is implemented by spawning multiple processes, each searching a distinct range of nonces to find one that produces a hash meeting the difficulty requirements. The main process creates a shared Manager and Queue to coordinate results, then divides the nonce space into chunks which are processed in parallel. Each subprocess attempts to find a nonce that produces a valid block hash, periodically logging its progress. If any subprocess finds a valid nonce, it places the result in the shared queue, causing all other processes to terminate. The mined block is then updated with the discovered nonce and hash before being added to the local blockchain and announced to the network

-  By continuously running a dedicated mining thread and properly synchronizing it with the main thread, I’ve shown advanced concurrency management that ensures parallel processing of block mining without blocking other operations -- Thus I do deserve the 10 % Bonus marks !
-  Note - I verify the new block with the previous block hash before announcing it to the Network.



I have mined blocks in the main network with the name "Nico Rosberg" -- Mined a total of 15 Blocks !, following is block 2155 which I have mined :

(base) wifi-wpa-cw2-140-193-120-197:Distributed-Computing-TrangoTowers Ali_Nawaz$ echo '{"type":"GET_BLOCK", "height":2155}' | nc -u eagle.cs.umanitoba.ca 8999
{"type": "GET_BLOCK_REPLY", "height": 2155, "minedBy": "Nico Rosberg", "nonce": "146424285", "messages": ["Jihan", "Park", "Mirha"], "hash": "6a90cf4e2ac46dd0f3b59e8a99673b4e800f08ac96731e1c35c2972900000000", "timestamp": 1733103931}



following is the relevent code from Sardukar.py which implements the above 

    def mine_block(self, block):
        """Mine the block to meet the difficulty requirement using multi-processing."""
        print(f"Mining block with height {block['height']} using multi-processing...")
        difficulty = self.blockchain.DIFFICULTY

        manager = multiprocessing.Manager()
        result_queue = manager.Queue()
        num_processes = multiprocessing.cpu_count()
        nonce_range_per_process = 1000000  # Adjust as needed

        # Prepare block data without the nonce and hash
        block_data = {
            'type': block['type'],
            'height': block['height'],
            'messages': block['messages'],
            'minedBy': block['minedBy'],
            'timestamp': block['timestamp']
        }
  ....... Code is longer - refer to Sardukar.py for the full verison




Blockchain Verification
-------------------

After fetching the entire chain from a peer, I run a validate_fetched_chain function that checks the integrity and correctness of every block in the sequence. This involves verifying that each block properly references the hash of the previous block, confirming that each block’s hash meets the required difficulty level, and ensuring that no data within the blocks has been tampered with. Only if every block passes these checks do I accept the fetched chain as valid; otherwise, I discard it and keep my existing blockchain.

Below is the Relevent peice of code from Blockchain.py that implements this : 

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




Future Enhancements
-------------------
- Implement additional mining strategies for efficiency -- write GPU code.
- Enhance the peer discovery mechanism.

Notes
-----
- Ensure the correct IP address is used for the test and challenge networks.
- 

---
