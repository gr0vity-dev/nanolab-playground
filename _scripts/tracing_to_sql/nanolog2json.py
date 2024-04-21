import json
import re
import sys

# Pre-compiling the regular expression to handle both log line formats
regex_pattern = re.compile(
    r"\[(.*?)\](?: \[(.*?)\])? \[(.*?)\] \[(.*?)\] (.*)")


def parse_log_line(log_line, default_node_name):
    match = regex_pattern.match(log_line)
    if not match:
        return None

    timestamp, node, log_process, log_level, remainder = match.groups()
    if not node:  # If log_node is missing, use the default node name
        node = default_node_name

    log_json = {
        "log_timestamp": timestamp,
        "log_node": node,
        "log_process": log_process,
        "log_level": log_level
    }

    if log_level == "trace":
        try:
            content_json = json.loads("{" + remainder + "}")
            log_json.update(content_json)
        except json.JSONDecodeError:
            log_json["content"] = "Invalid JSON content"
    else:
        log_json["content"] = remainder

    return json.dumps(log_json)


def process_file(file, default_node_name):
    output_buffer = []
    for line in file:
        json_line = parse_log_line(line, default_node_name)
        if json_line:
            output_buffer.append(json_line)
            if len(output_buffer) >= 1000:  # Adjust the buffer size as needed
                print('\n'.join(output_buffer))
                output_buffer.clear()
    if output_buffer:
        print('\n'.join(output_buffer))


# Default node name can be provided as a command line argument
default_node_name = sys.argv[1] if len(sys.argv) > 1 else "unknown_node"

with sys.stdin as file:
    process_file(file, default_node_name)
