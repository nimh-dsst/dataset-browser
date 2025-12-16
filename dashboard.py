#! /usr/bin/env python3

###
# Serves a Plotly Dash dashboard for BIDS participant data from bids2table
# Parquet files. Accepts multiple Parquet files as input via CLI.
###

# dash-specific imports
from dash import Dash, html, dcc, Output, Input, State
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.express as px

# general imports
import argparse
import pandas
from pathlib import Path

# dataframe loading
parquet_list = [str(p) for p in Path('data').glob('*/*.parquet')]

for i, parquet_file in enumerate(parquet_list):
    if i == 0:
        b2t_df = pandas.read_parquet(parquet_file)
    else:
        temp_df = pandas.read_parquet(parquet_file)
        b2t_df = pandas.concat([b2t_df, temp_df], ignore_index=True)

subset_df = b2t_df[[
    'ds__dataset',
    'ent__datatype',
    'ent__suffix',
    'ent__task',
    'ent__sub',
    ]].drop_duplicates()

df = subset_df[[
    'ent__datatype',
    'ent__suffix',
    'ent__task',
]].value_counts(sort=False, dropna=False).reset_index(name='count')

participants = subset_df[['ds__dataset', 'ent__sub']].sort_values(by=['ds__dataset', 'ent__sub']).drop_duplicates().reset_index(drop=True)
filtered_participants = participants
datatypes = subset_df['ent__datatype'].sort_values().drop_duplicates().reset_index(drop=True)
suffixes = subset_df['ent__suffix'].sort_values().drop_duplicates().reset_index(drop=True)

# initialize Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# The dashboard is laid out with selectors to filter data and tables to display
# remaining participants and data available.
app.layout = dbc.Container([
    dbc.Row([
        html.H1("BIDS Participant Dashboard"),
        dbc.Row([
            dbc.Col([
                dbc.Stack([
                    dbc.Card(dbc.CardBody('Sex')),
                    dbc.Card(dbc.CardBody(dcc.Dropdown(
                        options=['female', 'male', 'n/a'],
                        value=None,
                        multi=True,
                        closeOnSelect=False,
                        style={'width': '100%'},
                        id='sex-multiselect',
                    ))),
                ]),
            ]),
            dbc.Col(
                dbc.Stack([
                    dbc.Card(dbc.CardBody('Data Types')),
                    dbc.Card(dbc.CardBody(dcc.Dropdown(
                        options=datatypes.to_list(),
                        value=None,
                        multi=True,
                        closeOnSelect=False,
                        style={'width': '100%'},
                        id='datatype-multiselect',
                    ))),
                ]),
            ),
            dbc.Row(
                dbc.Stack([
                    dbc.Card(dbc.CardBody('Suffixes')),
                    dbc.Card(dbc.CardBody(dcc.Dropdown(
                        options=suffixes.to_list(),
                        value=None,
                        multi=True,
                        closeOnSelect=False,
                        style={'width': '100%'},
                        id='suffix-multiselect',
                    ))),
                ]),
            ),

            # data table
            dag.AgGrid(
                rowData=df.to_dict('records'),
                columnDefs=[
                    {'field': 'ent__datatype', 'headerName': 'Data Type'},
                    {'field': 'ent__suffix', 'headerName': 'Suffix'},
                    {'field': 'ent__task', 'headerName': 'Task Name'},
                    {'field': 'count', 'headerName': 'Participant Count'},
                ],
                columnSize="sizeToFit",
                id='datatype-table'
            ),

        ], style={'width': '70%'}),

        dbc.Col(
            # participants table
            dbc.Stack([
                dag.AgGrid(
                    # rowData=[{'participant_id': p} for p in participants.to_list()],
                    rowData=participants.to_dict('records'),
                    columnDefs=[
                        {"field": 'ds__dataset', 'headerName': 'Dataset'},
                        {"field": 'ent__sub', 'headerName': 'Participant ID'},
                    ],
                    id='participants-table',
                ),
                dbc.Card(dbc.CardBody(
                    f'Count: {str(participants.shape[0])}',
                    id='participants-count'
                )),
                dbc.Card(dbc.CardBody(
                    html.Div([
                        html.Button("Download Participants TSV", id="download-participants-button"),
                        dcc.Download(id="download-button"),
                    ]),
                    style={'textAlign': 'center'}
                )),
            ]),
        )

    ])

])


# callback for filtering datatype table based on datatype dropdown selections
@app.callback(
    Output('datatype-table', 'rowData', allow_duplicate=True),
    Input('datatype-multiselect', 'value'),
    prevent_initial_call=True,
)
def update_datatype_table_datatype(filtered_datatypes):

    if not filtered_datatypes:
        return df.to_dict('records')

    else:
        filtered_df = df[df['ent__datatype'].isin(filtered_datatypes)]
        return filtered_df.to_dict('records')


# callback for filtering datatype table based on suffix dropdown selections
@app.callback(
    Output('datatype-table', 'rowData', allow_duplicate=True),
    Input('suffix-multiselect', 'value'),
    prevent_initial_call=True,
)
def update_datatype_table_suffix(filtered_suffixes):

    if not filtered_suffixes:
        return df.to_dict('records')

    else:
        filtered_df = df[df['ent__suffix'].isin(filtered_suffixes)]
        return filtered_df.to_dict('records')


# callback for updating suffix dropdown based on filtered datatype table
@app.callback(
    Output('suffix-multiselect', 'value'),
    Input('datatype-table', 'rowData'),
    prevent_initial_call=True,
)
def update_suffix_dropdown(filtered_rows):

    if not filtered_rows:
        return []

    else:
        filtered_df = pandas.DataFrame(filtered_rows)
        return filtered_df['ent__suffix'].unique().tolist()


# callback for updating participants table based on filtered datatype table
@app.callback(
    Output('participants-table', 'rowData'),
    Input('datatype-table', 'rowData'),
)
def update_participants_table(filtered_rows):

    if not filtered_rows:
        filtered_participants = participants.to_dict('records')
        return filtered_participants

    else:
        filtered_df = pandas.DataFrame(filtered_rows)

        merged_df = pandas.merge(
            subset_df,
            filtered_df,
            on=['ent__datatype', 'ent__suffix', 'ent__task'],
            how='inner'
        )

        filtered_participants = merged_df[[
            'ds__dataset',
            'ent__sub'
            ]].sort_values(by=['ds__dataset', 'ent__sub']).drop_duplicates().reset_index(drop=True)

        return filtered_participants.to_dict('records')


# callback for updating participants count based on filtered participants table
@app.callback(
    Output('participants-count', 'children'),
    Input('participants-table', 'rowData'),
    prevent_initial_call=True,
)
def update_participants_count(filtered_rows):
    if not filtered_rows:
        count = participants.shape[0]
    else:
        filtered_df = pandas.DataFrame(filtered_rows)
        count = filtered_df.shape[0]

    return f'Count: {str(count)}'


@app.callback(
    Output("download-button", "data"),
    Input("download-participants-button", "n_clicks"),
    State("participants-table", "rowData"),
    prevent_initial_call=True,
)
def export_on_click(n_clicks, table_data):
    df = pandas.DataFrame.from_dict(table_data)
    return dcc.send_data_frame(df.to_csv, "participants.tsv", sep="\t", index=False)


# run the app
if __name__ == "__main__":
    app.run(debug=True)
