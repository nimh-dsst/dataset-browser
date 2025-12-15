#! /usr/bin/env python3

###
# Serves a Plotly Dash dashboard for BIDS participant data from bids2table
# Parquet files. Accepts multiple Parquet files as input via CLI.
###

# dash-specific imports
from dash import Dash, html, dcc, callback, Output, Input
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.express as px

# general imports
import argparse
import pandas
from pathlib import Path

# dataframe loading

def cli():
    parser = argparse.ArgumentParser(
        description="Serve a dashboard for BIDS participant data."
    )
    parser.add_argument(
        '-p', '--parquet', type=Path, metavar="PARQUET_FILE", nargs='+', dest='parquets',
        help="Paths to all input bids2table Parquet files."
    )
    args = parser.parse_args()

    return args


# load data
args = cli()
parquet_list = args.parquets

for p in parquet_list:
    if not p.is_file():
        raise FileNotFoundError(f"Error: The file {p} does not exist.")

# For simplicity, using the first file
# @TODO Handle multiple files properly
parquet_file = parquet_list[0]
b2t_df = pandas.read_parquet(parquet_file)
df = b2t_df[['ds__dataset', 'ent__datatype', 'ent__suffix', 'ent__task', 'ent__run', 'ent__echo']]

participants = b2t_df['ent__sub'].sort_values().drop_duplicates().reset_index(drop=True)
datatypes = b2t_df['ent__datatype'].sort_values().drop_duplicates().reset_index(drop=True)

# initialize Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# The dashboard is laid out with selectors to filter data and tables to display
# remaining participants and data available.
app.layout = dbc.Container([
    dbc.Row([
        html.H1("BIDS Participant Dashboard", className="my-4"),
        dbc.Row([
            dbc.Col([
                dbc.Stack([
                    dbc.Card(dbc.CardBody('Sex (select 1 or more)')),
                    dbc.Card(dbc.CardBody(dcc.Dropdown(
                        options=['female', 'male', 'n/a'],
                        value=['female', 'male', 'n/a'],
                        multi=True,
                        closeOnSelect=False,
                        style={'width': '100%'},
                        id='sex-multiselect',
                    ))),
                ]),
            ]),
            dbc.Col(
                dbc.Stack([
                    dbc.Card(dbc.CardBody('Data Types (select 1 or more)')),
                    dbc.Card(dbc.CardBody(dcc.Dropdown(
                        options=datatypes.to_list(),
                        value=datatypes.to_list(),
                        multi=True,
                        closeOnSelect=False,
                        style={'width': '100%'},
                        id='dt-multiselect',
                    ))),
                ]),
            ),

            # data table
            dag.AgGrid(
                rowData=df.to_dict('records'),
                columnDefs=[{"field": c} for c in df.columns],
                id='dt-table'
            ),

        ], style={'width': '80%'}),

        dbc.Col(
            # participant table
            dag.AgGrid(
                rowData=[{'participant_id': p} for p in participants.to_list()],
                columnDefs=[{"field": 'participant_id'}],
                id='participant-table'
            ),
        )

    ])

])


if __name__ == "__main__":
    app.run(debug=True)
