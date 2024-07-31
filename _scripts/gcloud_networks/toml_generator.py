import random
import string

def generate_seed(index):
    prefix = "ABC"
    base = prefix + "0" * (64 - len(prefix) - len(str(index)))
    seed = f"{base}{index}"
    assert len(seed) == 64
    return seed


def generate_nodes(machine_type, zones):
    zone_mappings = {
        "europe": ["europe-west2-a", "europe-west6-b", "europe-west4-c"],
        "us": ["us-central1-a", "us-east1-b", "us-east4-a"],
        "asia": ["asia-southeast2-a", "asia-northeast3-a", "asia-northeast2-b"],
        "australia": ["australia-southeast1-c", "australia-southeast2-a"]
    }

    nodes = []
    index = 1

    for region, count in zones.items():
        possible_zones = zone_mappings.get(region, [])
        for _ in range(count):
            zone = random.choice(possible_zones) if possible_zones else "default-zone"
            node = {
                "name": f"node{index}",
                "seed": generate_seed(index),
                "vote_weight_percent": 0,
                "zone": zone,
                "machine_type": machine_type
            }
            nodes.append(node)
            index += 1

    return nodes

def generate_toml(machine_type, zones):
    nodes = generate_nodes(machine_type, zones)
    toml_string = '[[representatives.nodes]]\n'
    toml_nodes = []

    for node in nodes:
        node_toml = (
            f'      name = "{node["name"]}"\n'
            f'      seed = "{node["seed"]}"\n'
            f'      vote_weight_percent = {node["vote_weight_percent"]}\n'
            f'      zone = "{node["zone"]}"\n'
            f'      machine_type = "{node["machine_type"]}"\n'
            f'      prom_enable = false\n'
            f'      enable_voting = false\n\n'
        )        
        toml_nodes.append(node_toml)

    return toml_string + toml_string.join(toml_nodes)

if __name__ == "__main__":
    machine_type = "e2-small"
    zones = {
        "europe": 10,
        "us": 10,
        "asia": 5,
        "australia": 5
    }

    toml_output = generate_toml(machine_type, zones)
    print(toml_output)