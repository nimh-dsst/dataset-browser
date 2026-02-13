# Template PowerShell script for converting Parquet files to SQLite and joining with CSV/TSV data
# 
# Usage:
#   1. Replace the placeholder values (indicated by <...>) with your actual paths and column names
#   2. Run this script in PowerShell, or copy the commands and run them individually
#

# Step 1: Convert Parquet files to SQLite database
# Replace:
#   <PARQUET_GLOB> - Glob pattern to find Parquet files (e.g., "./data/**/*.parquet")
#   <OUTPUT_DB>    - Output SQLite file path (e.g., "./data/db.sqlite")
uv run python parquets2db.py "<PARQUET_GLOB>" --output "<OUTPUT_DB>"

# Step 2: Join a CSV/TSV file to the database
# Replace:
#   <OUTPUT_DB>       - SQLite database file from step 1 (e.g., "./data/db.sqlite")
#   <CSV_FILE>        - Path to CSV or TSV file to join (e.g., "./data/participants.tsv")
#   <DB_KEY_COLUMN>   - Column name in database table to join on (e.g., "participant_id")
#   <CSV_KEY_COLUMN>  - Column name in CSV/TSV file to join on (e.g., "participant_id")
#   [Optional] --join-type: left (default), right, inner, or outer
#   [Optional] --output-table: Name for the joined table in database (default: "joined_data")
#   [Optional] --table: Name of table in database to join with (default: "data")
uv run python db_join.py "<OUTPUT_DB>" "<CSV_FILE>" `
    --db-key "<DB_KEY_COLUMN>" `
    --csv-key "<CSV_KEY_COLUMN>" `
    --join-type left `
    --output-table "joined_data" `
    --replace


# ============================================================================
# Example with actual values (commented out):
# ============================================================================

<# 
# Convert all RD parquet files to SQLite
uv run python parquets2db.py "./data/RD/**/*.parquet" --output "./data/RD_database.sqlite"

# Join with participants TSV file
uv run python db_join.py "./data/RD_database.sqlite" "./data/RD/participants.tsv" `
    --db-key "participant_id" `
    --csv-key "participant_id" `
    --join-type left `
    --output-table "joined_data" `
    --replace
#>
