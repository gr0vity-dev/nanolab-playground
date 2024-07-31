import asyncio
import json
from nanows.api import NanoWebSocket
from nano_lib_py import Block

async def run():
    url = "ws://192.168.178.88:47104"
    nano_ws = None
    EXPECTED_COUNT = 200014

    while not nano_ws:
        try:
            # Attempt to initialize the NanoWebSocket
            nano_ws = NanoWebSocket(url=url)
            await nano_ws.connect()
            print(f"Connected to Nano WebSocket at {url}")
        except Exception as e:
            print(f"Failed to connect to Nano WebSocket: {e}")
            nano_ws = None
            await asyncio.sleep(1)  # Wait for 1 second before retrying

    # Subscribe to the new_unconfirmed_block topic
    await nano_ws.subscribe_new_unconfirmed_block()

    blocks = {"h": []}

    messages = []

    # Listen for messages and save each new unconfirmed block
    async for message in nano_ws.receive_messages():
        # print(f"Received new unconfirmed block: {message}")
        messages.append(message)
        msg_len = len(messages)
        if msg_len % 1000 == 0 :
            print(msg_len)
        if msg_len == EXPECTED_COUNT : break

    for message in messages:
        if "message" in message:
            json_block = message["message"]
            json_block.pop("subtype")
            nano_block = Block.from_dict(json_block, verify=False)
            # Assuming message contains the block hash
            blocks["h"].append(nano_block.block_hash)
            if len( blocks["h"]) % 1000 == 0:
                print(len( blocks["h"]))

    # Save blocks to file
    with open('unconfirmed_blocks.json', 'w') as file:
        json.dump(blocks, file, indent=4)

# Run the async function
asyncio.run(run())
