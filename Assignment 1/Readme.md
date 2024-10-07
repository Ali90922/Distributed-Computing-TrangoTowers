
# TCP Chatroom Assignment

This repository contains the Chat Server and Client for a simple TCP-based chatroom application. The project is divided into two main parts:
- **Part 1**: Basic Chat Server and Client functionality.
- **Part 2**: Stress Testing, located in the `StressTesting` directory.

## Part 1: Chat Server and Client

### How to Run the Chat Server
1. Start the server by running the following command:
   ```bash
   python Server.py
   ```

2. After starting the server, run the client by providing the IP address of the host machine as a command-line argument:
   ```bash
   python client.py <host_ip_address>
   ```
   Replace `<host_ip_address>` with the actual IP address of the server (e.g., `130.179.28.117`).

## Part 2: Stress Testing

The `StressTesting` directory contains tools for performance testing the chat server, including:
- **modifiedServer.py**: A version of the server with logging enabled for testing purposes.
- **spamClient.py**: A client script that sends frequent, automated messages to the server.
- **run_clients.sh**: A bash script for automating client connections during testing.



### IMPORTANT Note on PSUTIL

The stress testing setup requires the psutil library to log CPU metrics. To install psutil, run:
```bash
   pip install psutil
   ```
This command will install psutil and allow the stress testing scripts to record CPU and memory metrics during testing.


### Running the Stress Test
1. Start the modified server with logging enabled by running:
   ```bash
   python modifiedServer.py
   ```

2. Use the bash script to run multiple clients for testing. Provide the desired number of clients and the host machine's IP address as arguments:
   ```bash
   ./run_clients.sh <num_clients> <host_ip_address>
   ```
   Replace `<num_clients>` with the number of clients to run (e.g., `10`) and `<host_ip_address>` with the IP address of the server (e.g., `192.168.1.100`).

## Logs and Reporting

- **Logs**: The `Logs` folder contains the full terminal output for each test conducted.
- **Graphs**: The `Graphs` directory includes Python scripts for generating boxplot diagrams and line graphs from the test data.
- **Report**: `Report.md` contains a comprehensive report of the testing process and results.

---

