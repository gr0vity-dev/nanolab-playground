#!/bin/bash

# Check if the ledger name argument is set
if [ -z "$1" ]; then
  echo "Usage: $0 [ledger_name]"
  exit 1
fi

# Set the ledger name and command to execute
ledger_name=$1
project_id=$(jq -r '.project_id' ./gcloud/config_gcloud.json)

# Function to create the command string
create_command() {
  local instance_name=$1
  echo """
    sudo bash -c \"
    # Stop the Nano node docker container
    docker stop nanonode 2>/dev/null

    # Remove any existing .ldb files
    rm -f /root/NanoTest/*.ldb

    # Wait until Docker is available
    while ! command -v docker &> /dev/null
    do
        echo 'Docker is not available on instance ${instance_name}, waiting...'
        sleep 10
    done

    # Start the Nano node docker container
    sleep 10
    cd /root/ && docker compose stop    

    echo 'Downloading ledger...'
    # Download the file
    wget -q -O /root/NanoTest/${ledger_name} https://frmpm7m0wpcq.objectstorage.eu-frankfurt-1.oci.customer-oci.com/n/frmpm7m0wpcq/b/nanoct/o/${ledger_name}
   
    # Check the file extension and handle accordingly
    if [[ ${ledger_name} == *.ldb ]]; then
        cp /root/NanoTest/${ledger_name} /root/NanoTest/data.ldb
        echo "Ledger downloaded to /root/NanoTest/data.ldb"
    elif [[ ${ledger_name} == *.tar.gz ]]; then
        rm -rf /root/NanoTest/rocksdb
        mkdir -p /root/NanoTest/rocksdb
        tar -xzf /root/NanoTest/${ledger_name} --strip-components=1 -C /root/NanoTest/rocksdb
        echo "Ledger extracted to /root/NanoTest/rocksdb"
    else
        echo "Unsupported file format."
        rm /root/NanoTest/${ledger_name}
    fi

    # wget -q -O /root/NanoTest/data.ldb https://frmpm7m0wpcq.objectstorage.eu-frankfurt-1.oci.customer-oci.com/n/frmpm7m0wpcq/b/nanoct/o/${ledger_name}

    echo 'Download complete'
    cd /root/ && docker compose up -d --quiet-pull
    sleep 10
    \"
  """
}

# Retrieve a list of instances with the 'nanonode' tag
instances=$(gcloud compute instances list --format="table(name,zone)" --project=${project_id} --filter="status=RUNNING" | tail -n +2)

while read -r instance zone; do
  echo "Executing command on instance ${instance} in zone ${zone}..."
  command_to_execute=$(create_command "${instance}")
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
