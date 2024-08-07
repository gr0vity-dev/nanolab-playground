#!./nanolab_venv/bin/python
import asyncio
import subprocess
import re
import time
import concurrent.futures
import base64
import json
import toml
import random

# This script expects to be run from parent directory like ./gcloud/gcloud_nano.py

# TODO :
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
prom_rundid = config.get('prom_rundid', 'nanolab_default_gcloud')


async def async_subprocess_run(command):
    proc = await asyncio.create_subprocess_exec(*command,
                                                stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    return stdout, stderr, proc.returncode


def wait_instance_up(instance_name, zone):
    # Waiting for instances to actually start up
    while True:
        try:
            result = subprocess.run([
                'gcloud', 'compute', 'ssh', instance_name,
                f'--project={project_id}', f'--zone={zone}', '--command',
                'echo "Instance is up"'
            ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            if result.returncode == 0:
                break
            else:
                print(f"'{instance_name}' in '{zone}' waiting startup...")
                time.sleep(5)
        except:
            print(f"SSH failed for '{instance_name}' in '{zone}' retrying...")
            time.sleep(5)

    return True


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

def setup_docker_compose(worker):
    name = worker["name"]
    zone = worker["zone"]
    docker_tag = worker["docker_tag"]
    run_id = worker["runid"]
    prom_enable = worker.get("prom_enable", True)

    # Choose the appropriate docker-compose file based on prom_enable
    docker_compose_file = 'gcloud/gcloud_dc.yml' if prom_enable else 'gcloud/gcloud_dc_nodeonly.yml'

    # Encode the contents of the selected docker-compose.yml file
    with open(docker_compose_file, 'rb') as f:
        docker_compose_contents = f.read()
    docker_compose_b64 = base64.b64encode(docker_compose_contents).decode()

    # Encode the contents of the .env file
    env_contents = f'RUN_ID={run_id}\nDOCKER_TAG={docker_tag}\nINSTANCE_NAME={name}'
    env_b64 = base64.b64encode(env_contents.encode()).decode()

    ssh_cmd = f"""gcloud compute ssh {name} --zone {zone} --command 'sudo sh -c "\
    echo '{env_b64}' | base64 -d > /root/.env && \
    echo '{docker_compose_b64}' | base64 -d > /root/docker-compose.yml"' """
    subprocess.run(ssh_cmd, shell=True, check=True)



def execute_worker_tasks(worker):
    
    worker_instance = worker["name"]
    worker_zone = worker["zone"]
    config_node_path = worker["config_node_path"]
    config_rpc_path = worker["config_rpc_path"]
                             
    wait_instance_up(worker_instance, worker_zone)
    add_config_node(worker_instance, worker_zone, config_node_path)
    add_config_rpc(worker_instance, worker_zone, config_rpc_path)
    setup_docker_compose(worker)


def set_worker_ledger(worker_instance, worker_zone, ledger_name):
    # worker_instance = "example-instance"
    # worker_zone = "us-central1-a"
    # ledger_name = "example-ledger.ldb"
    cmd = [
        "/bin/bash", "./gcloud/script_set_worker_ledger.sh", worker_instance,
        worker_zone, ledger_name
    ]
    subprocess.run(cmd, shell=True, check=True)


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

    node: dict
    for node in config["representatives"]["nodes"]:
        assert "name" in node, "Missing 'name' field in node"
        node.setdefault("zone", random.choice(await get_zones()))
        node.setdefault("machine_type", machine_type)
        node.setdefault("runid", prom_rundid)
        node.setdefault("docker_tag", config["representatives"]["docker_tag"])
        node.setdefault("config_node_path",
                        config["representatives"]["config_node_path"])
        node.setdefault("config_rpc_path",
                        config["representatives"]["config_rpc_path"])

        worker_instances.append(node)

    # return [worker_instances[1]]
    return worker_instances


async def create_instance(worker):
    
    worker_name = worker["name"]
    worker_zone = worker["zone"]
    worker_machine = worker["machine_type"]

    # Create the startup script that will decode the files and execute the docker-compose.yml file
    startup_script = """#!/bin/bash
        apt-get update
        apt-get install -y curl gdb
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        sudo curl -L "https://github.com/docker/compose/releases/download/1.29.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    """

    # Update the gcloud command to pass the metadata with the encoded files and the startup script
    cmd = f'gcloud compute instances create {worker_name} ' \
          f'--project={project_id} ' \
          f'--zone={worker_zone} ' \
          f'--machine-type={worker_machine} ' \
          f'--scopes=compute-rw ' \
          f'--image-family=ubuntu-2204-lts ' \
          f'--image-project=ubuntu-os-cloud '

    # Add metadata
    if is_spot:
        cmd += f'--metadata=worker_role={worker_name},startup-script="{startup_script}",shutdown-script="sudo poweroff" ' \
               '--provisioning-model=SPOT --no-restart-on-failure ' \
               '--maintenance-policy TERMINATE '
        # cmd += f'--metadata=worker_role={name},startup-script="{startup_script}",shutdown-script="sudo poweroff" ' \
        #        '--preemptible --no-restart-on-failure ' \
        #        '--maintenance-policy TERMINATE '
    else:
        cmd += f'--metadata=worker_role={worker_name},startup-script="{startup_script}"'

    process = await asyncio.create_subprocess_shell(cmd,
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE)
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        print(f'Error creating instance {worker_name}: {stderr.decode().strip()}')
    else:
        print(f'Created instance: {worker_name}')


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


async def main():

    # Extract worker instance names, zones and docker_tags
    worker_instances = await get_worker_instances(nl_config_path)

    # Create worker instances concurrently
    tasks = [
        asyncio.ensure_future(create_instance(worker))
        for worker in worker_instances
    ]
    await asyncio.gather(*tasks)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(execute_worker_tasks, worker) for worker in worker_instances]
        # Wait for all tasks to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f"An error occurred: {exc}")


if __name__ == '__main__':
    asyncio.run(main())
