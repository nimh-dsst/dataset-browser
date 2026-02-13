# SQLite Database Browser - Plotly Dash App

A Python/web-based database browser for querying and visualizing large SQLite databases. Built with Plotly Dash, it provides similar functionality to the Flutter app but with a web interface.

## Features

- **Database Loading**: Load any SQLite database (.sqlite files)
- **Table Browser**: View all tables and their metadata (column names, row counts)
- **Advanced Search**: Modular filter builder with 11 different operators (equals, contains, comparisons, NULL checks, and more)
- **SQL Query Execution**: Write and execute custom SQL queries
- **Results Display**: View query results in an interactive HTML table with SQL preview
- **Data Visualization**: Create histograms, bar charts, and scatter plots with Plotly
- **Statistics**: View summary statistics for numeric columns
- **Responsive Design**: Works on desktop and tablets with Bootstrap styling

## Installation

### Prerequisites
- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) package manager (fast Rust-based Python package installer)

### Install uv (if you don't have it)

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

Or visit [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv) for other installation methods.

### Setup

Dependencies are managed through `pyproject.toml`. Install them with:

```bash
uv sync
```

This creates a virtual environment and installs all required packages.

## Usage

### Starting the App

**Option 1: Quick Start (Interactive)**
```bash
python quickstart.py
```
This will:
- Automatically install uv if needed
- Check for any missing dependencies via `uv sync`
- Find SQLite files on your system
- Launch the app and open your browser

**Option 2: Manual Start**
```bash
uv sync      # Install dependencies (once per setup)
uv run dash_app.py
```

**Option 3: Direct with uv (if deps already synced)**
```bash
uv run dash_app.py
```

The app will start on `http://127.0.0.1:8050` - open your browser and navigate there.

## Dependencies

All dependencies are defined in `pyproject.toml` for easy management with uv:
- **dash** - Web framework for interactive dashboards
- **plotly** - Interactive visualizations
- **pandas** - Data manipulation
- **dash-bootstrap-components** - Bootstrap styling
- **dash-extensions** - Additional Dash utilities
- **dash-ag-grid** - Advanced data grid component
- **fastparquet** - For Parquet file support

### Workflow

1. **Load Database**: 
   - Enter the path to your `.sqlite` file (e.g., `C:\path\to\database.sqlite` or `./data.sqlite`)
   - Click "Load" button
   - The app will display available tables

2. **Select a Table**:
   - Choose a table from the dropdown
   - Click "Load Table" 
   - The app displays table info (columns, row count)
   - Filter field selectors are populated with column names

3. **Build Advanced Search Queries** (Recommended):
   - Use the "Advanced Search" section to build queries without SQL
   - Select a field → Choose an operator → Enter a value
   - Click "+ Add Filter" to add multiple conditions (AND logic)
   - Supported operators: equals, contains, comparisons, NULL checks, and more
   - Click "Apply Filters" to see results
   - See [ADVANCED_SEARCH_GUIDE.md](ADVANCED_SEARCH_GUIDE.md) for detailed examples

4. **Execute Custom SQL Queries** (Optional):
   - Write custom SQL queries in the "Execute Custom Query" section
   - Click "Execute Query" to run
   - Results appear in the "Table View" tab
   - The generated SQL is shown for reference

5. **Analyze Data**:
   - Switch to the "Statistics" tab to see numeric column summaries
   - Switch to "Visualizations" to create plots
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
```
Field: "ds_dataset"
Operator: like (contains)
Value: "moa"
Result: Shows all participants with "moa" in dataset field
```

### Using Advanced Search: Multiple Conditions
```
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

### Join Query
```sql
SELECT a.id, a.name, b.value 
FROM "table_a" a 
JOIN "table_b" b ON a.id = b.a_id 
LIMIT 500
```

## Components

### Main Sections

1. **Load Database**: File path input and database connection
2. **Tables**: List of available tables with selector
3. **Execute Query**: SQL textarea and execution controls
4. **Results Tabs**:
   - Table View: Interactive data table (max 1000 rows displayed)
   - Statistics: Summary statistics for numeric columns
   - Visualizations: Plotly interactive charts

### Query Limits

- By default, queries are limited to the first 1000 rows to prevent memory issues with large databases
- You can modify this in the code by changing the `limit` parameter in the `execute_query` method

## Tips & Tricks

### For Large Databases
- Use WHERE clauses to filter data before visualization
- Use LIMIT to restrict results
- Aggregate data with GROUP BY before visualizing

### Example: Filtering Before Visualization
```sql
SELECT age FROM "participants" WHERE age IS NOT NULL AND age < 120
```

### Column Selection
- The visualization tab only shows columns that exist in your query results
- Only numeric columns appear in the statistics tab

### Performance
- The app displays up to 1000 rows in tables
- Visualizations work with your current data (200-1000 rows)
- For larger aggregations, use SQL to pre-aggregate: `GROUP BY`, `SUM()`, etc.

## Troubleshooting

### "Database file not found"
- Check the path is correct (use forward slashes or escaped backslashes)
- Use absolute paths: `C:/Users/username/Desktop/data.sqlite`

### "No tables found"
- The database may have no tables
- Verify the file is a valid SQLite database

### Query Error: "no such table"
- Check table name spelling (case-sensitive)
- Use quotes around table names: `SELECT * FROM "table_name"`

### Visualizations not appearing
- Ensure you have numeric data in the selected column
- Try a histogram first, it works with most data types
- Check results table for actual data values

## Architecture

The app consists of:

- **DatabaseConnection**: Manages SQLite connections and queries
- **UI Components**: Dash/Bootstrap layout with organized sections
- **Callbacks**: Real-time event handlers for loading, querying, and visualization
- **Plotly Integration**: Interactive charts and statistics

## Future Enhancements

Potential additions:
- Export query results to CSV/Excel
- Save query history and favorites
- Advanced filtering UI
- Multi-table joins helper
- Data profiling and data quality checks
- Query builder UI for non-SQL users

## Limitations

- Read-only access (no INSERT/UPDATE/DELETE)
- Maximum 1000 rows displayed at once
- No connection pooling (single connection per session)
- Limited to SQLite format

## Related Files

- `parquets2db.py`: Convert Parquet files to SQLite databases
- `app/`: Original Flutter implementation for reference
