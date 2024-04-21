import json
import time
import pandas as pd
import asyncio
from nanorpc.client import NanoRpcTyped
import toml
import sys

# DESCRIPTION
# This script expects a running 5n4pr gcloud network and will create a continuous stream of 200 send & open blocks.
# It will wait for the previous confirmation (or timeout) before publishing the next block
#
# EXAMPLE USAGE
# Setup network :   nanolab run -t testcases/backlog/11n10pr_100k_change_lmdb_1cpu_maxed.json -i nanocurrency/nano:V26.1
# Run script:       python3 publish_5n4pr_dynamic.py 5n4pr_publish_local
#
# AUTHOR
# gr0vity-dev : March 2024


# Helper Functions
def get_rpc_endpoints():
    data = toml.load("nl_config.toml")
    host_port_rpc = data['representatives']['host_port_rpc']
    endpoints = []
    for node in data['representatives']['nodes']:
        host_ip = node['host_ip']
        endpoints.append(f"http://{host_ip}:{host_port_rpc}")
    return endpoints


def load_config(config_file):
    with open(config_file, 'r') as file:
        config = toml.load(file)

    # Extract the required configurations
    confirmation_timeout_seconds = config['confirmation_timeout_seconds']
    threshold = config['threshold']
    legit_blocks_path = config['legit_blocks_path']

    # Handle dynamic endpoint loading
    if config.get('use_dynamic_endpoints', False):
        rpc_endpoints = get_rpc_endpoints(config['dynamic_endpoint_config'])
    else:
        rpc_endpoints = config['rpc_endpoints']

    print("Timeout:", confirmation_timeout_seconds)
    print("Threshold:", threshold)
    print("Blocks Path:", legit_blocks_path)
    print("RPC Endpoints:", rpc_endpoints)

    return confirmation_timeout_seconds, threshold, legit_blocks_path, rpc_endpoints


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


async def main(config_file):
    confirmation_timeout_seconds, threshold, legit_blocks_path, rpc_endpoints = load_config(
        config_file)

    data = load_data(legit_blocks_path)
    rpc_clients = [NanoRpcTyped(url) for url in rpc_endpoints]
    publisher_rpc = rpc_clients[2]

    while not await block_count_threshold_reached(publisher_rpc, threshold, debug=True):
        await asyncio.sleep(5)

    for block in data["b"][0]:
        response = await publisher_rpc.process(block, subtype=block["subtype"], json_block=True)
        hash = response.get("hash")
        if not hash:
            continue
        results = await confirm_block(hash, rpc_clients, confirmation_timeout_seconds)
        display_results(hash, block["subtype"], publisher_rpc.rpc.url, results)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 myscript.py <config_file>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
