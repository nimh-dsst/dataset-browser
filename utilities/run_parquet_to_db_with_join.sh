#!/usr/bin/env bash
#
# Template script for converting Parquet files to SQLite and joining with CSV/TSV data
# 
# Usage:
#   Run this script, or copy the commands and run them individually
#

# Step 1: Convert Parquet files to SQLite database
# Replace:
#   <PARQUET_GLOB> - Glob pattern to find Parquet files (e.g., "./data/**/*.parquet")
#   <OUTPUT_DB>    - Output SQLite file path (e.g., "./data/db.sqlite")
uv run python utilities/parquets2db.py "C:/Users/earlea/OneDrive - National Institutes of Health/Desktop/temp/dataset_browser/data/*/*.parquet" --output "data/db.sqlite"

# Step 2: Join a CSV/TSV file to the database
# Replace:
#   <OUTPUT_DB>       - SQLite database file from step 1 (e.g., "./data/db.sqlite")
#   <CSV_FILE>        - Path to CSV or TSV file to join (e.g., "./data/participants.tsv")
#   <DB_KEY_COLUMN>   - Column name in database table to join on (e.g., "participant_id")
#   <CSV_KEY_COLUMN>  - Column name in CSV/TSV file to join on (e.g., "participant_id")
#   [Optional] --join-type: left (default), right, inner, or outer
#   [Optional] --output-table: Name for the joined table in database (default: "joined_data")
#   [Optional] --table: Name of table in database to join with (default: "data")
uv run python utilities/db_join.py "data/db.sqlite" "data/sub_MRN_clean_subset.csv" \
    --db-key "ent__sub" \
    --csv-key "ent__sub" \
    --join-type outer \
    --output-table "data" \
    --replace
