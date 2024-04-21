import json
import time
import pandas as pd
import asyncio
from nanorpc.client import NanoRpcTyped

# This script expects a running 5n4pr network and will create a continuous stream of 200 send & open blocks.
# It will wait for the previous confirmation (or timeout) before publishing the next block

CONFIRMATION_TIMEOUT_SECONDS = 20
THRESHOLD = 203000
LEGIT_BLOCKS_PATH = "testcases/downloads/_blocks/5n4pr_200legit.json"
RPC_ENDPOINTS = [
    "http://127.0.0.1:45101",
    "http://127.0.0.1:45102",
    "http://127.0.0.1:45103",
    "http://127.0.0.1:45104"]


# Helper Functions
def load_data(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)


async def block_count_threshold_reached(rpc, threshold, debug=False):
    try:
        result = await rpc.block_count()
        if debug:
            print(json.dumps(result, indent=2))
        return int(result.get("count", 0)) > threshold
    except Exception as exc:
        print(str(exc))
        return False


async def confirm_block(hash, rpc_clients, timeout):
    start_times = {}
    tasks = [confirm_single_block(rpc, hash, timeout, start_times)
             for rpc in rpc_clients]
    results = await asyncio.gather(*tasks)
    return {rpc.rpc.url: result for rpc, result in zip(rpc_clients, results)}


async def confirm_single_block(rpc, hash, timeout, start_times):
    start_times[rpc] = time.time()
    start_count, start_cemented = await get_block_counts(rpc)
    seen, confirmed_time, seen_time = False, None, None

    while time.time() - start_times[rpc] < timeout:
        block_info = await rpc.block_info(hash)
        if block_info.get("error") == "Block not found":
            await asyncio.sleep(0.2)
            continue
        if not seen:
            seen = True
            seen_time = time.time() - start_times[rpc]
        if block_info.get("confirmed") == "true":
            confirmed_time = time.time() - start_times[rpc]
            break
        await asyncio.sleep(0.2)

    end_count, end_cemented = await get_block_counts(rpc)
    duration = time.time() - start_times[rpc]
    return {
        'seen': f"{seen_time:.2f}",
        'confirmed': f"{confirmed_time:.2f}",
        'bps': f"{calculate_rate(start_count, end_count, duration):.2f}",
        'cps': f"{calculate_rate(start_cemented, end_cemented, duration):.2f}",
        'count_init': start_count,
        'count_final': end_count,
        'cemented_init': start_cemented,
        'cemented_final': end_cemented
    }


async def get_block_counts(rpc):
    result = await rpc.block_count()
    return result['count'], result['cemented']


def calculate_rate(start, end, duration):
    return (int(end) - int(start)) / duration if duration > 0 else 0


def display_results(hash, subtype, publisher, results):
    print(f"="*64)
    print(f"\n{subtype} : {hash} published from {publisher}")
    df = pd.DataFrame.from_dict(results, orient='index')
    print(df[['seen', 'confirmed', 'bps', 'cps', 'count_init',
          'count_final', 'cemented_init', 'cemented_final']].to_string())

# Main Execution


async def main():
    data = load_data(LEGIT_BLOCKS_PATH)
    rpc_clients = [NanoRpcTyped(url) for url in RPC_ENDPOINTS]
    publisher_rpc = rpc_clients[2]

    while not await block_count_threshold_reached(publisher_rpc, THRESHOLD, debug=True):
        time.sleep(5)

    for block in data["b"][0]:
        response = await publisher_rpc.process(block, subtype=block["subtype"], json_block=True)
        hash = response.get("hash")
        if not hash:
            continue
        results = await confirm_block(hash, rpc_clients, CONFIRMATION_TIMEOUT_SECONDS)
        display_results(hash, block["subtype"], publisher_rpc.rpc.url, results)

if __name__ == "__main__":
    asyncio.run(main())
