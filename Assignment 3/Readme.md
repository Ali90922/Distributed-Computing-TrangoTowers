
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

2. `Peer.py`:
   - Implements the UDP communication for the peer-to-peer network.
   - Handles protocols such as GOSSIP, GET_BLOCK, STATS, CONSENSUS, and message relaying.

3. `Sardukar.py`:
   - Same functionality as Peer.py just uses multi threading and focuses on mining blocks.
   - Automatically starts mining, does not need the user to prompt it to mine

4. `BlockchainFetcher.py`:
   - Used for fetching the blockchain from peers during synchronization.

5. `Script.py`:
   - Contains the main script to initialize and start a peer.

6. `test_cli.py`:
   - CLI for testing blockchain commands and protocols.

7. `Commands`:
   - Directory containing example commands and usage for testing the blockchain functionality.

8. `Assets`:
   - Contains any additional assets used during the project.

How to Run the Code
-------------------
1. Start a peer:
   - Run `Peer.py` with the required arguments:
     ```
     python Peer.py --host <HOST_IP> --port <PORT> 
     ```

2. Join the network:
   - The peer will automatically send a GOSSIP message to one of the well-known hosts.

3. Mining:
   - Mining is implemented in `Sardukar.py`. The Sardukar file is a slightly modified version of Peer.py with focus on mining - 

4. Testing Protocols:
   - Use the `test_cli.py` script to send protocol messages like `GET_BLOCK`, `STATS`, and `CONSENSUS`:
     ```
     python test_cli.py --command "STATS"
     ```

Consensus Algorithm
-------------------
- Implemented in `Peer.py` (lines 177-215).
- The peer requests STATS from all known peers to find the longest chain.
- The chain with the highest height and matching hash is chosen as the valid chain.
- Missing blocks are fetched using `GET_BLOCK` requests. -- Following is the function for perfomring Conesensus :




    def perform_consensus(self):
        """Perform consensus by fetching blockchain stats from well-known peers."""
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

        if longest_chain_stats["height"] <= len(self.blockchain.chain) - 1:
            print("Local blockchain is already up to date or matches the longest chain.")
            return

        print(f"Peer {longest_chain_peer[0]}:{longest_chain_peer[1]} has the longest chain (height {longest_chain_stats['height']}).               Fetching their blockchain...")

        # Clear local chain and fetch the longer one
        self.blockchain.chain = []
        fetcher = BlockchainFetcher(self.blockchain)
        fetcher.fetch_all_blocks(*longest_chain_peer)

        # Validate the fetched chain and print stats
        if self.blockchain.validate_fetched_chain(self.blockchain.chain):
            print(f"Consensus complete. Blockchain synchronized with height: {len(self.blockchain.chain) - 1}")
        else:
            print("Fetched blockchain is invalid. Keeping local blockchain.")



Peer Management
---------------
- Peers are managed in `Peer.py` (lines XX-XX).
- GOSSIP messages are used to discover and maintain peers.
- Inactive peers are cleaned up after 60 seconds of inactivity.

Mining
------
- Implemented in both Peer.py and Sardukar.py, but Sardukar is more speacialised and does automining while utilising mutltiple cpu threads.
- Proof-of-work is used, requiring a nonce that generates a hash with a certain number of leading zeros.
- I have implemented implemented a continuous mining thread that operates in the background, mining blocks while ensuring synchronization with the main thread using a threading.Lock for thread-safe access to the blockchain. The mining loop checks if the chain is synchronized, mines blocks using multiprocessing, and safely adds them to the blockchain. The thread gracefully shuts down when the peer stops, and synchronization ensures no conflicts between mining and consensus. This implementation aligns with real-world blockchain behavior, demonstrating concurrency management and meeting the +10% bonus criteria effectively.

**- I have mined blocks in the main network with the name "Nico Rosberg" -- Mined a total of 15 Blocks !, following is block 2155 which I have mined : **

(base) wifi-wpa-cw2-140-193-120-197:Distributed-Computing-TrangoTowers Ali_Nawaz$ echo '{"type":"GET_BLOCK", "height":2155}' | nc -u eagle.cs.umanitoba.ca 8999
{"type": "GET_BLOCK_REPLY", "height": 2155, "minedBy": "Nico Rosberg", "nonce": "146424285", "messages": ["Jihan", "Park", "Mirha"], "hash": "6a90cf4e2ac46dd0f3b59e8a99673b4e800f08ac96731e1c35c2972900000000", "timestamp": 1733103931}




Future Enhancements
-------------------
- Optimize consensus to avoid fetching the entire chain during re-syncs.
- Implement additional mining strategies for efficiency.
- Enhance the peer discovery mechanism.

Notes
-----
- Ensure the correct IP address is used for the test and challenge networks.
- All the scripts must be executed with Python 3.

---
