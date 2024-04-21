#!/bin/bash

# Check if the ledger name argument is set
if [ -z "$1" ]; then
  echo "Usage: $0 [ledger_name]"
  exit 1
fi

# Set the ledger name and command to execute
ledger_name=$1
project_id=$(jq -r '.project_id' ./gcloud/config_gcloud.json)


command_to_execute="""
    sudo bash -c \"
    # Stop the Nano node docker container
    docker stop nanonode 2>/dev/null

    # Remove any existing .ldb files
    rm -f /root/NanoTest/*.ldb

    # Start the Nano node docker container
    while ! command -v docker &> /dev/null
    do
        echo 'Docker is not available, waiting...'
        sleep 10
    done
    sleep 10
    cd /root/ && docker compose stop    

    echo 'Downloading ledger...'
    wget -q -O /root/NanoTest/data.ldb ./_resources/ledgers/${ledger_name}
    echo 'Download complete'
    cd /root/ && docker compose up -d --quiet-pull
    sleep 10
    \"
"""

# Retrieve a list of instances with the 'nanonode' tag
instances=$(gcloud compute instances list --format="table(name,zone)" --project=${project_id} --filter="status=RUNNING" | tail -n +2)

while read -r instance zone; do
  echo "Executing command on instance ${instance} in zone ${zone}..."
  (
    gcloud compute ssh ${instance} \
      --zone ${zone} \
      --command "${command_to_execute}" \
      --project=${project_id} \
      --quiet
    echo "Command execution completed for instance ${instance} in zone ${zone}."
  ) &
done <<< "${instances}"

# Wait for all background processes to complete
wait

echo "All commands executed."