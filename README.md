# SQLite Database Browser - Plotly Dash App

A Python/web-based database browser for querying and visualizing SQLite databases. Built with Plotly Dash, it provides an intuitive interface for loading databases, exploring tables, building advanced search queries, visualizing results with interactive charts, and exporting full filtered results.

## Features

- **Database Loading**: Load any SQLite database (.sqlite files)
- **Table Browser**: View all tables and their metadata (column names, row counts)
- **Advanced Search**: Modular filter builder with 11 different operators (equals, contains, comparisons, NULL checks, and more)
- **SQL Query Execution**: Write and execute custom SQL queries
- **Results Display**: View query results in an interactive HTML table with SQL preview
- **Data Visualization**: Built-in histograms, bar charts, and scatter plots with Plotly
- **Statistics**: View summary statistics for numeric columns
- **Export**: Export filtered query results to TSV (including your SQL query)

## Installation

### Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) package manager (fast Rust-based Python package installer)

### Install uv (if you don't have it already)

Visit [uv's installation guide](https://docs.astral.sh/uv/getting-started/installation/) for installation methods.

### Setup

Dependencies are managed through `pyproject.toml`. Install them with:

```bash
uv sync
```

## Usage

### Starting the App

```bash
uv run python dash_app.py
```

The app will start "locally" (only on your computer) on `http://127.0.0.1:8050` - open your browser and navigate there.

### Workflow

1. **Load Database**
   - Enter the path to your `.sqlite` file (e.g. `C:\path\to\database.sqlite` or `./data/db.sqlite`)
   - Click "Load" button
   - The app will display available tables

2. **Select a Table**
   - Choose a table from the dropdown
   - Click "Load Table"
   - The app displays table info (columns, row count)
   - Filter field selectors are populated with column names

3. **Build Advanced Search Queries** (Recommended)
   - Use the "Advanced Search" section to build queries without SQL
   - Select a field → Choose an operator → Enter a value (manually typed values must be folowed by the Enter key)
   - Click "+ Add Filter" to add multiple conditions (it's all "AND" logic)
   - Supported operators: equals, contains, comparisons, NULL checks, and more
   - Click "Apply Filters" to see results
   - See [ADVANCED_SEARCH_GUIDE.md](docs/ADVANCED_SEARCH_GUIDE.md) for detailed examples or refer to the ["Advanced Search Operators"](#advanced-search-operators) section below

4. **Execute Custom SQL Queries** (Optional):
   - Write custom SQL queries in the "Execute Custom Query" section
   - Click "Execute Query" to run
   - Results appear in the "Table View" tab
   - The generated SQL is shown for reference

5. **Analyze Data**:
   - Switch to the "Statistics" tab to see numeric column summaries
   - Switch to "Visualizations" to view simple plots
   - Select a column and visualization type (Histogram/Bar/Scatter)

## Advanced Search Operators

The filter builder supports 11 operators for powerful searching:

| Operator | Best For | Example |
|----------|----------|---------|
| **equals** | Exact match | `status = "active"` |
| **does not equal** | Filtering out values | `status != "inactive"` |
| **like (contains)** | Substring search | `name LIKE "%john%"` |
| **not like** | Exclude patterns | `name NOT LIKE "%test%"` |
| **less than** | Range queries | `age < 30` |
| **less than or equal** | Range boundaries | `age <= 65` |
| **greater than** | Minimum values | `score > 80` |
| **greater than or equal** | Minimum thresholds | `score >= 70` |
| **in** | Multiple values | `status IN (val1, val2, val3)` |
| **is null** | Missing data | `optional_field IS NULL` |
| **is not null** | Non-null values | `optional_field IS NOT NULL` |

## Examples

### Using Advanced Search: Find Participants by Dataset

```text
Field: "ent__sub"
Operator: like (contains)
Value: "MOA"
Result: Shows all participants with "MOA" in ent__sub field
```

### Using Advanced Search: Multiple Conditions

```text
Filter 1: "age" > 30
Filter 2: "status" = "active"
Result: All records where age > 30 AND status = active
```

### Custom SQL Examples

```sql
SELECT * FROM "table_name" LIMIT 100
```

### Filtered Query

```sql
SELECT column1, column2 FROM "participants" WHERE age > 30 LIMIT 1000
```

### Aggregation

```sql
SELECT condition, COUNT(*) as count FROM "data" GROUP BY condition
```

### Query Limits

- By default, queries are limited to the first 500 rows to prevent memory issues with large databases

## Limitations

- Read-only access (no INSERT/UPDATE/DELETE)
- No connection pooling (single connection per session)
- Limited to SQLite format
- Performance may degrade with very large datasets (over 100k rows)
