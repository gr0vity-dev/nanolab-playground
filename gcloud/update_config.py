#!./nanolab_venv/bin/python
import json
import subprocess
import toml

with open('./gcloud/config_gcloud.json') as f:
    config = json.load(f)

project_id = config['project_id']
config_file = config['nl_config_path']

# Call the gcloud command to list instances
result = subprocess.run([
    "gcloud", "compute", "instances", "list", "--project", project_id,
    "--format=json(name,networkInterfaces[0].accessConfigs[0].natIP,zone)"
],
    capture_output=True)

# Parse the JSON output
instances = json.loads(result.stdout.decode())
print(instances)
insights_config = {"nodes": [], "source": "gcloud_gr0vity"}

# Load the TOML file
with open(config_file, "r") as f:
    config = toml.load(f)

# Update the IP addresses in the TOML file
for instance in instances:

    # Find the matching node in the TOML file
    matching_node = next((node for node in config["representatives"]["nodes"]
                          if node["name"] == instance["name"]), None)

    # If a matching node is found, update its IP address
    if matching_node:
        matching_node["host_ip"] = instance["networkInterfaces"][0][
            "accessConfigs"][0]["natIP"]

        insights_config["nodes"].append({
            "name":
            f'nl_{matching_node["name"]}',
            "rpc_url":
            f'http://{matching_node["host_ip"]}:17076',
            "is_pr":
            False if matching_node["name"] == "genesis" else True
        })
    else:
        print(f"No node found in config file with name '{instance['name']}'")

# Write the updated TOML file back to disk
with open(config_file, "w") as f:
    toml.dump(config, f)

# This can be used to generate a config file for nano-insights project
# with open("./gcloud/config_gather_stats.gcloud.json", "w") as f:
#     json.dump(insights_config, f)
