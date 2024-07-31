#!/bin/bash

# Loop through each argument
for container in "$@"
do
    # Extract IP address for the container
    ip=$(docker inspect $container | jq -r '.[0].NetworkSettings.Networks["nl_nano-local"].IPAddress')

    # Output in the desired format: container_name : ip_address
    echo "$container : $ip"
done
