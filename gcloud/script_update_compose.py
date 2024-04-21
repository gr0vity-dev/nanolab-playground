#!./gcloud_venv/bin/python
import asyncio
import subprocess
import re
import concurrent.futures
import base64
import json
import toml
import random
import argparse

#This script expects to be run from parent directory like ./gcloud/gcloud_nano.py

#TODO :
# pass projectid as argument fo all scripts (or create a config)
# make machine_type configurable
# stop instances after tests have finsished.
# restart existing instances if [name , zone , machine_type] equal, else delete instance and create new
# recreate gcloud_dc.yml and use env variables from nl_config

with open('./gcloud/config_gcloud.json') as f:
    config = json.load(f)

project_id = config['project_id']
machine_type = config['machine_type']
nl_config_path = config['nl_config_path']
is_spot = config.get('is_spot', False)


async def async_subprocess_run(command):
    proc = await asyncio.create_subprocess_exec(*command,
                                                stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    return stdout, stderr, proc.returncode



def add_config_node(name, zone, config_node_path):
    result = subprocess.run([
        'gcloud', 'compute', 'instances', 'list', '--format', 'json',
        f'--project={project_id}'
    ],
                            stdout=subprocess.PIPE)
    instances = json.loads(result.stdout)

    # Extract the internal IP addresses of each instance
    ips = [
        instance['networkInterfaces'][0]['networkIP'] for instance in instances
    ]

    # Read the config-node.toml file
    with open(config_node_path, 'r') as f:
        config = toml.load(f)
    # Update the preconfigured_peers field with the internal IP addresses
    config['node']['preconfigured_peers'] = ips
    # Convert the dictionary to a JSON string and encode as bytes
    toml_bytes = toml.dumps(config).encode()
    config_b64 = base64.b64encode(toml_bytes).decode()

    ssh_cmd = f"""gcloud compute ssh {name} --zone {zone} --command 'sudo sh -c "\
    mkdir -p /root/NanoTest && echo '{config_b64}' | base64 -d > /root/NanoTest/config-node.toml"' """
    subprocess.run(ssh_cmd, shell=True, check=True)


def add_config_rpc(name, zone, config_rpc_path):

    with open(config_rpc_path, 'rb') as f:
        config = f.read()
    config_b64 = base64.b64encode(config).decode()

    ssh_cmd = f"""gcloud compute ssh {name} --zone {zone} --command 'sudo sh -c "\
    mkdir -p /root/NanoTest && echo '{config_b64}' | base64 -d > /root/NanoTest/config-rpc.toml"' """
    subprocess.run(ssh_cmd, shell=True, check=True)


def setup_docker_compose(name, zone, docker_tag, run_id):

    # Encode the contents of the docker-compose.yml file
    with open('gcloud/gcloud_dc.yml', 'rb') as f:
        docker_compose_contents = f.read()
    docker_compose_b64 = base64.b64encode(docker_compose_contents).decode()

    # Encode the contents of the .env file
    env_contents = f'RUN_ID={run_id}\nDOCKER_TAG={docker_tag}\nINSTANCE_NAME={name}'
    env_b64 = base64.b64encode(env_contents.encode()).decode()

    ssh_cmd = f"""gcloud compute ssh {name} --zone {zone} --command 'sudo sh -c "\
    echo '{env_b64}' | base64 -d > /root/.env && \
    echo '{docker_compose_b64}' | base64 -d > /root/docker-compose.yml && docker compose up -d"' """
    subprocess.run(ssh_cmd, shell=True, check=True)




async def get_zones():
    command = ["gcloud", "compute", "zones", "list", "--format", "json"]
    stdout, stderr, rcode = await async_subprocess_run(command)
    zones_data = json.loads(stdout)
    zones = [zone["name"] for zone in zones_data]
    return zones

def get_gcloud_instances():
    instances = []

    command = f"gcloud compute instances list --project={project_id} --format=json --filter=status=RUNNING"
    output = subprocess.check_output(command, shell=True)
    raw_instances = json.loads(output)

    for instance in raw_instances:
        instances.append({
            "name": instance["name"],
            "zone": instance["zone"].split('/')[-1]
        })

    return instances


async def get_worker_instances(toml_path) -> list:

    worker_instances = []
    with open(toml_path, "r") as f:
        config = toml.load(f)

    assert "config_node_path" in config[
        "representatives"], "Missing 'config_node_path' in representatives"
    assert "config_rpc_path" in config[
        "representatives"], "Missing 'config_rpc_path' in representatives"
    assert "docker_tag" in config[
        "representatives"], "Missing 'docker_tag' in representatives"
    config.setdefault("prom_runid", "gcloud_test")

    node: dict
    for node in config["representatives"]["nodes"]:
        assert "name" in node, "Missing 'name' field in node"
        node.setdefault("zone", random.choice(await get_zones()))
        node.setdefault("runid", config["prom_runid"])
        node.setdefault("docker_tag", config["representatives"]["docker_tag"])
        node.setdefault("config_node_path",
                        config["representatives"]["config_node_path"])
        node.setdefault("config_rpc_path",
                        config["representatives"]["config_rpc_path"])

        worker_instances.append(node)

    #return [worker_instances[0]]
    return worker_instances


def escape_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r'[^a-z0-9-]+', '-',
                  name)  # Replace any invalid characters with hyphens
    name = re.sub(r'^[^a-z]+', '',
                  name)  # Remove any leading non-alphabetic characters
    name = re.sub(r'[^a-z0-9]+$', '',
                  name)  # Remove any trailing non-alphanumeric characters
    name = re.sub(r'[-]{2,}', '-',
                  name)  # Replace consecutive hyphens with a single hyphen
    name = name[:63]  # Truncate the name if it's longer than 63 characters
    return name

def execute_worker_tasks(worker_instance, worker_zone, config_node_path,
                         config_rpc_path, docker_tag, run_id):
    setup_docker_compose(worker_instance, worker_zone, docker_tag, run_id)
    add_config_rpc(worker_instance, worker_zone, config_rpc_path)
    add_config_node(worker_instance, worker_zone, config_node_path)

def parse_args():
    parser = argparse.ArgumentParser(description="Execute worker tasks with specific configurations.")
    parser.add_argument('-i', '--docker_tag', help='Docker tag to use for the worker tasks', required=False)
    parser.add_argument('--config_rpc_path', help='Path for the RPC configuration', required=False)
    parser.add_argument('--config_node_path', help='Path for the node configuration', required=False)
    return parser.parse_args()

async def main(args):
    # Extract worker instance names, zones, and docker_tags
    worker_instances = await get_worker_instances(nl_config_path)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                execute_worker_tasks,
                worker["name"],
                worker["zone"],
                args.config_node_path or worker["config_node_path"],
                args.config_rpc_path or worker["config_rpc_path"],
                args.docker_tag or worker["docker_tag"],
                worker["runid"]
            ) for worker in worker_instances
        ]
        # Wait for all tasks to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f"An error occurred: {exc}")

if __name__ == '__main__':
    args = parse_args()
    asyncio.run(main(args))