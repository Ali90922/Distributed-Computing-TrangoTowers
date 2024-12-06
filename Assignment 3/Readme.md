
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
     python Peer.py --host <HOST_IP> --port <PORT> --name <PEER_NAME>
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
- Implemented in `BlockchainFetcher.py` (lines XX-XX).
- The peer requests STATS from all known peers to find the longest chain.
- The chain with the highest height and matching hash is chosen as the valid chain.
- Missing blocks are fetched using `GET_BLOCK` requests.

Peer Management
---------------
- Peers are managed in `Peer.py` (lines XX-XX).
- GOSSIP messages are used to discover and maintain peers.
- Inactive peers are cleaned up after 60 seconds of inactivity.

Mining
------
- Implemented in `Sardukar.py` (lines XX-XX).
- Proof-of-work is used, requiring a nonce that generates a hash with a certain number of leading zeros.

Limitations
-----------
- Messages are limited to 20 characters to fit within the MTU.
- The blockchain uses ASCII zeros for difficulty rather than binary zeros.

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
