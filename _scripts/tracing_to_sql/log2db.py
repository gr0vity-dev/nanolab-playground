#!/usr/bin/env python3

"""
Converts log files to JSON and generates a SQL database from them.

Usage:
./log2db.py

This script reads all `.log` files in the current directory, converts each to a `.json` file using `nanolog2json.py`,
and then generates a SQL database from these JSON files using `json2sql`.

Ensure `nanolog2json.py` and `json2sql` are executable and accessible in your PATH.
"""

import os
import subprocess


def list_log_files(directory):
    """List all .log files in the specified directory."""
    return [f for f in os.listdir(directory) if f.endswith('.log')]


def generate_json(log_file):
    """Generate a JSON file from a log file using nanolog2json.py, with improved error handling."""
    parts = log_file.split('_')
    if len(parts) < 3:  # Check if the filename splits into at least three parts
        print(f"Skipping {log_file}: unexpected filename format.")
        return None
    prefix = parts[0] + '_' + parts[1]  # Safely extract prefix
    json_file = prefix + '.txt'  # Name of the JSON file to be generated
    # Execute the conversion command
    try:
        cmd = f"cat {log_file} | python3 nanolog2json.py {prefix} > {json_file}"
        subprocess.run(cmd, shell=True, check=True)
        return json_file
    except subprocess.CalledProcessError as e:
        print(f"Error processing {log_file}: {e}")
        return None


def main():

    log_files = list_log_files('.')
    json_files = []

    # Convert each log file to a JSON file
    for log_file in log_files:
        json_file = generate_json(log_file)
        if json_file:  # Only add if json_file is not None
            json_files.append(json_file)

    # Ensure there are JSON files to process
    if not json_files:
        print("No JSON files were generated. Exiting.")
        return

    # Step 2: Generate SQL database with the specified order
    json_files_sorted = sorted(json_files, key=lambda x: x.split('_')[
                               1])  # Sort based on the part after 'nl_'
    json_files_order = ' '.join(json_files_sorted)
    cmd = f"json2sql --file {json_files_order} --db capture.db --pin_root"
    subprocess.run(cmd, shell=True, check=True)


if __name__ == "__main__":
    main()
