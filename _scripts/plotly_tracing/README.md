## Plotly graph for hash based events
After tracing all nodes on a local network and exporting it to sql via `tracing_to_sql/run.sh` you can visualize the activity on a specific hash for all nodes.

### Example:

# run spam (60s of backlog processing)
`nanolab run -t testcases/confirming/5n4pr_trace_60s_backlog.json -i nanocurrency/nano-beta:latest`

- run legit block publishing sequentially
`python3 _scripts/publish_legit/publish_dynamic.py _scripts/publish_legit/5n4pr_publish_local.toml`


- After the testcase ended, create the tracing sql capture
`cd _scripts/tracing_to_sql && ./run.sh `


- Create plotly graph for a legit hash, by looking at the hash you are interested in.
`_scripts/plotly_tracing/plotly_events.py` #provide teh right block_hash and database path

