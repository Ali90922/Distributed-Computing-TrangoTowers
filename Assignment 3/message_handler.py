def handle_message(message, peer, addr):
    """Process incoming messages."""
    if message["type"] == "GOSSIP":
        peer.peers.add((message["host"], message["port"]))
        return {
            "type": "GOSSIP_REPLY",
            "host": peer.host,
            "port": peer.port,
            "name": f"Peer_{peer.host}_{peer.port}"
        }

    elif message["type"] == "STATS":
        return peer.blockchain.get_stats()

    elif message["type"] == "GET_BLOCK":
        height = message.get("height")
        if 0 <= height < len(peer.blockchain.chain):
            return peer.blockchain.chain[height]
        return {"type": "GET_BLOCK_REPLY", "height": None}

    elif message["type"] == "CONSENSUS":
        # Trigger consensus (simplified)
        pass

    elif message["type"] == "NEW_WORD":
        # Handle new words (bonus)
        pass

    return None