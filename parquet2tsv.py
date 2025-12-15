#! /usr/bin/env python3

###
# Converts a Parquet file to a TSV (Tab-Separated Values) file using a
# single argument CLI and Pandas' read_parquet() and DataFrame.to_csv().
###

import argparse
import pandas
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Convert a Parquet file to a TSV file."
    )
    parser.add_argument(
        "parquet_file", type=Path, metavar="PARQUET_FILE",
        help="Path to the input Parquet file."
    )
    args = parser.parse_args()

    parquet_file = args.parquet_file
    tsv_file = parquet_file.with_suffix('.tsv')

    if not parquet_file.is_file():
        raise FileNotFoundError(f"Error: The file {parquet_file} does not exist.")

    df = pandas.read_parquet(parquet_file)
    df.to_csv(tsv_file, sep='\t', index=False)
    print(f"Successfully converted {parquet_file} to {tsv_file}")

if __name__ == "__main__":
    main()
