#!/usr/bin/env python3

"""
Join a CSV or TSV file to an SQLite database table.
The joined result will be written back to the database as a new or updated table.
"""

import argparse
import sqlite3
from pathlib import Path
import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description="Join a CSV or TSV file to a table in an SQLite database."
    )
    parser.add_argument(
        "database",
        type=Path,
        metavar="DATABASE",
        help="Path to the SQLite database file (.sqlite)."
    )
    parser.add_argument(
        "csv_file",
        type=Path,
        metavar="CSV_FILE",
        help="Path to the CSV or TSV file to join."
    )
    parser.add_argument(
        "-t", "--table",
        type=str,
        default="data",
        metavar="TABLE",
        help="Name of the table in the database to join with (default: data)."
    )
    parser.add_argument(
        "-k", "--db-key",
        type=str,
        required=True,
        metavar="DB_KEY",
        help="Column name in the database table to use as the join key."
    )
    parser.add_argument(
        "-c", "--csv-key",
        type=str,
        required=True,
        metavar="CSV_KEY",
        help="Column name in the CSV/TSV file to use as the join key."
    )
    parser.add_argument(
        "-j", "--join-type",
        type=str,
        choices=["left", "right", "inner", "outer"],
        default="outer",
        metavar="JOIN_TYPE",
        help="Type of join to perform: left, right, inner, or outer (default: outer)."
    )
    parser.add_argument(
        "-o", "--output-table",
        type=str,
        default="data",
        metavar="OUTPUT_TABLE",
        help="Name of the output table in the database (default: data)."
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace the output table if it already exists."
    )
    parser.add_argument(
        "-s", "--separator",
        type=str,
        default=None,
        metavar="SEPARATOR",
        help="Delimiter for the input file. Auto-detected from file extension if not specified."
    )
    
    args = parser.parse_args()
    
    # Validate database file
    if not args.database.exists():
        print(f"Error: Database file does not exist: {args.database}")
        return 1
    
    if args.database.suffix != ".sqlite":
        print(f"Warning: Database file does not have .sqlite extension: {args.database}")
    
    # Validate CSV file
    if not args.csv_file.exists():
        print(f"Error: CSV/TSV file does not exist: {args.csv_file}")
        return 1
    
    # Auto-detect separator if not specified
    separator = args.separator
    if separator is None:
        if args.csv_file.suffix.lower() in [".tsv", ".tab"]:
            separator = "\t"
        else:
            separator = ","
    
    try:
        # Connect to database
        print(f"Connecting to database: {args.database}")
        conn = sqlite3.connect(str(args.database))
        
        # Read database table
        print(f"Reading table '{args.table}' from database...")
        db_df = pd.read_sql_query(f'SELECT * FROM "{args.table}"', conn)
        print(f"  Loaded {len(db_df)} rows, {len(db_df.columns)} columns")
        
        # Read CSV/TSV file
        print(f"Reading file: {args.csv_file}")
        csv_df = pd.read_csv(args.csv_file, sep=separator)
        print(f"  Loaded {len(csv_df)} rows, {len(csv_df.columns)} columns")
        
        # Validate join keys exist
        if args.db_key not in db_df.columns:
            print(f"Error: Column '{args.db_key}' not found in database table '{args.table}'")
            print(f"Available columns: {', '.join(db_df.columns)}")
            conn.close()
            return 1
        
        if args.csv_key not in csv_df.columns:
            print(f"Error: Column '{args.csv_key}' not found in CSV/TSV file")
            print(f"Available columns: {', '.join(csv_df.columns)}")
            conn.close()
            return 1
        
        # Perform join
        print(f"Performing {args.join_type} join on {args.db_key} = {args.csv_key}...")
        joined_df = pd.merge(
            db_df,
            csv_df,
            left_on=args.db_key,
            right_on=args.csv_key,
            how=args.join_type
        )
        print(f"  Result: {len(joined_df)} rows, {len(joined_df.columns)} columns")
        
        # Write result to database
        if_exists = "replace" if args.replace else "fail"
        print(f"Writing joined data to table '{args.output_table}'...")
        joined_df.to_sql(args.output_table, conn, if_exists=if_exists, index=False)
        
        conn.close()
        
        print(f"\nSuccess! Joined data written to table '{args.output_table}' in {args.database}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.close()
        return 1


if __name__ == "__main__":
    exit(main())
