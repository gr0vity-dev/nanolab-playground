import json
import requests
import toml

# API endpoint to get the IP addresses
api_url = "https://beta.nanobrowse.com/api/reps_online/"

# Fetch data from the API
response = requests.get(api_url)
api_data = response.json()

# Create the TOML structure
config = {"representatives": {"nodes": []}}
insights_config = {"nodes": [], "source": "gcloud_gr0vity"}

# Add nodes from API response to the TOML structure
for node in api_data:
    node_name = node["alias"]
    node_ip = node["node_ip"].split(']:')[0].strip('[')

    toml_node = {
        "name": node_name,
        "vote_weight_percent": node.get("weight_percent", 0),
        "enable_voting": node.get("is_known_account", False),
        "host_ip": node_ip,
    }

    config["representatives"]["nodes"].append(toml_node)

    insights_config["nodes"].append({
        "name": f'nl_{node_name}',
        "rpc_url": f'http://{node_ip}:17076',
        "is_pr": True
    })

# Write the new TOML file to disk
config_file = './nl_config.toml'
with open(config_file, "w") as f:
    toml.dump(config, f)

# Optionally print insights config for verification
print(insights_config)
