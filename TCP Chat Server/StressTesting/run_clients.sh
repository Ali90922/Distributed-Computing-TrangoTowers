#!/bin/bash

# Number of clients passed as an argument
num_clients=$1

# Server IP passed as an argument
server_ip=$2

# Path to my Python client file  - which is in the same directory
client_script="SpamClient.py"

# Function to run a single client
run_client() {
    python3 "$client_script" "Client_$1" "$server_ip" &  # Pass a unique nickname and the server IP to each client
}

# Check if both the number of clients and server IP are provided
if [ $# -lt 2 ]; then
    echo "Usage: ./run_clients.sh <num_clients> <server_ip>"
    exit 1
fi

# Launch the specified number of clients
echo "Running with $num_clients clients connecting to $server_ip..."

for ((i = 1; i <= num_clients; i++)); do
    run_client $i
done


# How to run this file : ./run_clients.sh 10 192.168.1.100
