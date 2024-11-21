#!/bin/bash

# Script to prepare the environment for running local Nano currency testnets using nanolab
# Creates a Python virtual environment and downloads necessary test data for either:
# - 5n4pr configuration (5 nodes total, 4 representatives)
# - 11n10pr configuration (11 nodes total, 10 representatives)


action=$1

setup_python() {
    echo "Setting up the Python virtual environment..."
    rm -rf nanolab_venv
    python3 -m venv nanolab_venv
    . nanolab_venv/bin/activate
    ./nanolab_venv/bin/python3 -m pip install --upgrade pip
    ./nanolab_venv/bin/pip3 install wheel
}

install_dependencies() {
    echo "Installing dependencies..."
    ./nanolab_venv/bin/pip3 install git+https://github.com/gr0vity-dev/python-ed25519-blake2b
    ./nanolab_venv/bin/pip3 install git+https://github.com/gr0vity-dev/nanomock.git@1f0573b13453e4f3e10cae49d9bc6b0d13799a7b
    ./nanolab_venv/bin/pip3 install git+https://github.com/gr0vity-dev/nanolab.git@f664563b1106c80384ade431f93d1670443bc407
}

output_result() {
    echo "A new virtual environment was created."
    echo "################################################"
    echo "#### Please run the following command to activate: "
    echo "###"
    echo "###"
    echo "###      . nanolab_venv/bin/activate"
    echo "###"
    echo "###"
    echo "################################################"
}

untar_folder() {
    echo "Untarring files into _resources/ledgers..."
    local network=$1
    
    # Define arrays based on network type
    declare -a files
    if [ "$network" = "5n4pr" ]; then
        files=("5n4pr_buckets_rocksdb" "5n4pr_init_rocksdb" "5n4pr_bintree_rocksdb")
    elif [ "$network" = "11n10pr" ]; then
        files=() # Add any 11n10pr tar.gz files here if needed
    fi

    # Iterate over the list to untar files conditionally
    for base_name in "${files[@]}"
    do
        local file="${base_name}.tar.gz"
        local target_directory="_resources/ledgers/${base_name}"
        if [ ! -d "$target_directory" ]; then
            echo "Untarring $file..."
            tar -xzvf "_resources/ledgers/$file" -C _resources/ledgers
        else
            echo "Skipping $file, directory $target_directory exists."
        fi
    done
}

create_uid() {
   if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        machine_id=$(cat /sys/class/net/eth0/address)
        random_string=$(echo -n $machine_id | sha256sum | cut -c 1-8)
        sed_cmd="sed -i"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        machine_id=$(ifconfig en0 | awk '/ether/{print $2}')
        random_string=$(echo -n $machine_id | shasum -a 256 | cut -c 1-8)
        sed_cmd="sed -i ''"
    else
        echo "Unsupported OS"
        exit 1
    fi

    find . -type f \( -name "*.toml" -o -name "config*.json" \) | while IFS= read -r file; do
        eval "$sed_cmd 's/\(prom_runid.*\"nanolab_\)[^\"]*/\1${random_string}/g' \"$file\""
    done

    echo "################################################"
    echo "### Visit https://nl-nodestats.bnano.info to see test results"
    echo "### Your personal JOB_ID is nanolab_${random_string}"
    echo "################################################"
    sleep 2

    echo "Replacement complete."
}

download_large_files() {
    local network=$1
    echo "Downloading and organizing files for $network configuration..."
    base_url="https://frmpm7m0wpcq.objectstorage.eu-frankfurt-1.oci.customer-oci.com/n/frmpm7m0wpcq/b/nanoct/o/"

    mkdir -p _resources/blocks
    mkdir -p _resources/ledgers

    # Define arrays based on network type
    declare -a json_files
    declare -a ledger_files

    if [ "$network" = "5n4pr" ]; then
        json_files=("5n4pr_100k_bintree.json"
                   "5n4pr_100k_bintree_short.json"
                   "5n4pr_bucket_rounds.json"
                   "5n4pr_bucket_rounds_short.json"
                   "5n4pr_200legit.json")
        ledger_files=("5n4pr_init_v24.ldb"
                     "5n4pr_init_rocksdb.tar.gz"
                     "5n4pr_buckets_rocksdb.tar.gz"
                     "5n4pr_bucket0-1-88-90-100_10kaccs_v24.ldb"
                     "5n4pr_bintree_rocksdb.tar.gz")
    elif [ "$network" = "11n10pr" ]; then
        json_files=("11n10pr_200legit.json"
                   "11n10pr_bucket_rounds_2m.json")
        ledger_files=("11n10pr_800k.ldb"
                     "11n10pr_800k_rocksdb.tar.gz"
                     "11n10pr_500k_checked_part1.ldb"
                     "11n10pr_500k_checked_part2.ldb"
                     "11n10pr_500k_checked_part3.ldb"
                     "11n10pr_500k_checked_part4.ldb")
    fi

    # Download JSON files into the blocks directory
    for file in "${json_files[@]}"
    do
        wget -nc "${base_url}${file}" -P _resources/blocks
    done

    # Download ldb and tar.gz files into the ledgers directory
    for file in "${ledger_files[@]}"
    do
        wget -nc "${base_url}${file}" -P _resources/ledgers
    done
    echo "Download completed for $network configuration"
}

# Main program execution
case "$action" in
    "")
        create_uid
        download_large_files "5n4pr"
        download_large_files "11n10pr"
        untar_folder "5n4pr"
        untar_folder "11n10pr"
        setup_python
        install_dependencies
        output_result
        ;;
    "download")
        download_large_files "5n4pr"
        download_large_files "11n10pr"
        ;;
    "5n4pr")
        create_uid
        download_large_files "5n4pr"
        untar_folder "5n4pr"
        setup_python
        install_dependencies
        output_result
        ;;
    "11n10pr")
        create_uid
        download_large_files "11n10pr"
        untar_folder "11n10pr"
        setup_python
        install_dependencies
        output_result
        ;;
    "delete")
        if [ -d "nanolab_venv" ]; then
            . nanolab_venv/bin/activate
            deactivate
            rm -rf nanolab_venv
        fi
        ;;
    *)
        echo "Usage:"
        echo "  ./setup_env.sh          # Create virtual environment and download all configuration files"
        echo "  ./setup_env.sh 5n4pr    # Setup environment with 5n4pr configuration files"
        echo "  ./setup_env.sh 11n10pr  # Setup environment with 11n10pr configuration files"
        echo "  ./setup_env.sh delete   # Delete the virtual environment"
        echo "  ./setup_env.sh download # Download all configuration files"
        ;;
esac