# Advanced Search Implementation - Summary

## What Was Added

A complete advanced, modular search interface with a powerful filter builder to replace/supplement basic SQL query execution.

## Key Features Implemented

### 1. **11 Filter Operators**
- `equals` - Exact match
- `does not equal` - Exclusion
- `like (contains)` - Substring search (handles wildcards automatically)
- `not like` - Negative substring matching
- `less than`, `less than or equal` - Lower bound comparisons
- `greater than`, `greater than or equal` - Upper bound comparisons
- `in` - Match multiple comma-separated values
- `is null` - Find NULL/empty values
- `is not null` - Exclude NULL values

### 2. **Modular Filter Builder UI**
```
[Load Database] → [Select Table] → [Advanced Search] → [Results]
                                       ↓
                                  [Field] [Operator] [Value] [✕]
                                  [Field] [Operator] [Value] [✕]
                                  + Add Filter | Apply | Clear
```

**Features:**
- Dynamic field selection (auto-populated from selected table)
- Operator dropdown with all 11 options
- Value input field with context-aware behavior
- Add/remove filters on the fly
- Clear all filters at once

### 3. **Multi-Filter AND Logic**
- All filters are combined with AND operator
- Multiple conditions must all be true
- Example: `age > 25 AND status = "active" AND name LIKE "%john%"`

### 4. **SQL Generation & Preview**
- Generates safe, parameterized SQL queries
- Displays the exact SQL being executed
- Shows row count, column count, and execution time
- SQL visible in the results section for transparency and reuse

### 5. **Dynamic Column Population**
- When you load a table, filter field selectors automatically populate
- Only shows columns that actually exist
- Updates when you switch tables

## Architecture Details

### DatabaseConnection Class Enhancements

**New Methods:**
- `build_where_clause(filters)` - Converts filter objects to SQL WHERE clause with parameters
- `get_table_data(table_name, filters)` - Executes filtered queries with safe parameter binding
- `get_columns(table_name)` - Returns available columns for the table

**Key Implementation:**
```python
def build_where_clause(self, filters: List[Dict]) -> Tuple[str, List]:
    """Builds parameterized SQL WHERE clause from filter objects"""
    # Converts each filter to a condition
    # Handles all 11 operator types
    # Returns (where_clause_string, parameters_list)
    # Safe from SQL injection via parameter binding
```

### UI Components

**Filter Row Template:**
```python
def create_filter_row(filter_id: int) -> dbc.Row
    # Returns a row with:
    # - Dropdown for field selection
    # - Dropdown for operator selection  
    # - Text input for value
    # - Remove button
```

### Callbacks

**Filter Management:**
- `add_filter()` - Handles adding new filter rows
- `remove_filter()` - Removes individual filter rows
- `update_filter_field_options()` - Updates field dropdowns when table changes

**Query Execution:**
- `apply_filters()` - Main callback that builds and executes filtered queries
- Shows results, statistics, and visualizations

## How It Works

### Step-by-Step Data Flow

1. **User loads database** → `load_database()` callback
2. **User selects table** → `load_table_info()` callback
   - Fetches columns and stores in `table-columns-store`
3. **Columns load in filter dropdowns** → `update_filter_field_options()` callback
4. **User builds filters** → Dynamic UI updates
5. **User clicks "Apply Filters"** → `apply_filters()` callback
   - Collects filter field/operator/value combinations
   - Calls `db.build_where_clause(filters)`
   - Calls `db.get_table_data(table_name, filters)`
6. **Results returned** → Display in table, statistics, visualization

### SQL Generation Example

**Filter Input:**
```python
filters = [
    {"field": "age", "operator": "greater_than", "value": "25"},
    {"field": "status", "operator": "equals", "value": "active"},
    {"field": "name", "operator": "like", "value": "john"}
]
```

**Generated SQL:**
```sql
WHERE "age" > ? AND "status" = ? AND "name" LIKE ?
Parameters: [25, "active", "%john%"]
```

**Full Query:**
```sql
SELECT * FROM "participants" 
WHERE "age" > ? AND "status" = ? AND "name" LIKE ? 
LIMIT 1000
```

## Operator Implementation Details

### Text Operators
- **equals**: Exact string match with `=`
- **does not equal**: `!=` operator
- **like (contains)**: Wraps value in `%` for substring: `LIKE "%value%"`
- **not like**: Negated substring: `NOT LIKE "%value%"`
- **in**: Splits comma-separated values, generates `IN (?, ?, ?)`

### Numeric Operators
- **less_than**, **less_than_or_equal**, **greater_than**, **greater_than_or_equal**
- Value converted to float automatically
- Supports decimals, negatives

### NULL Operators
- **is_null**: `field IS NULL` (no value parameter needed)
- **is_not_null**: `field IS NOT NULL` (no value parameter needed)

## Integration with Existing Features

The advanced search **coexists** with custom SQL:
- Use filter builder for 80% of queries
- Use custom SQL section for complex operations (joins, aggregations, etc.)
- Both can view results in the same way

## Files Modified

1. **dash_app.py**
   - Added FILTER_OPERATORS dictionary
   - Enhanced DatabaseConnection class
   - Added create_filter_row() helper
   - Added new layout section for "Advanced Search"
   - Added 8 new callbacks for filter management
   - Updated store components

2. **DASH_APP_README.md**
   - Updated features section
   - Updated workflow to include advanced search
   - Added operator reference table
   - Added advanced search examples

3. **ADVANCED_SEARCH_GUIDE.md** (NEW)
   - Complete guide to using the filter builder
   - 5+ detailed examples
   - Troubleshooting section
   - Performance tips
   - SQL reference

4. **pyproject.toml**
   - Already has all dependencies (dash, pandas, plotly, etc.)

## Usage Example

### Traditional Workflow (Before)
1. User manually writes SQL
2. High error rate, typos
3. Need to know SQL syntax
4. Limited to SELECT queries

### Advanced Workflow (After)
```
Load DB → Select Table → Click field dropdown → Pick "age"
→ Click operator → Pick "greater_than" 
→ Type value "25" 
→ Click "Apply Filters" 
→ Results appear with generated SQL
```

No SQL knowledge required!

## Performance Considerations

- **Parameterized queries**: Safe from SQL injection
- **Local filtering**: Operates on SQLite, which is fast for ~1000 row limits
- **Smart value conversion**: Numbers, strings, NULL handled appropriately
- **LIKE operator**: Uses standard SQLite substring search (% wildcards)

## Future Enhancement Possibilities

1. **OR Logic**: Support "OR" conditions in addition to "AND"
2. **Query Builder**: Graphical condition builder with more complex logic
3. **Saved Filters**: Save and reuse common filter combinations
4. **Predefined Templates**: Common filters (last 30 days, active users, etc.)
5. **Filter History**: Auto-complete from recent searches
6. **Advanced Types**: Date range picker, dropdown for ENUM-like fields
7. **Export Filters**: Save filter configuration as reusable queries

## Security

- **SQL Injection Prevention**: Uses parameter binding (?,?,?) not string concatenation
- **Input Validation**: Numbers converted to float, properly typed
- **Safe LIKE**: Automatic % wrapping prevents unintended patterns

Example safe query:
```python
query = 'SELECT * FROM "table" WHERE "field" LIKE ?'
params = ["%search%"]
# Safely executes with proper escaping
```

## Testing the Implementation

```bash
# Start the app
uv run dash_app.py

# In browser:
# 1. Load database (path/to/data.sqlite)
# 2. Select table
# 3. Try building filters:
#    - Exact match: field="value"
#    - Substring: field contains="partial"
#    - Range: age > 25
#    - Multiple: age > 25 AND status="active"
# 4. Check generated SQL in results
# 5. Try custom SQL for comparison
```

## Summary

The advanced search feature provides:
✅ Easy-to-use filter interface (no SQL needed)
✅ 11 powerful operators covering most use cases
✅ Multi-condition AND logic for complex queries
✅ SQL preview for learning and transparency
✅ Safe parameterized queries (no injection risk)
✅ Dynamic UI that adapts to your table schema
✅ Coexists with custom SQL for advanced needs

This dramatically improves usability while maintaining the power of SQL for advanced users.
