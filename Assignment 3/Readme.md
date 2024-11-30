### Directory Structure

peer.py:
The main program for running the peer. Handles blockchain synchronization, gossiping, and consensus.
Listens for incoming UDP messages and responds to requests like GET_BLOCK, STATS, and CONSENSUS.


blockchain.py:
Contains the blockchain data structure and core logic.
Handles block mining, validation, and chain management.
Provides utility functions for fetching statistics and adding new blocks.


BlockchainFetcher.py:
Responsible for fetching the blockchain from well-known peers during the consensus process.
Implements robust retry logic to handle timeouts and ensure reliable fetching of blocks.


Test_cli.py:
Provided by the professor to interact with the peer.
Includes commands like stats, get, and consensus to test blockchain functionality.


Commands:
A text file to store important temporary information or logs during development and testing.


Script.py:
A simple script to ping well-known peers and verify their activity before attempting consensus or blockchain synchronization.