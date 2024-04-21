import pandas as pd
import subprocess
import json

# This script looks at the available gcloud instances and creates a matrix of nodes recognised by the peercrawler (with vote weight)
#            genesis pr1 pr2 pr3 pr4
#    genesis           X   X   X   X
#        pr1               X   X   X
#        pr2           X       X
#        pr3           X   X
#        pr4           X   X   X


completed_process = subprocess.run(
    ['nanomock', 'rpc', '--payload',
        '{"action": "confirmation_quorum", "peer_details": "true"}'],
    capture_output=True,
    text=True
)


def rm_substring_to_end(s, substring):
    # Split the string at the specified substring
    # The second argument limits the split to the first occurrence
    parts = s.split(substring, 1)
    # Return the part before the substring if it's found, otherwise return the original string
    return parts[0] if len(parts) > 1 else s


json_data = None
# Check if the command was successful
if completed_process.returncode == 0:
    output = completed_process.stderr
    # Assuming the output starts with 'SUCCESS: '
    try:
        # Extract JSON string after 'SUCCESS: '
        json_str = rm_substring_to_end(
            output.split('SUCCESS: ', 1)[1], "\nSUCCESS")

        # Parse the JSON string into a Python object
        json_data = json.loads(json_str)
    except Exception as e:
        print(f"Failed to parse JSON data: {e}")
else:
    print("Command failed")
    json_data = None


# List of peers with their details
# peers_info = [
#     {"name": "pr2", "zone": "us-east1-b", "internal_ip": "10.142.0.63"},
#     {"name": "pr4", "zone": "us-east1-b", "internal_ip": "10.142.15.192"},
#     {"name": "genesis", "zone": "europe-west2-a", "internal_ip": "10.154.0.43"},
#     {"name": "pr1", "zone": "europe-west2-a", "internal_ip": "10.154.0.41"},
#     {"name": "pr3", "zone": "asia-south1-a", "internal_ip": "10.160.15.199"}
# ]


# Execute the command and capture the output
completed_process2 = subprocess.run(
    ['gcloud/gcluster.py', '--list'],
    capture_output=True,
    text=True
)

# Initialize an empty list to hold the parsed peer info
peers_info = []

# Check if the command was successful
if completed_process2.returncode == 0:
    output = completed_process2.stdout
    # Split the output into lines
    lines = output.strip().split('\n')
    # Skip the header line and iterate over the remaining lines
    for line in lines[1:]:
        # Split each line into parts based on whitespace
        parts = line.split()
        # Extract the required fields and add them to the peers_info list
        if len(parts) >= 7:
            peer_info = {
                "name": parts[0],
                "zone": parts[1],
                "internal_ip": parts[4]
            }
            peers_info.append(peer_info)


# Mapping node names to their IP addresses
ip_to_name = {peer["internal_ip"]: peer["name"] for peer in peers_info}

# Extract the internal IP addresses from the json_data for mapping


def extract_internal_ip(peer_ip):
    ip_start = peer_ip.find("10.")
    ip_end = peer_ip.find("]:")
    return peer_ip[ip_start:ip_end]


# Initialize the connection matrix
nodes = ["genesis", "pr1", "pr2", "pr3", "pr4",
         "pr5", "pr6", "pr7", "pr8", "pr9", "pr10"]
# nodes = ["genesis", "pr1", "pr2", "pr3", "pr4"]
connections = {node: {other_node: '' for other_node in nodes}
               for node in nodes}

# Continuing to populate the connection matrix based on the corrected approach
for index, element in enumerate(json_data):
    # Node names are assumed to be assigned in order: genesis, pr1, pr2, pr3, pr4
    node_name = nodes[index]
    for peer in element["peers"]:
        internal_ip = extract_internal_ip(peer["ip"])
        if internal_ip in ip_to_name:
            peer_name = ip_to_name[internal_ip]
            # Mark the connection with 'X'
            connections[node_name][peer_name] = 'X'

# Display the connection matrix in a readable format
connection_matrix = [[""] + nodes]  # Header row
for node in nodes:
    row = [node]
    for other_node in nodes:
        row.append(connections[node][other_node])
    connection_matrix.append(row)


df = pd.DataFrame(connection_matrix[1:], columns=connection_matrix[0])
print(df)
