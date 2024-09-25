#!/bin/bash

# Number of clients passed as an argument
num_clients=$1

# Path to your Python client file
client_script="SpamClient.py"

# Function to run a single client
run_client() {
    python3 "$client_script" "Client_$1" &  # Pass a unique nickname to each client
}

# Launch the specified number of clients
echo "Running with $num_clients clients..."

for ((i = 1; i <= num_clients; i++)); do
    run_client $i
done

# Let the clients run for 5 minutes (300 seconds) before killing them
sleep 300

# Kill all clients after test period
echo "Stopping clients..."
pkill -f "$client_script"

echo "Test complete!"



# Command to make to script executeble on my AWS machine : chmod +x run_clients.sh
# How to run the script with the commandline arguments : ./run_clients.sh 10
