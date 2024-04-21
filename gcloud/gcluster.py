#!/usr/bin/python3
import argparse
import json
import asyncio
import random


def log_to_console(stdout, stderr):
    if stderr and len(stderr) > 0:
        print(stderr.decode("utf-8"))
    elif stdout:
        print(stdout.decode("utf-8"))


async def get_zones():
    command = ["gcloud", "compute", "zones", "list", "--format", "json"]
    stdout, stderr = await async_subprocess_run(command)
    zones_data = json.loads(stdout)
    zones = [zone["name"] for zone in zones_data]
    return zones


async def async_subprocess_run(command):
    proc = await asyncio.create_subprocess_exec(*command,
                                                stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    return stdout, stderr


async def list_instances_console():
    command = ["gcloud", "compute", "instances", "list"]
    stdout, stderr = await async_subprocess_run(command)
    log_to_console(stdout, stderr)


async def list_instances_async():
    command = ["gcloud", "compute", "instances", "list", "--format", "json"]
    stdout, stderr = await async_subprocess_run(command)
    instances = json.loads(stdout)
    return instances


async def stop_instance(instance):
    instance_name = instance["name"]
    zone = instance["zone"].split("/")[-1]
    print(f"Stopping instance {instance_name} in zone {zone}...")
    command = [
        "gcloud", "compute", "instances", "stop", instance_name, "--zone", zone
    ]
    stdout, stderr = await async_subprocess_run(command)
    log_to_console(stdout, stderr)
    return True


async def stop_instances():
    instances = await list_instances_async()
    stop_tasks = [stop_instance(instance) for instance in instances]
    results = await asyncio.gather(*stop_tasks)
    success_count = sum(1 for result in results if result)
    print(f"{success_count} instances stopped out of {len(stop_tasks)}")


async def delete_instance(instance):
    instance_name = instance["name"]
    zone = instance["zone"].split("/")[-1]
    print(f"Deleting instance {instance_name} in zone {zone}...")
    command = [
        "gcloud", "compute", "instances", "delete", instance_name, "--zone",
        zone, "--quiet"
    ]
    stdout, stderr = await async_subprocess_run(command)
    log_to_console(stdout, stderr)
    return True


async def delete_instances():
    instances = await list_instances_async()
    delete_tasks = [delete_instance(instance) for instance in instances]
    results = await asyncio.gather(*delete_tasks)

    # Count the number of successful deletions
    success_count = sum(1 for result in results if result)
    print(f"{success_count} instances deleted out of {len(delete_tasks)}")


async def restart_instance(instance):
    instance_name = instance["name"]
    zone = instance["zone"].split("/")[-1]
    print(f"Restarting instance {instance_name} in zone {zone}...")
    command = [
        "gcloud", "compute", "instances", "start", instance_name, "--zone",
        zone
    ]
    stdout, stderr = await async_subprocess_run(command)
    log_to_console(stdout, stderr)
    return True


async def restart_instances():
    instances = await list_instances_async()
    restart_tasks = [
        restart_instance(instance) for instance in instances
        if instance["status"] == "TERMINATED"
    ]
    results = await asyncio.gather(*restart_tasks)
    # Count the number of successful deletions
    success_count = sum(1 for result in results if result)
    print(f"{success_count} instances restarted out of {len(restart_tasks)}")


def process_create_args(create_args):
    parsed_args = []
    i = 0
    while i < len(create_args):
        docker_tag = create_args[i]
        num_instances = int(create_args[i + 1])
        i += 2

        if i < len(create_args) and not create_args[i].isdigit():
            zone = create_args[i]
            i += 1
        else:
            zone = None

        parsed_args.append({
            "docker_tag": docker_tag,
            "num_instances": num_instances,
            "zone": zone
        })

    return parsed_args


def main():
    parser = argparse.ArgumentParser(
        description="A tool for managing Google Cloud instances")
    parser.add_argument("--stop",
                        action="store_true",
                        help="Stop all instances")
    parser.add_argument("--restart",
                        action="store_true",
                        help="Restart all terminated instances")
    parser.add_argument("--delete",
                        action="store_true",
                        help="Delete all instances")
    parser.add_argument("--list",
                        action="store_true",
                        help="List current instances")
    args = parser.parse_args()

    asyncio.run(main_async(args))


async def main_async(args):
    if args.stop:
        await stop_instances()

    if args.restart:
        await restart_instances()

    if args.delete:
        await delete_instances()

    if args.list:
        await list_instances_console()


if __name__ == "__main__":
    main()
