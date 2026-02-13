# Advanced Search & Filter Builder

The SQLite Database Browser now includes a powerful advanced search interface with a modular filter builder, allowing you to create complex queries without writing SQL.

## Features

### Filter Types Supported

| Operator | Description | Example |
|----------|-------------|---------|
| **equals** | Exact match | `field = "value"` |
| **does not equal** | Excludes matches | `field != "value"` |
| **like (contains)** | Substring search with wildcards | `field LIKE "%substr%"` |
| **not like** | Excludes substring matches | `NOT LIKE "%substr%"` |
| **less than** | Numeric comparison | `field < 100` |
| **less than or equal** | Numeric comparison | `field <= 100` |
| **greater than** | Numeric comparison | `field > 100` |
| **greater than or equal** | Numeric comparison | `field >= 100` |
| **in** | Match one of multiple values | `field IN (val1, val2, val3)` |
| **is null** | Find NULL/empty values | `field IS NULL` |
| **is not null** | Exclude NULL/empty values | `field IS NOT NULL` |

## How to Use

### 1. Load Your Database

1. Enter the path to your SQLite database (e.g., `/path/to/data.sqlite`)
2. Click **Load**
3. Confirm the database loaded and shows table count

### 2. Select a Table

1. Choose a table from the dropdown
2. Click **Load Table**
3. The app will:
   - Display table metadata (columns, row count)
   - Populate the filter field selectors with available columns

### 3. Build Your Search Query

The Advanced Search section provides a modular filter builder:

```
┌─────────────────────────────────────────────────────────┐
│ Advanced Search                                           │
│ Build complex queries with multiple filters (AND logic)  │
│                                                           │
│ [Field Dropdown]  [Operator Dropdown] [Value Input] [✕]  │
│ [Field Dropdown]  [Operator Dropdown] [Value Input] [✕]  │
│                                                           │
│ [+ Add Filter] [Apply Filters] [Clear Filters]          │
└─────────────────────────────────────────────────────────┘
```

#### Step-by-Step Process:

1. **Select a Field**: Click the first dropdown and choose a column name
2. **Choose an Operator**: Select from the 11 available operators
3. **Enter a Value**: Type the value to search for
   - For "in" operator: comma-separated values (e.g., `value1, value2, value3`)
   - For "like" operator: partial text (e.g., "search" will find "research", "searching")
   - For NULL operators: leave empty (value is ignored)
4. **Add More Filters** (optional): Click "+ Add Filter" to add more conditions
5. **Apply Filters**: Click "Apply Filters" to execute the query

### 4. View Results

Results appear in three tabs:

- **Table View**: Interactive table showing matching records (max 1000 rows)
  - Displays the generated SQL query
  - Shows record count and column count
- **Statistics**: Summary statistics for numeric columns
- **Visualizations**: Create charts from the results

## Search Examples

### Example 1: Simple Equals Search
Find all participants with a specific MRN:

```
Field: "mrn_id"
Operator: equals
Value: "04M0222"
```
**Generates SQL**: `SELECT * FROM participants WHERE "mrn_id" = "04M0222"`

### Example 2: Substring Search (Contains)
Find all entries containing "moa" in the dataset field:

```
Field: "ds_dataset"
Operator: like (contains)
Value: "moa"
```
**Generates SQL**: `SELECT * FROM data WHERE "ds_dataset" LIKE "%moa%"`

This will match: "moa_3T", "MOA_7T", "moa_baseline", etc.

### Example 3: Multiple Filters (AND Logic)
Find participants over 30 years old AND from study group "A":

```
Filter 1:
  Field: "age"
  Operator: greater than
  Value: "30"

Filter 2:
  Field: "study_group"
  Operator: equals
  Value: "A"
```
**Generates SQL**: `SELECT * FROM participants WHERE "age" > 30 AND "study_group" = "A"`

### Example 4: IN Operator
Find records matching any of multiple values:

```
Field: "status"
Operator: in
Value: "active, pending, review"
```
**Generates SQL**: `SELECT * FROM data WHERE "status" IN (active, pending, review)`

### Example 5: NULL Checking
Find records with missing data:

```
Field: "optional_field"
Operator: is null
Value: (leave empty)
```
**Generates SQL**: `SELECT * FROM data WHERE "optional_field" IS NULL`

## Advanced Usage

### Complex Multi-Field Searches

Build complex queries by adding multiple filters. All filters are combined with **AND** logic:

```
Filter 1: age >= 18
Filter 2: age <= 65
Filter 3: status = "active"
Filter 4: department LIKE "%research%"
```

**Result**: All 4 conditions must be true

### Modifying Filters

- **Add Filter**: Click "+ Add Filter" to add another condition
- **Remove Filter**: Click the red "✕" button for any filter row to remove it
- **Clear Filters**: Click "Clear Filters" to reset all filters to default state

## SQL Query Display

After applying filters, the exact SQL query is displayed in the results section:

```
SQL: SELECT * FROM "particles" WHERE "age" > 25 AND "status" LIKE "%active%"
```

You can copy this and use it directly in custom queries or other tools.

## Custom SQL Queries

For even more advanced queries, use the "Execute Custom Query" section:

```sql
SELECT column1, column2, COUNT(*) as count
FROM "table_name"
WHERE age > 25
GROUP BY status
ORDER BY count DESC
LIMIT 100
```

The filter builder covers 80% of use cases, but the custom query section is available for complex aggregations, joins, and other advanced SQL operations.

## Tips & Best Practices

### Performance Tips

1. **Filter before visualizing**: Use the search filters to reduce data before creating visualizations
2. **Use LIKE wisely**: Substring searches can be slow on large tables
   - Use with keywords: `LIKE "%substring%"` works, but is slower
   - Prefer exact matches when possible
3. **Numeric comparisons**: Much faster than text searches on large datasets

### Common Patterns

**Find duplicates:**
- Use custom SQL: `SELECT field, COUNT(*) FROM table GROUP BY field HAVING COUNT(*) > 1`

**Exclude values:**
- Use "does not equal" or "NOT LIKE"

**Range queries:**
- Use two filters: `age >= 18` AND `age <= 65`

**Partial matches:**
- Use "like (contains)" for text fields

### When to Use Filters vs. Custom Queries

**Use the Filter Builder when:**
- Searching for simple conditions
- Need quick, interactive exploration
- Want to avoid writing SQL
- Learning what data exists

**Use Custom Queries when:**
- Need aggregations (COUNT, SUM, AVG, etc.)
- Joining multiple tables
- Complex nested conditions
- Computing derived values

## Troubleshooting

### "No results found"
- Check for typos in your search values
- Try a less restrictive search (fewer filters or broader text)
- Remember: text matching is case-sensitive

### Filter field dropdown empty
- Make sure you selected a table first ("Load Table")
- Check the database has columns
- Reload the table

### Query runs slowly
- Too many filters with LIKE operators?
- Try using numeric operators (faster)
- Reduce dataset before visualizing
- Use custom SQL with LIMIT clause

### Special characters in search values
- For text with quotes: the app handles escaping automatically
- For comma-separated "IN" values: values with commas need quotes in custom SQL

## Filter Operator Reference

### Text Matching

**Exact Match:**
```
Field: "category"
Operator: equals
Value: "A"
Result: category = "A"
```

**Contains (Substring):**
```
Field: "name"
Operator: like (contains)
Value: "john"
Result: name LIKE "%john%"
Matches: "john", "John", "John Smith", "johnson"
```

**Multiple Values:**
```
Field: "status"
Operator: in
Value: "active, pending, approved"
Result: status IN ('active', 'pending', 'approved')
```

### Numeric Comparisons

All support numbers (integers and decimals):
```
Field: "age"
Operator: greater than
Value: "25"
Result: age > 25
```

### NULL Checks

Find missing/empty values:
```
Field: "optional_data"
Operator: is null
Value: (ignored)
Result: optional_data IS NULL
```

## Architecture Notes

The filter builder:
- Creates dynamic filter UI with add/remove buttons
- Stores filter state in browser (Dash Store)
- Builds parameterized SQL queries (safe from injection)
- Supports AND logic (multiple conditions all apply)
- Shows the generated SQL for transparency
- Works with all field types (text, numeric, date)

Each filter generates safe SQL with proper parameter binding to prevent SQL injection.
