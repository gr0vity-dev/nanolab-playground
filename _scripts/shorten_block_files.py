import json


in_file = "11n10pr_bucket_funding_2m"  # .json is added by the script)
in_path = "/Users/bl/Git/nanolab_playground/_testcases_old/downloads/"
# Define the reduction parameters
max_rounds = 5  # Number of rounds to keep
max_elements = 50000  # Number of elements to keep in each list


def analyze_json_data(json_data):
    """ Analyze the JSON data to find the number of rounds and min/max elements per list in each key. """
    analysis_result = {}
    for key, value in json_data.items():
        num_rounds = len(value)
        min_elements = float('inf')
        max_elements = 0
        for sublist in value:
            num_elements = len(sublist)
            if num_elements < min_elements:
                min_elements = num_elements
            if num_elements > max_elements:
                max_elements = num_elements
        analysis_result[key] = {
            'rounds': num_rounds, 'min_elements': min_elements, 'max_elements': max_elements}
    return analysis_result


def process_json_data(json_data, max_rounds, max_elements):
    """ Reduce the number of rounds and elements per list in the JSON data. """
    processed_data = {}
    for key, value in json_data.items():
        processed_sublists = []
        for sublist in value[:max_rounds]:
            if isinstance(sublist, list):
                # Reduce number of elements for lists
                processed_sublists.append(sublist[:max_elements])
            elif isinstance(sublist, dict):
                # Reduce number of elements for dictionaries
                processed_sublists.append(
                    {k: v for k, v in list(sublist.items())[:max_elements]})
        processed_data[key] = processed_sublists
    return processed_data


# Example JSON data
with open(f"{in_path}{in_file}.json", "r") as f:
    json_data = json.load(f)


# Analyze the initial JSON data
initial_analysis = analyze_json_data(json_data)
print("Initial Analysis:", json.dumps(initial_analysis, indent=2))


# Process the JSON data
processed_json_data = process_json_data(json_data, max_rounds, max_elements)

# Re-analyze the processed JSON data
processed_analysis = analyze_json_data(processed_json_data)
print("Processed Analysis:", json.dumps(processed_analysis, indent=2))


with open(f"{in_file}_short.json", "w") as outfile:
    json.dump(processed_json_data, outfile)
