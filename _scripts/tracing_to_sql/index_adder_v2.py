import sys
from sqlalchemy import create_engine, MetaData, Table, Index

def add_indexes(engine, index_config):
    metadata = MetaData()
    metadata.reflect(bind=engine)

    for table_name, index_columns in index_config.items():
        table = metadata.tables[table_name]

        for idx_cols in index_columns:
            if isinstance(idx_cols, str):
                idx_cols = [idx_cols]  # Convert to list for consistency

            index_name = f"idx_{table_name}_{'_'.join(idx_cols)}"
            try:
                Index(index_name, *[table.c[col] for col in idx_cols]).create(bind=engine)
                print(index_name, "SUCCESS")
            except Exception as exc:
                print(index_name, "ERROR", exc)

# Check if the script received the filename as an argument
if len(sys.argv) != 2:
    print("Usage: ./myscript.py <database_filename>")
    sys.exit(1)

database_path = sys.argv[1]
engine = create_engine(f'sqlite:///{database_path}')

# Define your index configuration
index_config = {
    'log': ['log_process', 'log_event', 'log_file'],
    'message': ['message_type'],
    'mappings': [
        ['main_sql_id', 'main_type', 'link_type', 'link_id'],  # Existing indices
        ['main_sql_id', 'link_type']  # New composite index
    ],
    'blocks': ['signature', 'hashes'],
    'votes': ['timestamp']
}

# Add index on 'sql_id' for each table except 'mappings'
metadata = MetaData()
metadata.reflect(bind=engine)
for table_name in metadata.tables:
    if table_name != 'mappings':
        index_config.setdefault(table_name, []).append(['sql_id'])

# Add the indexes to the database
add_indexes(engine, index_config)
