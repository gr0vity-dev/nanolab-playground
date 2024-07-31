import json

in_file = "5n4pr_bucket_rounds"  # Assume the .json extension is added later
in_path = "_resources/blocks/"
# Define the reduction parameters with defaults allowing full list processing when not specified
skip_rounds = 2
skip_elements = 1000
take_rounds = 1  # Number of rounds to process after skipping
take_elements = 1000  # Number of elements to take after skipping

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

def process_json_data(json_data, skip_rounds, take_rounds, skip_elements, take_elements):
    """ Reduce the range of rounds and elements per list in the JSON data based on the specified skips and takes. """
    processed_data = {}
    for key, value in json_data.items():
        # Process the rounds by skipping and then taking the specified number
        processed_sublists = value[skip_rounds:skip_rounds + take_rounds]
        processed_data[key] = [
            sublist[skip_elements:skip_elements + take_elements] if isinstance(sublist, list) else
            {k: v for k, v in list(sublist.items())[skip_elements:skip_elements + take_elements]} if isinstance(sublist, dict)
            else sublist  # In case the sublist is neither a list nor a dict
            for sublist in processed_sublists
        ]
    return processed_data

# Example JSON data loading
with open(f"{in_path}{in_file}.json", "r") as f:
    json_data = json.load(f)

# Analyze the initial JSON data
initial_analysis = analyze_json_data(json_data)
print("Initial Analysis:", json.dumps(initial_analysis, indent=2))

# Process the JSON data with specified skip and take parameters
processed_json_data = process_json_data(json_data, skip_rounds, take_rounds, skip_elements, take_elements)

# Re-analyze the processed JSON data
processed_analysis = analyze_json_data(processed_json_data)
print("Processed Analysis:", json.dumps(processed_analysis, indent=2))

# Save the processed JSON data
with open(f"{in_file}_{skip_rounds}-{skip_rounds + take_rounds}_{skip_elements}-{skip_elements+take_elements}.json", "w") as outfile:
    json.dump(processed_json_data, outfile)
