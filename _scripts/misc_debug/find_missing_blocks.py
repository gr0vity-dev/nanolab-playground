import json
import asyncio
from nanorpc.client import NanoRpcTyped
from nanorpc.client_nanoto import NanoToRpcTyped

# Function to initialize the NanoRpc client
def get_nanorpc_client():
    rpc_url = "http://192.168.178.88:45104"

    return NanoRpcTyped(url=rpc_url, wrap_json=True)

# Initialize clients
nanorpc = get_nanorpc_client()


# Function to read hashes from a file
def read_hashes_from_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    hashes = [item for sublist in data['h'] for item in sublist]
    return hashes

# Function to fetch block info asynchronously
async def fetch_block_info(hashes):
    try:
        response = await nanorpc.blocks_info(hashes, json_block="true", source="true", receive_hash="true", include_not_found="true")
    except Exception as exc:
        raise ValueError("Timeout...\nPlease try again later.")

    return response




# Main function to read hashes and fetch block info
async def main():
    file_path = '/mnt/nvme0n1/Crypto/Nano/projects/nanolab-playground/unconfirmed_blocks.json'
    hashes = read_hashes_from_file(file_path)

    # Split hashes into chunks if necessary (e.g., if API limits the number of hashes per request)
    chunk_size = 1000
    hash_chunks = [hashes[i:i + chunk_size] for i in range(0, len(hashes), chunk_size)]

    missing_hashes = []

    for count, chunk in enumerate(hash_chunks):
        try:
            print(count)
            blocks_info = await fetch_block_info(chunk)
            if "blocks_not_found" in blocks_info:
                missing_hashes.extend(blocks_info["blocks_not_found"])

        except ValueError as e:
            print(e)

    if missing_hashes:
        print(f"Missing hashes: {missing_hashes}")
    else:
        print("All hashes are present.")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())



