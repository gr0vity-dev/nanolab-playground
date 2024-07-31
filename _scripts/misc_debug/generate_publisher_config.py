import json
import sys

def generate_blocks(N, total_range):
    step = total_range // N
    blocks = []
    
    for i in range(N):
        start_index = i * step
        end_index = (i + 1) * step if i < N - 1 else total_range
        
        block = {
            "type": "python",
            "method": "publish_blocks",
            "variables": {
                "publish_params": {
                    "blocks_path": "{BLOCK_PATH}",
                    "bps": "{BPS_PER_THREAD}",
                    "start_round": "{START_ROUND}",
                    "end_round": "{END_ROUND}",
                    "subset": {
                        "start_index": start_index,
                        "end_index": end_index
                    }
                }
            },
            "class": "NodeInteraction"
        }
        blocks.append(block)
    
    return blocks

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./run <N>")
        sys.exit(1)
    
    N = int(sys.argv[1])
    total_range = 200000
    
    blocks = generate_blocks(N, total_range)
    
    with open('blocks.json', 'w') as f:
        json.dump(blocks, f, indent=4)
    
    print(f"Blocks written to blocks.json")

