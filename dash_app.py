#!/usr/bin/env python3

"""
Plotly Dash app for querying and visualizing data from SQLite databases.
Features advanced search with modular filter builder, multiple operators,
and support for complex queries.
"""

import os
import sqlite3
import traceback
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, ALL, callback_context
from dash.exceptions import PreventUpdate
from dash.dash_table import DataTable
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "Database Browser"


# Filter operator definitions
FILTER_OPERATORS = {
    "equals": {"label": "equals", "type": "text", "needs_value": True},
    "does_not_equal": {"label": "does not equal", "type": "text", "needs_value": True},
    "like": {"label": "like (contains)", "type": "text", "needs_value": True},
    "not_like": {"label": "not like", "type": "text", "needs_value": True},
    "less_than": {"label": "less than", "type": "number", "needs_value": True},
    "less_than_or_equal": {"label": "less than or equal", "type": "number", "needs_value": True},
    "greater_than": {"label": "greater than", "type": "number", "needs_value": True},
    "greater_than_or_equal": {"label": "greater than or equal", "type": "number", "needs_value": True},
    "in": {"label": "in", "type": "text", "needs_value": True, "help": "comma-separated values"},
    "is_null": {"label": "is null", "type": "none", "needs_value": False},
    "is_not_null": {"label": "is not null", "type": "none", "needs_value": False},
}


class DatabaseConnection:
    """Manages SQLite database connections and queries."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.table_names = []
        self.current_columns = []

    def connect(self) -> bool:
        """Initialize database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self._load_table_names()
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False

    def _load_table_names(self) -> None:
        """Load all table names from the database."""
        if not self.conn:
            return

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        self.table_names = [row[0] for row in cursor.fetchall()]
        cursor.close()

    def get_tables(self) -> List[str]:
        """Get list of all tables."""
        return self.table_names

    def get_table_info(self, table_name: str) -> Tuple[List[str], int]:
        """Get column names and row count for a table."""
        if not self.conn:
            return [], 0

        cursor = self.conn.cursor()
        
        # Get columns
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        self.current_columns = columns

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        cursor.close()
        return columns, row_count

    def get_columns(self, table_name: str) -> List[str]:
        """Get column names for a table."""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        cursor.close()
        return columns

    def build_where_clause(self, filters: List[Dict]) -> Tuple[str, List]:
        """Build WHERE clause from filters list.
        
        Returns:
            Tuple of (where_clause_string, parameters_list)
        """
        if not filters:
            return "", []

        conditions = []
        params = []

        for f in filters:
            if not f.get("field") or not f.get("operator"):
                continue

            field = f["field"]
            operator = f["operator"]
            value = f.get("value", "")

            # Build condition based on operator
            if operator == "equals":
                conditions.append(f'"{field}" = ?')
                params.append(value)
            elif operator == "does_not_equal":
                conditions.append(f'"{field}" != ?')
                params.append(value)
            elif operator == "like":
                # LIKE allows wildcard matching; wrap in % for contains
                conditions.append(f'"{field}" LIKE ?')
                params.append(f"%{value}%")
            elif operator == "not_like":
                conditions.append(f'"{field}" NOT LIKE ?')
                params.append(f"%{value}%")
            elif operator == "less_than":
                conditions.append(f'"{field}" < ?')
                params.append(float(value) if value else 0)
            elif operator == "less_than_or_equal":
                conditions.append(f'"{field}" <= ?')
                params.append(float(value) if value else 0)
            elif operator == "greater_than":
                conditions.append(f'"{field}" > ?')
                params.append(float(value) if value else 0)
            elif operator == "greater_than_or_equal":
                conditions.append(f'"{field}" >= ?')
                params.append(float(value) if value else 0)
            elif operator == "in":
                # Split by comma and strip whitespace
                values = [v.strip() for v in value.split(",") if v.strip()]
                if values:
                    placeholders = ",".join(["?" for _ in values])
                    conditions.append(f'"{field}" IN ({placeholders})')
                    params.extend(values)
            elif operator == "is_null":
                conditions.append(f'"{field}" IS NULL')
            elif operator == "is_not_null":
                conditions.append(f'"{field}" IS NOT NULL')

        if not conditions:
            return "", []

        where_clause = " AND ".join(conditions)
        return where_clause, params

    def format_sql_for_display(self, where_clause: str, params: List) -> str:
        """Format SQL WHERE clause with actual parameter values for display.
        
        Args:
            where_clause: WHERE clause with ? placeholders
            params: List of parameter values
            
        Returns:
            WHERE clause with values substituted (for display only, not execution)
        """
        if not params:
            return where_clause
        
        # Replace ? placeholders with actual values
        display_clause = where_clause
        for param in params:
            # Properly quote string values, leave numbers as-is
            if isinstance(param, str):
                # Escape single quotes in strings
                escaped_value = param.replace("'", "''")
                display_clause = display_clause.replace("?", f"'{escaped_value}'", 1)
            else:
                display_clause = display_clause.replace("?", str(param), 1)
        
        return display_clause

    def execute_query(
        self, query: str, limit: Optional[int] = 500
    ) -> Tuple[pd.DataFrame, Optional[str]]:
        """Execute a SQL query and return results as DataFrame."""
        if not self.conn:
            return pd.DataFrame(), "Database not connected"

        try:
            # Add LIMIT clause if not already present and limit is specified
            query = query.strip()
            if limit and "LIMIT" not in query.upper():
                query += f" LIMIT {limit}"

            df = pd.read_sql_query(query, self.conn)
            return df, None
        except Exception as e:
            return pd.DataFrame(), str(e)

    def get_table_data(
        self, table_name: str, filters: List[Dict] = None, limit: Optional[int] = 500
    ) -> Tuple[pd.DataFrame, Optional[str], str]:
        """Get data from a specific table with optional filters.
        
        Returns:
            Tuple of (dataframe, error_message, sql_query_for_display)
        """
        where_clause, params = self.build_where_clause(filters or [])
        
        query = f'SELECT * FROM "{table_name}"'
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if limit is not None:
            query += f" LIMIT {limit}"

        # Build display query with actual values
        display_query = f'SELECT * FROM "{table_name}"'
        if where_clause:
            display_where = self.format_sql_for_display(where_clause, params)
            display_query += f" WHERE {display_where}"
        if limit is not None:
            display_query += f" LIMIT {limit}"

        try:
            if params:
                df = pd.read_sql_query(query, self.conn, params=params)
            else:
                df = pd.read_sql_query(query, self.conn)
            return df, None, display_query
        except Exception as e:
            return pd.DataFrame(), str(e), display_query

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


def create_table_with_truncation(df: pd.DataFrame) -> DataTable:
    """Create a DataTable with full data but CSS-truncated display at 40 chars."""
    if df.empty:
        return DataTable(data=[], columns=[], id="table-results-datatable")
    
    # Create columns configuration
    columns = [
        {
            "name": col,
            "id": col,
        }
        for col in df.columns
    ]
    
    # Use full data without truncation - CSS will handle display truncation
    # Also add title attribute for hover tooltips
    display_data = []
    for _, row in df.iterrows():
        row_data = {}
        for col in df.columns:
            cell_value = str(row[col]) if row[col] is not None else ""
            # Add title attribute for hover tooltip showing full content
            row_data[col] = cell_value
        display_data.append(row_data)
    
    return DataTable(
        id="table-results-datatable",
        data=display_data,
        columns=columns,
        row_selectable=False,
        selected_rows=[],
        cell_selectable=False,
        virtualization=False,
        page_action='none',
        style_cell={
            "whiteSpace": "nowrap",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
            "maxWidth": "300px",
            "padding": "10px 5px",
            "cursor": "pointer",
        },
        style_cell_conditional=[
            {
                "if": {"column_id": col},
                "textAlign": "left",
            }
            for col in df.columns
        ],
        style_as_list_view=True,
        style_table={
            "overflowX": "auto",
            "overflowY": "auto",
            "maxHeight": "600px",
        },
        style_header={
            "fontWeight": "bold",
            "backgroundColor": "#f8f9fa",
            "textAlign": "left",
            "padding": "10px 5px",
            "whiteSpace": "nowrap",
            "position": "sticky",
            "top": "0",
            "zIndex": "10",
        },
        style_data={
            "backgroundColor": "white",
            "border": "1px solid #ddd",
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#f9f9f9",
            }
        ],
    )


def get_selected_columns_for_display(df: pd.DataFrame, selected_columns: Optional[List[str]]) -> pd.DataFrame:
    """Return DataFrame filtered to selected columns, preserving source column order."""
    if selected_columns is None:
        return df

    selected_set = set(selected_columns)
    valid_columns = [col for col in df.columns if col in selected_set]
    return df.loc[:, valid_columns]


def get_column_selector_options(columns: List[str]) -> List[Dict[str, str]]:
    """Build dropdown options for the column selector."""
    return [{"label": col, "value": col} for col in columns]


def get_columns_from_records(records: Optional[List[Dict]]) -> List[str]:
    """Extract ordered columns from query result records."""
    if not records:
        return []

    columns = []
    seen = set()
    for row in records:
        if not isinstance(row, dict):
            continue
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def create_filter_row(filter_id: int) -> dbc.Row:
    """Create a single filter row component."""
    return dbc.Row(
        [
            dbc.Col(
                dcc.Dropdown(
                    id={"type": "filter-field", "index": filter_id},
                    placeholder="Select field...",
                    className="mb-2",
                ),
                width=3,
            ),
            dbc.Col(
                dcc.Dropdown(
                    id={"type": "filter-operator", "index": filter_id},
                    options=[
                        {"label": v["label"], "value": k}
                        for k, v in FILTER_OPERATORS.items()
                    ],
                    placeholder="Select operator...",
                    value="equals",
                    className="mb-2",
                ),
                width=3,
            ),
            dbc.Col(
                dcc.Dropdown(
                    id={"type": "filter-value", "index": filter_id},
                    placeholder="Select or type value...",
                    searchable=True,
                    clearable=True,
                    className="mb-2",
                    options=[],
                ),
                width=4,
            ),
            dbc.Col(
                dbc.Button(
                    "✕",
                    id={"type": "filter-remove-btn", "index": filter_id},
                    color="danger",
                    size="sm",
                    className="w-100",
                ),
                width=2,
            ),
        ],
        className="g-2 mb-2",
    )


# App layout
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.H1("SQLite Database Browser", className="mb-4 mt-4"),
                    width=12,
                )
            ]
        ),
        # Load Database section
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H5("Load Database", className="card-title"),
                                        dbc.InputGroup(
                                            [
                                                dbc.Input(
                                                    id="db-path-input",
                                                    placeholder="Enter path to .sqlite file",
                                                    type="text",
                                                    value="./data/db.sqlite",
                                                ),
                                                dbc.Button(
                                                    "Load", id="load-db-btn", color="primary"
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            id="db-status-message",
                                            className="mt-2 text-muted small",
                                        ),
                                    ]
                                )
                            ]
                        ),
                    ],
                    width=12,
                    lg=6,
                )
            ],
            className="mb-4",
        ),
        # Table selection section
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H5("Tables", className="card-title"),
                                        dcc.Dropdown(
                                            id="table-selector",
                                            placeholder="Select a table...",
                                            className="mb-2",
                                        ),
                                        dbc.Button(
                                            "Load Table",
                                            id="load-table-btn",
                                            color="info",
                                            size="sm",
                                        ),
                                        html.Div(
                                            id="table-info",
                                            className="mt-2 small text-muted",
                                        ),
                                    ]
                                )
                            ]
                        ),
                    ],
                    width=12,
                    lg=6,
                )
            ],
            className="mb-4",
        ),
        # Column display section
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.H5("Column Display", className="card-title mb-0"),
                                                    width="auto",
                                                ),
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Toggle",
                                                        id="toggle-column-selector-btn",
                                                        color="info",
                                                        outline=True,
                                                        size="sm",
                                                    ),
                                                    width="auto",
                                                ),
                                            ],
                                            className="mb-2",
                                        ),
                                        html.P(
                                            "Select columns to include in the table view. Unselected columns are excluded.",
                                            className="small text-muted mb-2",
                                        ),
                                        dbc.Collapse(
                                            [
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            dbc.Button(
                                                                "Select All",
                                                                id="select-all-columns-btn",
                                                                color="primary",
                                                                outline=True,
                                                                size="sm",
                                                            ),
                                                            width="auto",
                                                        ),
                                                        dbc.Col(
                                                            dbc.Button(
                                                                "Clear All",
                                                                id="clear-all-columns-btn",
                                                                color="secondary",
                                                                outline=True,
                                                                size="sm",
                                                            ),
                                                            width="auto",
                                                        ),
                                                    ],
                                                    className="mb-3",
                                                ),
                                                html.Div(
                                                    id="column-checklist-container",
                                                    style={
                                                        "maxHeight": "300px",
                                                        "overflowY": "auto",
                                                        "border": "1px solid #ddd",
                                                        "borderRadius": "4px",
                                                        "padding": "10px",
                                                    },
                                                ),
                                            ],
                                            id="column-selector-collapse",
                                            is_open=False,
                                        ),
                                        # Hidden store for column selector state
                                        dcc.Store(id="column-selector", data=None),
                                    ]
                                )
                            ]
                        ),
                    ],
                    width=12,
                )
            ],
            className="mb-4",
        ),
        # Advanced Filter Builder section
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H5("Advanced Search", className="card-title"),
                                        html.P(
                                            "Build complex queries with multiple filters (AND logic)",
                                            className="small text-muted mb-3",
                                        ),
                                        html.Div(
                                            id="filters-container",
                                            children=[create_filter_row(0)],
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Button(
                                                        "+ Add Filter",
                                                        id="add-filter-btn",
                                                        color="success",
                                                        outline=True,
                                                        size="sm",
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Apply Filters",
                                                        id="apply-filters-btn",
                                                        color="primary",
                                                        size="sm",
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Clear Filters",
                                                        id="clear-filters-btn",
                                                        color="secondary",
                                                        outline=True,
                                                        size="sm",
                                                    ),
                                                    width="auto",
                                                ),
                                            ],
                                            className="g-2",
                                        ),
                                        html.Div(
                                            id="filter-error-message",
                                            className="mt-2 text-danger small",
                                        ),
                                    ]
                                )
                            ]
                        ),
                    ],
                    width=12,
                )
            ],
            className="mb-4",
        ),
        # SQL Query section
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H5("Execute Custom Query", className="card-title"),
                                        dbc.Textarea(
                                            id="query-input",
                                            placeholder="Enter SQL query (e.g., SELECT * FROM table_name WHERE condition)",
                                            rows=4,
                                            className="mb-2",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Execute Query",
                                                        id="execute-query-btn",
                                                        color="success",
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Clear",
                                                        id="clear-query-btn",
                                                        color="secondary",
                                                        outline=True,
                                                    ),
                                                    width="auto",
                                                ),
                                            ],
                                            className="g-2",
                                        ),
                                        html.Div(
                                            id="query-error-message",
                                            className="mt-2 text-danger small",
                                        ),
                                    ]
                                )
                            ]
                        ),
                    ],
                    width=12,
                )
            ],
            className="mb-4",
        ),
        # Results section
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Tabs(
                            [
                                dbc.Tab(
                                    label="Table View",
                                    children=[
                                        html.Div(
                                            id="results-info",
                                            className="mb-3 mt-3 small text-muted",
                                        ),
                                        html.Div(
                                            id="sql-display",
                                            className="mb-3 mt-2 p-2 bg-light rounded border",
                                            style={"fontFamily": "monospace", "fontSize": "0.85rem"},
                                        ),
                                        html.H6("Table Display", className="mt-3 mb-2"),
                                        html.P("Table cells are limited to 40 characters for readability. Hover over cells or copy the text to view the full content. Use 'Export Data' to download the full dataset.", className="small text-muted"),
                                        html.Div(
                                            id="table-results",
                                            className="table-responsive",
                                        ),
                                        html.Div(
                                            id="debug-active-cell",
                                            style={"fontSize": "0.8rem", "color": "#666", "marginTop": "10px", "padding": "5px", "backgroundColor": "#f0f0f0"}
                                        ),
                                        dcc.Store(id="table-full-data-store"),

                                    ],
                                ),
                                dbc.Tab(
                                    label="Statistics",
                                    children=[
                                        html.Div(
                                            id="statistics-container",
                                            className="mt-3",
                                        ),
                                    ],
                                ),
                                dbc.Tab(
                                    label="Visualizations",
                                    children=[
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.H6("Column for Visualization:"),
                                                        dcc.Dropdown(
                                                            id="viz-column-selector",
                                                            placeholder="Select column...",
                                                        ),
                                                    ],
                                                    width=12,
                                                    lg=6,
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.H6("Visualization Type:"),
                                                        dcc.RadioItems(
                                                            id="viz-type-selector",
                                                            options=[
                                                                {"label": " Histogram", "value": "histogram"},
                                                                {"label": " Bar Chart", "value": "bar"},
                                                                {"label": " Scatter", "value": "scatter"},
                                                            ],
                                                            value="histogram",
                                                            inline=True,
                                                        ),
                                                    ],
                                                    width=12,
                                                    lg=6,
                                                ),
                                            ],
                                            className="mb-3 mt-3",
                                        ),
                                        dcc.Graph(
                                            id="data-visualization",
                                            config={"responsive": True},
                                        ),
                                    ],
                                ),
                            ]
                        ),
                    ],
                    width=12,
                )
            ]
        ),
        # Export section
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H5("Export Filtered Table", className="card-title"),
                                        dbc.InputGroup(
                                            [
                                                dbc.Input(
                                                    id="export-path-input",
                                                    placeholder="Enter directory path (e.g., C:/Users/username/Desktop)",
                                                    type="text",
                                                    value="./data/exports",
                                                ),
                                            ],
                                            className="mb-3",
                                        ),
                                        dbc.Checkbox(
                                            id="export-selected-columns-only",
                                            label="Export only currently selected/displayed columns",
                                            value=False,
                                            className="mb-3",
                                        ),
                                        dbc.Button(
                                            "Export Filtered Table",
                                            id="export-table-btn",
                                            color="primary",
                                            size="lg",
                                            className="w-100",
                                            style={
                                                "backgroundColor": "#003366",
                                                "color": "white",
                                                "fontWeight": "bold",
                                                "fontSize": "1.2rem",
                                                "padding": "15px",
                                            },
                                        ),
                                        html.Div(
                                            id="export-status-message",
                                            className="mt-2 small",
                                        ),
                                    ]
                                )
                            ]
                        ),
                    ],
                    width=12,
                )
            ],
            className="mb-4 mt-4",
        ),
        # Hidden stores for app state
        dcc.Store(id="current-data-store", storage_type="memory"),
        dcc.Store(id="current-filters-store", storage_type="memory"),
        dcc.Store(id="filter-count-store", data={"count": 1}),
        dcc.Store(id="current-table-store", storage_type="memory"),
        dcc.Store(id="table-columns-store", storage_type="memory"),
    ],
    fluid=True,
    className="mb-5",
)



# ============================================================================
# CALLBACKS
# ============================================================================


@app.callback(
    Output("db-status-message", "children"),
    Output("table-selector", "options"),
    Output("table-selector", "value"),
    Input("load-db-btn", "n_clicks"),
    State("db-path-input", "value"),
    prevent_initial_call=True,
)
def load_database(n_clicks, db_path):
    """Load database and display available tables."""
    if not db_path:
        return "Please enter a database path", [], None

    db_path = str(Path(db_path).expanduser())

    if not os.path.exists(db_path):
        return f"Error: File not found: {db_path}", [], None

    try:
        db = DatabaseConnection(db_path)
        if not db.connect():
            return "Error: Could not open database", [], None

        tables = db.get_tables()
        db.close()

        if not tables:
            return "Database loaded but no tables found", [], None

        options = [{"label": t, "value": t} for t in tables]
        # Auto-select first table
        first_table = tables[0] if tables else None
        return f"✓ Database loaded: {len(tables)} tables", options, first_table

    except Exception as e:
        return f"Error loading database: {str(e)}", [], None


@app.callback(
    Output("table-info", "children"),
    Output("table-columns-store", "data"),
    Input("load-table-btn", "n_clicks"),
    State("table-selector", "value"),
    State("db-path-input", "value"),
    prevent_initial_call=True,
)
def load_table_info(n_clicks, table_name, db_path):
    """Load table info and store column names."""
    if not table_name or not db_path:
        raise PreventUpdate

    db_path = str(Path(db_path).expanduser())
    
    try:
        db = DatabaseConnection(db_path)
        if not db.connect():
            return "Error connecting to database", None

        columns, row_count = db.get_table_info(table_name)
        db.close()

        info = f"Columns: {len(columns)} | Rows: {row_count}"
        return info, columns

    except Exception as e:
        return f"Error: {str(e)}", None


@app.callback(
    Output("filters-container", "children", allow_duplicate=True),
    Output("filter-count-store", "data"),
    Input("add-filter-btn", "n_clicks"),
    State("filters-container", "children"),
    State("filter-count-store", "data"),
    prevent_initial_call=True,
)
def add_filter(n_clicks, existing_children, store_data):
    """Add a new filter row while preserving existing filters."""
    # Get current count (defaults to 1 since we start with filter 0)
    count = store_data.get("count", 1) if store_data else 1
    
    # Preserve existing filters and append a new one with unique index
    existing_children = existing_children or []
    new_filter_index = count  # Use count as the new index
    existing_children.append(create_filter_row(new_filter_index))
    
    # Increment count for next filter
    new_count = count + 1
    
    return existing_children, {"count": new_count}


@app.callback(
    Output("filters-container", "children", allow_duplicate=True),
    Input({"type": "filter-remove-btn", "index": ALL}, "n_clicks"),
    State({"type": "filter-remove-btn", "index": ALL}, "id"),
    State({"type": "filter-field", "index": ALL}, "value"),
    State({"type": "filter-operator", "index": ALL}, "value"),
    State({"type": "filter-value", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def remove_filter(remove_clicks, button_ids, fields, operators, values):
    """Remove a filter row."""
    # Check if any button was actually clicked
    ctx = callback_context
    if not ctx.triggered or not button_ids:
        raise PreventUpdate
    
    # Ensure at least one button has actually been clicked (n_clicks > 0 indicates a real click)
    # This prevents the callback from being triggered just by component list changes
    if not remove_clicks or not any(c is not None and c > 0 for c in remove_clicks):
        raise PreventUpdate
    
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Parse which button was clicked
    try:
        clicked_button = json.loads(triggered_id)
        removed_index = clicked_button["index"]
    except:
        raise PreventUpdate
    
    # Rebuild filters excluding the removed one
    new_children = []
    new_idx = 0
    
    for i, btn_id in enumerate(button_ids):
        # Skip the filter that was removed
        if btn_id["index"] == removed_index:
            continue
        
        # Create a new filter row with sequential index
        # Preserve the values if they exist
        new_filter = create_filter_row(new_idx)
        
        # Try to preserve the field, operator, and value from the old filter
        # Note: This creates the UI structure, values will be lost but that's ok
        # since we're removing filters anyway
        new_children.append(new_filter)
        new_idx += 1
    
    # Ensure we have at least one filter
    if not new_children:
        new_children = [create_filter_row(0)]
    
    return new_children


@app.callback(
    Output("column-selector-collapse", "is_open"),
    Input("toggle-column-selector-btn", "n_clicks"),
    State("column-selector-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_column_selector(n_clicks, is_open):
    """Toggle the column selector collapse state."""
    return not is_open


@app.callback(
    Output("table-selector", "value", allow_duplicate=True),
    Output("current-table-store", "data"),
    Input("load-table-btn", "n_clicks"),
    State("table-selector", "value"),
    prevent_initial_call=True,
)
def store_table_name(n_clicks, table_name):
    """Store the current table name."""
    return table_name, table_name


@app.callback(
    Output({"type": "filter-field", "index": ALL}, "options"),
    Input("table-columns-store", "data"),
    Input({"type": "filter-field", "index": ALL}, "id"),
)
def update_filter_field_options(columns, matched_ids):
    """Update field options in all filter rows when table changes or new filters are added."""
    if not columns or not matched_ids:
        # Return empty options if no columns loaded yet
        return [[] for _ in (matched_ids or [])]
    
    options = [{"label": col, "value": col} for col in columns]
    # Return one options list for each matched component
    return [options for _ in matched_ids]


@app.callback(
    Output("column-checklist-container", "children"),
    Output("column-selector", "data"),
    Input("table-columns-store", "data"),
    Input("current-data-store", "data"),
    Input({"type": "column-checkbox", "index": ALL}, "value"),
    Input("select-all-columns-btn", "n_clicks"),
    Input("clear-all-columns-btn", "n_clicks"),
    State("column-selector", "data"),
    State({"type": "column-checkbox", "index": ALL}, "id"),
)
def update_column_selector(
    table_columns,
    current_data,
    checkbox_values,
    select_all_clicks,
    clear_all_clicks,
    current_selection,
    checkbox_ids,
):
    """Render column checklist and manage selection state."""
    data_columns = get_columns_from_records(current_data)
    available_columns = data_columns or (table_columns or [])

    if not available_columns:
        return html.P("No columns available", className="text-muted small"), None

    ctx = callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    # Determine selected columns based on trigger
    if trigger_id == "select-all-columns-btn":
        selected_columns = available_columns
    elif trigger_id == "clear-all-columns-btn":
        selected_columns = []
    elif trigger_id in {"current-data-store", "table-columns-store"}:
        # Default: select all on new dataset load
        selected_columns = available_columns
    elif "column-checkbox" in str(trigger_id):
        # User toggled a checkbox - build selection from checkbox states
        selected_columns = []
        for checkbox_id, checked in zip(checkbox_ids, checkbox_values):
            if checked:
                selected_columns.append(checkbox_id["index"])
    else:
        # Preserve current selection
        selected_columns = current_selection if current_selection is not None else available_columns

    # Build 6-column checklist layout
    num_cols = 6
    num_columns = len(available_columns)
    rows = []
    
    for i in range(0, num_columns, num_cols):
        cols = []
        for j in range(num_cols):
            idx = i + j
            if idx < num_columns:
                col_name = available_columns[idx]
                is_checked = col_name in (selected_columns or [])
                cols.append(
                    dbc.Col(
                        dbc.Checkbox(
                            id={"type": "column-checkbox", "index": col_name},
                            label=col_name,
                            value=is_checked,
                            className="mb-2",
                        ),
                        width=2,
                    )
                )
            else:
                cols.append(dbc.Col(width=2))
        
        rows.append(dbc.Row(cols, className="g-2"))
    
    return html.Div(rows), selected_columns


@app.callback(
    Output({"type": "filter-value", "index": ALL}, "options"),
    Input({"type": "filter-field", "index": ALL}, "value"),
    Input({"type": "filter-operator", "index": ALL}, "value"),
    Input({"type": "filter-value", "index": ALL}, "search_value"),
    State("current-table-store", "data"),
    State("db-path-input", "value"),
    State({"type": "filter-value", "index": ALL}, "id"),
    State({"type": "filter-value", "index": ALL}, "value"),
)
def update_filter_value_options(fields, operators, search_values, table_name, db_path, value_ids, current_values):
    """Update value dropdown options based on selected field and operator."""
    if not table_name or not db_path or not value_ids:
        # Return empty options for each filter value component
        return [[] for _ in (value_ids or [])]
    
    # Ensure all lists have the same length by padding with None
    num_filters = len(value_ids)
    fields = (fields or []) + [None] * (num_filters - len(fields or []))
    operators = (operators or []) + [None] * (num_filters - len(operators or []))
    search_values = (search_values or []) + [None] * (num_filters - len(search_values or []))
    current_values = (current_values or []) + [None] * (num_filters - len(current_values or []))
    
    try:
        db_path = str(Path(db_path).expanduser())
        db = DatabaseConnection(db_path)
        if not db.connect():
            return [[] for _ in value_ids]
        
        # For each filter row, get unique values if operator is "equals"
        results = []
        for idx in range(num_filters):
            field = fields[idx]
            operator = operators[idx] if idx < len(operators) else None
            search_val = search_values[idx] if idx < len(search_values) else None
            current_val = current_values[idx] if idx < len(current_values) else None
            
            if field and operator == "equals":
                # Get unique values from the database for equals operator
                # First check count to avoid long waits on high-cardinality columns
                try:
                    cursor = db.conn.cursor()
                    
                    # First, quickly check how many distinct values exist
                    count_query = (
                        f'SELECT COUNT(DISTINCT "{field}") FROM "{table_name}" '
                        f'WHERE "{field}" IS NOT NULL'
                    )
                    cursor.execute(count_query)
                    distinct_count = cursor.fetchone()[0]
                    
                    # Only fetch values if count is reasonable (<= 50 to keep it fast)
                    if distinct_count > 0 and distinct_count <= 50:
                        # Safe to fetch all unique values
                        value_query = (
                            f'SELECT DISTINCT "{field}" FROM "{table_name}" '
                            f'WHERE "{field}" IS NOT NULL ORDER BY "{field}" LIMIT 50'
                        )
                        cursor.execute(value_query)
                        unique_values = [row[0] for row in cursor.fetchall()]
                        cursor.close()
                        
                        options = [
                            {"label": str(val), "value": str(val)}
                            for val in unique_values
                        ]
                        results.append(options)
                    else:
                        # Too many unique values - skip dropdown population
                        cursor.close()
                        if distinct_count > 50:
                            print(f"Field '{field}' has {distinct_count} unique values - skipping dropdown (use free text)")
                        results.append([])
                except Exception as e:
                    print(f"Error fetching unique values: {e}")
                    results.append([])
            else:
                # For non-equals operators (like, not_like, etc.), create dynamic options from typed text
                # This allows free text entry by adding whatever the user types as an option
                # Always preserve current value if it exists
                options_to_add = []
                
                if current_val:
                    # User has a value set - always include it
                    options_to_add.append({"label": str(current_val), "value": str(current_val)})
                
                if search_val and search_val != current_val:
                    # User is actively typing something different - add it too
                    options_to_add.append({"label": str(search_val), "value": str(search_val)})
                
                results.append(options_to_add)
        
        db.close()
        return results
    except Exception as e:
        print(f"Error in update_filter_value_options: {e}")
        return [[] for _ in value_ids]
        return [[] for _ in value_ids]


@app.callback(
    Output("filter-error-message", "children"),
    Output("table-results", "children"),
    Output("results-info", "children"),
    Output("sql-display", "children"),
    Output("current-data-store", "data"),
    Output("viz-column-selector", "options"),
    Output("viz-column-selector", "value"),
    Output("table-full-data-store", "data"),
    Output("current-filters-store", "data"),
    Input("apply-filters-btn", "n_clicks"),
    Input("load-table-btn", "n_clicks"),
    State({"type": "filter-field", "index": ALL}, "value"),
    State({"type": "filter-operator", "index": ALL}, "value"),
    State({"type": "filter-value", "index": ALL}, "value"),
    State("column-selector", "data"),
    State("current-table-store", "data"),
    State("db-path-input", "value"),
    prevent_initial_call=True,
)
def apply_filters(
    apply_clicks,
    load_clicks,
    fields,
    operators,
    values,
    selected_columns,
    table_name,
    db_path,
):
    """Apply filters to table."""
    if not table_name or not db_path:
        raise PreventUpdate

    db_path = str(Path(db_path).expanduser())

    # Build filter objects
    filters = []
    for field, operator, value in zip(fields or [], operators or [], values or []):
        if field:  # Only add filters with a field selected
            filters.append({
                "field": field,
                "operator": operator or "equals",
                "value": value or "",
            })

    try:
        db = DatabaseConnection(db_path)
        if not db.connect():
            return "Error: Could not connect to database", "", "", "", None, [], None, None, None

        df, error, sql_query = db.get_table_data(table_name, filters=filters)
        db.close()

        if error:
            return f"Query Error: {error}", "", "", f"Error in query: {sql_query}", None, [], None, None, filters

        if df.empty:
            return (
                "",
                html.P("No results found."),
                "No results found",
                sql_query,
                None,
                [],
                None,
                None,
                filters,
            )

        # Apply optional column selection for display
        display_df = get_selected_columns_for_display(df, selected_columns)

        if display_df.shape[1] == 0:
            return (
                "",
                html.P("No columns selected. Choose at least one column in Column Display."),
                f"Showing {len(df)} rows, 0 columns (all columns excluded)",
                sql_query,
                df.to_dict("records"),
                [],
                None,
                {},
                filters,
            )

        # Create table from results
        table = create_table_with_truncation(display_df)

        # Results info
        info = f"Showing {len(display_df)} rows, {len(display_df.columns)} of {len(df.columns)} columns"

        # Column options for visualization
        all_cols = display_df.columns.tolist()
        col_options = [{"label": col, "value": col} for col in all_cols]
        viz_value = all_cols[0] if all_cols else None

        # Store full query data so column display can be changed without re-running query
        df_data = df.to_dict("records")
        
        # Store displayed data (before truncation) for click-to-view feature
        # Create a dictionary with string keys for both row indices and column names
        full_data_dict = {}
        for row_idx, (_, row) in enumerate(display_df.iterrows()):
            row_key = str(row_idx)
            full_data_dict[row_key] = {}
            for col in display_df.columns:
                col_key = str(col)
                full_data_dict[row_key][col_key] = str(row[col])

        # Format SQL display
        sql_display = html.Code(f"SQL: {sql_query}")

        return "", table, info, sql_display, df_data, col_options, viz_value, full_data_dict, filters

    except Exception as e:
        return f"Error: {traceback.format_exc()}", "", "", "", None, [], None, None, None


@app.callback(
    Output("filters-container", "children", allow_duplicate=True),
    Output("filter-error-message", "children", allow_duplicate=True),
    Input("clear-filters-btn", "n_clicks"),
    prevent_initial_call=True,
)
def clear_filters(n_clicks):
    """Clear all filters."""
    return [create_filter_row(0)], ""


@app.callback(
    Output("query-input", "value", allow_duplicate=True),
    Input("clear-query-btn", "n_clicks"),
    prevent_initial_call=True,
)
def clear_query(n_clicks):
    """Clear query input."""
    return ""


@app.callback(
    Output("table-results", "children", allow_duplicate=True),
    Output("results-info", "children", allow_duplicate=True),
    Output("query-error-message", "children"),
    Output("sql-display", "children", allow_duplicate=True),
    Output("current-data-store", "data", allow_duplicate=True),
    Output("viz-column-selector", "options", allow_duplicate=True),
    Output("viz-column-selector", "value", allow_duplicate=True),
    Output("table-full-data-store", "data", allow_duplicate=True),
    Output("current-filters-store", "data", allow_duplicate=True),
    Input("execute-query-btn", "n_clicks"),
    State("query-input", "value"),
    State("db-path-input", "value"),
    State("column-selector", "data"),
    prevent_initial_call=True,
)
def execute_custom_query(n_clicks, query, db_path, selected_columns):
    """Execute custom SQL query."""
    if not query or not db_path:
        raise PreventUpdate

    db_path = str(Path(db_path).expanduser())

    if not os.path.exists(db_path):
        return "", "", "Database file not found", "", None, [], None, None, None

    try:
        db = DatabaseConnection(db_path)
        if not db.connect():
            return "", "", "Error: Could not connect to database", "", None, [], None, None, None

        df, error = db.execute_query(query)
        db.close()

        if error:
            return "", "", f"Query Error: {error}", f"SQL: {query}", None, [], None, None, None

        if df.empty:
            return (
                html.P("No results found."),
                "No results found",
                "",
                f"SQL: {query}",
                None,
                [],
                None,
                None,
                None,
            )

        # Apply optional column selection for display
        display_df = get_selected_columns_for_display(df, selected_columns)

        if display_df.shape[1] == 0:
            return (
                html.P("No columns selected. Choose at least one column in Column Display."),
                f"Showing {len(df)} rows, 0 columns (all columns excluded)",
                "",
                f"SQL: {query}",
                df.to_dict("records"),
                [],
                None,
                {},
                None,
            )

        # Create table from results
        table = create_table_with_truncation(display_df)

        # Results info
        info = f"Showing {len(display_df)} rows, {len(display_df.columns)} of {len(df.columns)} columns"

        # Column options for visualization
        all_cols = display_df.columns.tolist()
        col_options = [{"label": col, "value": col} for col in all_cols]
        viz_value = all_cols[0] if all_cols else None

        # Store full query data so column display can be changed without re-running query
        df_data = df.to_dict("records")
        
        # Store displayed data (before truncation) for click-to-view feature
        # Create a dictionary with string keys for both row indices and column names
        full_data_dict = {}
        for row_idx, (_, row) in enumerate(display_df.iterrows()):
            row_key = str(row_idx)
            full_data_dict[row_key] = {}
            for col in display_df.columns:
                col_key = str(col)
                full_data_dict[row_key][col_key] = str(row[col])

        return table, info, "", f"SQL: {query}", df_data, col_options, viz_value, full_data_dict, None

    except Exception as e:
        return (
            "",
            "",
            f"Error: {traceback.format_exc()}",
            f"SQL: {query}",
            None,
            [],
            None,
            None,
            None,
        )


@app.callback(
    Output("table-results", "children", allow_duplicate=True),
    Output("results-info", "children", allow_duplicate=True),
    Output("viz-column-selector", "options", allow_duplicate=True),
    Output("viz-column-selector", "value", allow_duplicate=True),
    Output("table-full-data-store", "data", allow_duplicate=True),
    Input("column-selector", "data"),
    State("current-data-store", "data"),
    prevent_initial_call=True,
)
def apply_column_selection_to_display(selected_columns, current_data):
    """Apply selected columns to the current result set without re-running SQL."""
    if not current_data:
        raise PreventUpdate

    df = pd.DataFrame(current_data)

    if df.empty:
        return html.P("No results found."), "No results found", [], None, {}

    display_df = get_selected_columns_for_display(df, selected_columns)

    if display_df.shape[1] == 0:
        return (
            html.P("No columns selected. Choose at least one column in Column Display."),
            f"Showing {len(df)} rows, 0 columns (all columns excluded)",
            [],
            None,
            {},
        )

    table = create_table_with_truncation(display_df)
    info = f"Showing {len(display_df)} rows, {len(display_df.columns)} of {len(df.columns)} columns"
    col_options = [{"label": col, "value": col} for col in display_df.columns]
    viz_value = display_df.columns[0] if len(display_df.columns) > 0 else None

    full_data_dict = {}
    for row_idx, (_, row) in enumerate(display_df.iterrows()):
        row_key = str(row_idx)
        full_data_dict[row_key] = {}
        for col in display_df.columns:
            col_key = str(col)
            full_data_dict[row_key][col_key] = str(row[col])

    return table, info, col_options, viz_value, full_data_dict




@app.callback(
    Output("data-visualization", "figure"),
    Input("current-data-store", "data"),
    Input("column-selector", "data"),
    Input("viz-column-selector", "value"),
    Input("viz-type-selector", "value"),
)
def update_visualization(data, selected_columns, column, viz_type):
    """Update visualization based on selected column and type."""
    if not data or not column:
        return {
            "data": [],
            "layout": go.Layout(
                title="Select a column to visualize",
                xaxis={"title": "X"},
                yaxis={"title": "Y"},
            ),
        }

    df = pd.DataFrame(data)
    df = get_selected_columns_for_display(df, selected_columns)

    if df.shape[1] == 0:
        return {
            "data": [],
            "layout": go.Layout(
                title="No columns selected for visualization",
                xaxis={"title": "X"},
                yaxis={"title": "Y"},
            ),
        }

    if column not in df.columns:
        return {
            "data": [],
            "layout": go.Layout(
                title="Column not found",
                xaxis={"title": "X"},
                yaxis={"title": "Y"},
            ),
        }

    try:
        if viz_type == "histogram":
            fig = px.histogram(
                df,
                x=column,
                title=f"Distribution of {column}",
                nbins=30,
            )
        elif viz_type == "bar":
            # For bar chart, use value counts
            value_counts = df[column].value_counts().head(20)
            fig = px.bar(
                x=value_counts.index,
                y=value_counts.values,
                title=f"Top 20 values in {column}",
                labels={"x": column, "y": "Count"},
            )
        elif viz_type == "scatter":
            # For scatter, create a simple scatter with index
            fig = px.scatter(
                df,
                y=column,
                title=f"Scatter plot of {column}",
                labels={"index": "Row", "y": column},
            )
        else:
            fig = px.histogram(df, x=column, title=f"Distribution of {column}")

        fig.update_layout(height=500, hovermode="x unified")
        return fig

    except Exception as e:
        return {
            "data": [],
            "layout": go.Layout(
                title=f"Error creating visualization: {str(e)}",
                xaxis={"title": "X"},
                yaxis={"title": "Y"},
            ),
        }


@app.callback(
    Output("statistics-container", "children"),
    Input("current-data-store", "data"),
    Input("column-selector", "data"),
)
def update_statistics(data, selected_columns):
    """Display basic statistics about the data."""
    if not data:
        return html.P("Load data first to see statistics")

    df = pd.DataFrame(data)
    df = get_selected_columns_for_display(df, selected_columns)

    if df.shape[1] == 0:
        return html.P("No columns selected for statistics")

    # Get numeric columns
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if not numeric_cols:
        return html.P("No numeric columns found for statistics")

    # Create statistics table
    stats_data = []
    for col in numeric_cols:
        stats_data.append(
            {
                "Column": col,
                "Count": df[col].count(),
                "Mean": f"{df[col].mean():.2f}",
                "Std Dev": f"{df[col].std():.2f}",
                "Min": f"{df[col].min():.2f}",
                "Max": f"{df[col].max():.2f}",
            }
        )

    if not stats_data:
        return html.P("No statistics available")

    stats_df = pd.DataFrame(stats_data)
    stats_table = create_table_with_truncation(stats_df)

    return dbc.Card(
        dbc.CardBody(
            [
                html.H6("Numeric Column Statistics"),
                stats_table,
            ]
        )
    )


@app.callback(
    Output("debug-active-cell", "children"),
    Input("table-results-datatable", "id"),
)
def show_table_info(table_id):
    """Show info about the table."""
    return "Use the search and filter features above to find and query data. Cells display up to 40 characters - copy full text as needed."


@app.callback(
    Output("export-status-message", "children"),
    Output("export-status-message", "className"),
    Input("export-table-btn", "n_clicks"),
    State("export-path-input", "value"),
    State("export-selected-columns-only", "value"),
    State("column-selector", "data"),
    State("current-filters-store", "data"),
    State("current-table-store", "data"),
    State("db-path-input", "value"),
    prevent_initial_call=True,
)
def export_filtered_table(
    n_clicks,
    export_path,
    export_selected_only,
    selected_columns,
    filters,
    table_name,
    db_path,
):
    """Export the filtered table to a TSV file with timestamp.
    Re-executes the query without LIMIT to get all matching rows."""
    if not table_name or not db_path:
        return "No data to export. Please load and filter a table first.", "mt-2 small text-danger"
    
    if not export_path:
        return "Please enter a directory path.", "mt-2 small text-danger"
    
    try:
        # Expand user path and create Path object
        export_dir = Path(export_path).expanduser()
        
        # Check if directory exists
        if not export_dir.exists():
            # Try to create the directory
            try:
                export_dir.mkdir(parents=True, exist_ok=True)
            except Exception as mkdir_error:
                return f"Error: Directory does not exist and could not be created: {export_path}", "mt-2 small text-danger"
        
        if not export_dir.is_dir():
            return f"Error: Path is not a directory: {export_path}", "mt-2 small text-danger"
        
        # Re-execute the query WITHOUT the LIMIT to get all data
        db_path_expanded = str(Path(db_path).expanduser())
        db = DatabaseConnection(db_path_expanded)
        if not db.connect():
            return "Error: Could not connect to database", "mt-2 small text-danger"
        
        # Get ALL data by passing limit=None
        df, error, sql_query = db.get_table_data(table_name, filters=filters or [], limit=None)
        db.close()
        
        if error:
            return f"Query Error: {error}", "mt-2 small text-danger"
        
        if df.empty:
            return "No data to export (query returned 0 rows).", "mt-2 small text-danger"

        exported_df = df
        export_sql_query = sql_query
        
        if export_selected_only:
            exported_df = get_selected_columns_for_display(df, selected_columns)
            if exported_df.shape[1] == 0:
                return (
                    "Export failed: no columns selected. Select at least one column or uncheck selected-columns-only export.",
                    "mt-2 small text-danger",
                )
            
            # Build SQL query with explicit column names instead of SELECT *
            selected_col_names = ', '.join([f'"{col}"' for col in exported_df.columns])
            export_sql_query = sql_query.replace('SELECT *', f'SELECT {selected_col_names}', 1)
        
        # Create timestamp in YYYYMMDD_hhmmss format
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create filenames
        basename = f"{timestamp}_dataset_browser_export"
        tsv_filename = f"{basename}.tsv"
        query_filename = f"{basename}_query.txt"
        
        tsv_path = export_dir / tsv_filename
        query_path = export_dir / query_filename
        
        # Export data to TSV
        exported_df.to_csv(tsv_path, sep="\t", index=False)
        
        # Export SQL query to text file
        with open(query_path, "w", encoding="utf-8") as f:
            f.write(export_sql_query)
        
        return (
            f"✓ Successfully exported {len(exported_df)} rows and {len(exported_df.columns)} columns to: {tsv_path}\n"
            f"✓ SQL query saved to: {query_path}"
        ), "mt-2 small text-success"
        
    except Exception as e:
        return f"Error exporting file: {str(e)}", "mt-2 small text-danger"


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
