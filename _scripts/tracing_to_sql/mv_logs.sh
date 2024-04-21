#!/bin/bash


# Get the directory where the script itself is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRANDPARENT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Default values
DESTINATION_DIR="$SCRIPT_DIR"
SOURCE_DIR="$GRANDPARENT_DIR/nano_nodes"
EXECUTE_FLAG=""

# Parse arguments
for arg in "$@"
do
    if [[ "$arg" == "-x" ]]; then
        EXECUTE_FLAG="-x"
    elif [[ -z "$EXECUTE_FLAG" ]]; then  # If -x is not set, treat as destination directory
        DESTINATION_DIR="$arg"
    fi
done

# Function to process each found file
move_and_rename() {
    local file_path="$1"
    local destination_dir="$2"
    local execute_flag="$3"
    local dir_name=$(dirname "$file_path")
    local base_name=$(basename "$file_path")

    # Extract the folder name and the timestamp
    local folder_name=$(echo "$dir_name" | awk -F'/nano_nodes/' '{print $2}' | awk -F'/' '{print $1}')
    local timestamp=$(echo "$base_name" | sed 's/log_//')

    # Construct the new file name and path
    local new_name="${folder_name}_${timestamp}"
    local new_path="${destination_dir}/${new_name}"

    # Print or execute the move and rename command
    if [ "$execute_flag" == "-x" ]; then
        mkdir -p "$destination_dir"
        mv "$file_path" "$new_path"
    else
        echo "mv \"$file_path\" \"$new_path\""
    fi
}

# Export the function so it's available to find's -exec
export -f move_and_rename

# Find and process files from the current working directory's nano_nodes
find $SOURCE_DIR -name "log_*.log" -exec bash -c 'move_and_rename "$0" "'"$DESTINATION_DIR"'" "'"$EXECUTE_FLAG"'"' {} \;