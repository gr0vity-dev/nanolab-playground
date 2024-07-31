import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import sqlite3

# This script creates a plotly plot to analyse the events for a specific hash
# It requires nano traces converted to sqlite3 via `tracing_to_sql` script


def load_data_from_sqlite(db_file, sql_query):
    with sqlite3.connect(db_file) as conn:
        df = pd.read_sql_query(sql_query, conn)
    return df


def preprocess_data(df, time_column='log_timestamp'):
    # Convert time_column to datetime format if not already
    if not np.issubdtype(df[time_column].dtype, np.datetime64):
        df[time_column] = pd.to_datetime(df[time_column])

    # Drop rows where either 'log_node' or 'channel' is missing
    df = df.dropna(subset=['log_node', 'channel'])

    # Keep only rows where 'channel' is in the specified list
    channels = ['nl_pr1', 'nl_pr2', 'nl_pr3', 'nl_pr4']
    df = df[df['channel'].isin(channels)]

    # Generate labels based on 'log_process', 'final_vote', and 'dropped' columns
    df['label'] = df.apply(generate_label, axis=1)

    return df


def generate_label(row):
    label_parts = [row['log_process'].split('::')[-1]]

    label_parts.append('final' if str(
        row['final_vote']).lower() == 'true' else 'normal')
    if str(row['dropped']).lower() == 'true':
        label_parts.append('dropped')
    return '_'.join(label_parts)


def plot_data(df_filtered, df):
    # Create a unique list of all nodes (log_node and channel combined)
    nodes = pd.unique(df_filtered[['log_node', 'channel']].values.ravel('K'))
    nodes = sorted(nodes)  # Sort the nodes
    node_positions = {node: i for i, node in enumerate(nodes)}

    # Define colors for labels
    colors = px.colors.qualitative.Plotly
    labels = df_filtered['label'].unique()
    labels = sorted(labels)  # Sort the nodes
    color_map = {label: colors[i % len(colors)]
                 for i, label in enumerate(labels)}

    # Create a figure
    fig = go.Figure()

    # Add a line for each node, make them all black
    for node in nodes:
        fig.add_trace(go.Scatter(x=[df_filtered['log_timestamp'].min(),
                                    df_filtered['log_timestamp'].max()],
                                 y=[node_positions[node],
                                    node_positions[node]],
                                 mode='lines',
                                 line=dict(color='black'),
                                 name=node,
                                 showlegend=False))

    arrow_lines = {}
    arrow_heads = {}
    origin_dots = {}

    # Collect data for arrow lines, arrowheads, and origin dots
    for _, row in df_filtered.iterrows():
        label = row['label']
        voter = str(row['voter'])
        log_node = str(row['log_node'])

        text = str(
            row['voter']) if voter != 'None' and voter != log_node else ''

        if label not in arrow_lines:
            arrow_lines[label] = {'x': [], 'y': [], 'color': color_map[label]}
            arrow_heads[label] = {'x': [], 'y': [],
                                  'color': color_map[label], 'text': []}
            origin_dots[label] = {'x': [], 'y': [], 'color': color_map[label]}

        start_pos = node_positions[row['log_node']]
        end_pos = node_positions.get(row['channel'])

        if start_pos is not None and end_pos is not None:
            # Line (shaft) of the arrow
            # None to disconnect segments
            arrow_lines[label]['x'].extend(
                [row['log_timestamp'], row['log_timestamp'], None])
            arrow_lines[label]['y'].extend([start_pos, end_pos, None])

            # Arrowhead
            arrow_heads[label]['x'].append(row['log_timestamp'])
            arrow_heads[label]['y'].append(end_pos)
            arrow_heads[label]['text'].append(text)

            # Origin dot
            origin_dots[label]['x'].append(row['log_timestamp'])
            origin_dots[label]['y'].append(start_pos)

    # Add lines (shafts) for each arrow
    # Function to determine the angle for the arrowhead direction

    # Step 1: Add Lines (Shafts) for Each Arrow
    for label, data in arrow_lines.items():
        # Only add lines, without markers here
        fig.add_trace(go.Scatter(
            x=data['x'], y=data['y'],
            mode='lines',
            line=dict(color=data['color'], width=2),
            name=label,
            legendgroup=label,  # Group by label for toggling
        ))

    # Continue from your existing setup

    # Step 2: Adjusted to Plot Arrowheads with Direction
    for label, data in arrow_heads.items():
        if data["text"] != "":
            pass
        for i in range(len(data['x'])):  # Iterate through each arrowhead
            x_val = data['x'][i]
            y_val = data['y'][i]

            # Determine the direction based on y-coordinates
            start_y = origin_dots[label]['y'][i]  # Origin y-coordinate
            end_y = y_val  # Destination y-coordinate, same as arrowhead's y

            # Choose arrow direction
            arrow_symbol = 'triangle-down' if start_y > end_y else 'triangle-up'

            fig.add_trace(go.Scatter(
                x=[x_val], y=[y_val],
                mode='markers+text',
                marker=dict(symbol=arrow_symbol, size=8, color=data['color']),
                # Optionally, differentiate in the legend
                name=f"{label} Arrowhead",
                text=data['text'][i],  # Apply the label here
                textposition="top center",  # Apply the label here
                legendgroup=label,  # Ensure it's grouped with the line for toggling
                showlegend=False  # Hide legend item for arrowheads to avoid duplicates
            ))

    # The rest of your plotting code remains unchanged

    # Step 3: Plot Dots at Origins
    for label, data in origin_dots.items():
        fig.add_trace(go.Scatter(
            x=data['x'], y=data['y'],
            mode='markers',
            marker=dict(symbol='circle', size=7, color=data['color'], line=dict(
                width=1, color='DarkSlateGrey')),
            name=f"{label} Origin",
            legendgroup=label,  # Ensure it's grouped with the line for toggling
            showlegend=False  # Typically, you don't want separate legend items for these
        ))

    # One unit below the lowest node position
    y_axis_min = min(node_positions.values()) - 1
    # One unit above the highest node position
    y_axis_max = max(node_positions.values()) + 1

    # Define the blacklist patterns
    blacklist_patterns = ["channel", "message"]

    # Function to check if the event is in the blacklist
    def is_blacklisted(event):
        return any(event.startswith(pattern) for pattern in blacklist_patterns)

    # Create a dynamic color map for events
    colors = px.colors.qualitative.Plotly  # Using Plotly's qualitative colors
    event_color_map = {}

    # Initialize a dictionary to store data for each event
    squares_data = {}

    for _, row in df.iterrows():
        log_process = row['log_process']

        # Skip blacklisted events
        if is_blacklisted(log_process):
            continue

        if log_process not in event_color_map:
            event_color_map[log_process] = colors[len(event_color_map) % len(colors)]

        if log_process not in squares_data:
            squares_data[log_process] = {'x': [], 'y': [], 'color': event_color_map[log_process], 'text': []}

        if row['log_node'] in node_positions:
            squares_data[log_process]['x'].append(row['log_timestamp'])
            squares_data[log_process]['y'].append(node_positions[row['log_node']])

            voter = str(row['voter'])
            log_node = str(row['log_node'])
            text = str(row['voter']) if voter != 'None' and voter != log_node else ''
            squares_data[log_process]['text'].append(text)

    # Sort the squares_data by event name
    sorted_squares_data = dict(sorted(squares_data.items()))


    for event, data in sorted_squares_data.items():
        if data['x'] and data['y']:  # Check if there are any events to plot
            fig.add_trace(go.Scatter(
                x=data['x'],
                y=data['y'],
                mode='markers+text',
                marker=dict(symbol="square", color=data['color'], size=8),
                text=data['text'],
                textposition="bottom center",  # Apply the label here
                name=event,
            ))


    # Update the figure layout with customized settings
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Node",
        yaxis=dict(
            tickvals=list(node_positions.values()),
            ticktext=list(node_positions.keys()),
            range=[y_axis_min, y_axis_max]  # Set the y-axis to a tighter range
        ),
        xaxis=dict(
            rangeslider=dict(visible=True)  # Enable the range slider for the x-axis
        ),
        height=len(node_positions) * 120,  # Adjust the overall height of the plot
        legend=dict(
            orientation="h",
            yanchor="bottom",  # Anchor the legend to the top of the bottom margin
            xanchor="center",
            x=0.5,
            y=20,
            font=dict(size=10),  # Adjust the font size if needed
        ),
        margin=dict(l=20, r=20, t=120, b=80)
    )

    # Customize mode bar
    fig.update_layout(
        margin=dict(t=60)  # Increase top margin to make space for the mode bar
    )

    # interested_events = [
    #     "active_elections::active_started",
    #     "active_elections::active_stopped",
    #     "active_elections::active_cemented",
    #     "node::process_confirmed",
    #     "vote_processor::vote_processed",
    #     "election::vote_processed",
    #     "blockprocessor::block_processed",
    #     "network_processed::publish",
    #     "network_processed::confirm_ack"
    # ]

    # # Create a color map for the interested events
    # colors = px.colors.qualitative.Plotly  # Using Plotly's qualitative colors
    # event_color_map = {event: colors[i % len(colors)]
    #                    for i, event in enumerate(interested_events)}

    # # Iterate over the original dataset for the additional events
    # squares_data = {event: {'x': [], 'y': [], 'color': event_color_map[event], 'text': []}
    #                 for event in interested_events}
    # for _, row in df.iterrows():
    #     if row['log_process'] in interested_events and row['log_node'] in node_positions:
    #         squares_data[row['log_process']]['x'].append(row['log_timestamp'])
    #         squares_data[row['log_process']]['y'].append(
    #             node_positions[row['log_node']])

    #         voter = str(row['voter'])
    #         log_node = str(row['log_node'])
    #         text = str(
    #             row['voter']) if voter != 'None' and voter != log_node else ''
    #         squares_data[row['log_process']]['text'].append(text)

    # # Ensure each event type is plotted as a separate scatter trace
    # for event, data in squares_data.items():
    #     # Simplify the event name for the legend
    #     # simplified_event_name = event.split("::")[-1]
    #     if data['x'] and data['y']:  # Check if there are any events to plot
    #         fig.add_trace(go.Scatter(
    #             x=data['x'],
    #             y=data['y'],
    #             mode='markers+text',
    #             marker=dict(symbol="square", color=data['color'], size=8),
    #             text=data['text'],
    #             textposition="bottom center",  # Apply the label here
    #             name=event,
    #         ))

    return fig


def get_sql_query(query_hash):
    return f"""

SELECT
  log_timestamp,
  log_node,
  CASE
    WHEN c.node_id = 'node_3x6d94xew6ece9qu5bdsb4t1zucjmrz3ys7otbkcwsuiwg6t76nhtqksm15j' THEN 'nl_pr1'
    WHEN c.node_id = 'node_3xd3zcngjxjpnu8e37anphkc4t9r6xq9huhckznmi8mcnkaf1tpqewwnat5p' THEN 'nl_pr2'
    WHEN c.node_id = 'node_1o7hebgcybr7o9qb6gfypepdy8xgesx7pyygnnzs3k68s4ywsd5h4wxfmhax' THEN 'nl_pr3'
    WHEN c.node_id = 'node_3fd3p5izhm35b1yph3dyo1dpc7umh3e8qjf9xkb5qcfa3dbosojmrbkd8cr3' THEN 'nl_pr4'
    WHEN c.node_id = 'node_1wp7kh4cmz5adwwh8b6rujrh48kp8gaijjf1hadgsrpa3assj6uio8p66oj1' THEN 'nl_genesis'
    ELSE c.node_id -- Fallback to the original node_id if none of the conditions match
  END AS channel,
  log_process || CASE
                    WHEN result != 'nan' THEN "_" || result
                    ELSE ""
                 END AS log_process,
  v.final as final_vote,
  dropped,
  CASE
    WHEN t.account = '398562D3A2945BE17E6676B3E43603E160142A0A555E85071E5A10D04010D8EC' THEN 'nl_pr1'
    WHEN t.account = 'E7E14C093B31C38C2D806EC17D75D5B08EEEE668D75818F1F4ECF8DD0CC0F3B1' THEN 'nl_pr2'
    WHEN t.account = 'FCE16FA5F87645DD73C799B3E959F635752ACA6EF8D9F4918B34B3D5E00E0B56' THEN 'nl_pr3'
    WHEN t.account = '04BD6D942F527F887196868C8927FF84340B4A9AC491BE69DB3AFC31AAF36F57' THEN 'nl_pr4'
    WHEN v.account = '398562D3A2945BE17E6676B3E43603E160142A0A555E85071E5A10D04010D8EC' THEN 'nl_pr1'
    WHEN v.account = 'E7E14C093B31C38C2D806EC17D75D5B08EEEE668D75818F1F4ECF8DD0CC0F3B1' THEN 'nl_pr2'
    WHEN v.account = 'FCE16FA5F87645DD73C799B3E959F635752ACA6EF8D9F4918B34B3D5E00E0B56' THEN 'nl_pr3'
    WHEN v.account = '04BD6D942F527F887196868C8927FF84340B4A9AC491BE69DB3AFC31AAF36F57' THEN 'nl_pr4'
    ELSE v.account -- Fallback to the original node_id if none of the conditions match
  END AS voter
FROM (
select * from log
where sql_id in ( select main_sql_id from mappings
                  where link_sql_id = (select sql_id from blocks where hash = '{query_hash}')
                  and link_type = 'blocks')
UNION ALL
select * from log
where sql_id in ( select main_sql_id from mappings
                  where link_sql_id = (select sql_id from block where hash = '{query_hash}')
                  and link_type = 'block')
UNION ALL
select * from log
where sql_id in ( select main_sql_id from mappings
                  where link_sql_id = (select sql_id from roots where root = '{query_hash}')
                  and link_type = 'roots')
UNION ALL
select * from log
where sql_id in ( select main_sql_id from mappings
                  where link_sql_id = (select sql_id from hashes where hashes = '{query_hash}')
                  and link_type = 'hashes')
UNION ALL
select * from log where hash = '{query_hash}'
) as t
left join mappings mx on mx.main_sql_id = t.sql_id and mx.link_type = 'channel'
left join channel c on c.sql_id = mx.link_sql_id
left join mappings mx2 on mx2.main_sql_id = t.sql_id and mx2.link_type = 'vote'
left join vote v on v.sql_id = mx2.link_sql_id
order by log_timestamp asc
"""





def main(query_hash, db_file):
    file_out = db_file.split("/")[-1].split(".")[0]
    sql_query = get_sql_query(query_hash)
    df = load_data_from_sqlite(db_file, sql_query)
    df_filtered = preprocess_data(df)
    fig = plot_data(df_filtered, df)
    fig.write_html(f'plotly_{file_out}_{query_hash}.html')
    print(f"Plot saved as 'plotly_{file_out}_{query_hash}.html' ")


if __name__ == "__main__":
    query_hash = input("Enter the query hash: ")
    # example hash = "F183D770609E9611E076BAA0532CD1EC437CDDD0DF2D358A82BA1A6B4A8B158A"
    db_file = input("Enter the database file path: ")
    # example db_file = '/full/path/to/capture.db'
    main(query_hash, db_file)
