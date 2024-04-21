#!/bin/sh

#Script to create and delete a virtualenv to keep dependencies separate from other projects
# ./nanolab_venv.sh
 # ./nanolab_venv.sh delete

action=$1

#!/bin/bash

# Section 1: Setup virtual environment for Python
setup_python() {
    echo "Setting up the Python virtual environment..."
    rm -rf nanolab_venv
    python3 -m venv nanolab_venv
    . nanolab_venv/bin/activate
    ./nanolab_venv/bin/python3 -m pip install --upgrade pip
    ./nanolab_venv/bin/pip3 install wheel
}

# Section 2: Install dependencies
install_dependencies() {
    echo "Installing dependencies..."
    ./nanolab_venv/bin/pip3 install git+https://github.com/gr0vity-dev/python-ed25519-blake2b
    ./nanolab_venv/bin/pip3 install git+https://github.com/gr0vity-dev/nanomock.git@95f19d009dd3612308a03f2d4006df08bf3681cd
    ./nanolab_venv/bin/pip3 install git+https://github.com/gr0vity-dev/nanolab.git@4d072a2ec9efd90d085ca438d6201abb69ed8505 
    ./nanolab_venv/bin/pip3 install -r requirements.txt --quiet
}

# Section 4: Post-setup messages
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

# Section 7: Untar specific tar.gz files if the corresponding directory does not exist
untar_folder() {
    echo "Untarring files into _resources/ledgers..."

    # List of tar.gz files
    declare -a files=("5n4pr_buckets_rocksdb" "5n4pr_init_rocksdb" "5n4pr_bintree_rocksdb")

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



# Section 5: Download large files
download_large_files() {
    echo "Downloading and organizing files..."
    base_url="https://frmpm7m0wpcq.objectstorage.eu-frankfurt-1.oci.customer-oci.com/n/frmpm7m0wpcq/b/nanoct/o/"
    
    mkdir -p _resources/blocks
    mkdir -p _resources/ledgers

    # List of JSON files
    declare -a json_files=("5n4pr_100k_bintree.json"
                           "5n4pr_100k_bintree_short.json"
                           "5n4pr_bucket_rounds.json"
                           "5n4pr_bucket_rounds_short.json"
                           "11n10pr_bucket_rounds_2m.json")

    # List of ldb and tar.gz files
    declare -a ledger_files=("5n4pr_bucket0-1-88-90-100_10kaccs.ldb"
                             "5n4pr_init.ldb"
                             "5n4pr_buckets_rocksdb.tar.gz"
                             "5n4pr_init_rocksdb.tar.gz"
                             "5n4pr_bintree_rocksdb.tar.gz"
                             "11n10pr_800k.ldb"
                             "11n10pr_500k_checked_part1.ldb"
                             "11n10pr_500k_checked_part2.ldb"
                             "11n10pr_500k_checked_part3.ldb"
                             "11n10pr_500k_checked_part4.ldb")


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

    echo "Download completed"
}

# Main program execution
if [ "$action" = "" ]; then
    download_large_files
    untar_folder
    setup_python
    install_dependencies    
    output_result

elif [ "$action" = "delete" ];
then
    . nanolab_venv/bin/activate
    deactivate
    rm -rf nanolab_venv

else
     echo "run ./setup_python_venv.sh  to create a virtual python environment"
     echo "or"
     echo "run ./setup_python_venv.sh delete  to delete the virstual python environment"
fi

