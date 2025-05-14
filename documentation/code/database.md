# Documentation for `Database`

This document provides an overview of the `Database` class, its purpose, properties, and methods.
The `Database` class is a utility for managing an SQLite database, offering methods to execute queries, 
build and index tables, and perform various database operations.

---

## `Database`

The `Database` class is designed for interacting with SQLite databases. It abstracts complex database operations
and provides an intuitive API for managing tables and their entries.

### Constructor

```python
Database(db_url: str, db_build_file_path: str)
```

#### Parameters:
- `db_url` (str): The URL of the SQLite database.
- `db_build_file_path` (str): Path to the instructions file for building the database.

---

### Properties

#### `engine`
- **Type**: `sqlalchemy.engine.Engine`
- SQLAlchemy engine for the database connection.

#### `Session`
- **Type**: `sqlalchemy.orm.sessionmaker`
- SQLAlchemy session class for database transactions.

#### `tables`
- **Type**: `list[str]`
- A list of table names in the database.

#### `tables_to_optimize`
- **Type**: `list[str]`
- A list of tables marked for optimization.

#### `all_column_defaults`
- **Type**: `dict[str, dict[str, str]]`
- A dictionary mapping table names to their column default values.

#### `all_column_types`
- **Type**: `dict[str, dict[str, str]]`
- A dictionary mapping table names to their column data types.

#### `all_column_names`
- **Type**: `dict[str, list[str]]`
- A dictionary mapping table names to their column names.

#### `all_primary_keys`
- **Type**: `dict[str, str]`
- A dictionary mapping table names to their primary key column names.

---

### Methods

#### `execute_query`
Executes an SQL query.

```python
Database.execute_query(
    sql: str, args: dict = {}, commit: bool = False, multiple_values: bool = False
)
```

- **Parameters**:
  - `sql` (str): The SQL query to execute.
  - `args` (dict, optional): Query parameters.
  - `commit` (bool, optional): Whether to commit changes to the database.
  - `multiple_values` (bool, optional): Whether to return multiple query results.

- **Returns**:
  - Query result(s) as a single value or a list, based on `multiple_values`.

---

#### `build_database`
Builds the database by executing instructions from a file.

```python
Database.build_database(build_file_path: str)
```

- **Parameters**:
  - `build_file_path` (str): Path to the build file.

---

#### `index_tables`
Indexes all tables in the database.

```python
Database.index_tables()
```

---

#### `remove_extraneous_rows`
Removes rows matching default values from a table marked for optimization.

```python
Database.remove_extraneous_rows(
    table: str, skip_table_validation_check: bool = False
)
```

- **Parameters**:
  - `table` (str): Table name.
  - `skip_table_validation_check` (bool, optional): Skip validation for optimization markers.

---

#### `optimize_database`
Optimizes the database by removing extraneous rows from tables marked for optimization.

```python
Database.optimize_database()
```

---

#### `force_remove_entry`
Removes an entry from a table.

```python
Database.force_remove_entry(table: str, id: int)
```

- **Parameters**:
  - `table` (str): Table name.
  - `id` (int): Entry ID.

---

#### `get_column_default`
Retrieves the default value of a column.

```python
Database.get_column_default(
    table: str, column_name: str, format: bool = False
)
```

- **Parameters**:
  - `table` (str): Table name.
  - `column_name` (str): Column name.
  - `format` (bool, optional): Format the default value to its Python type.

- **Returns**:
  - Default value of the column.

---

#### `get_column_type`
Retrieves the data type of a column.

```python
Database.get_column_type(table: str, column_name: str)
```

- **Parameters**:
  - `table` (str): Table name.
  - `column_name` (str): Column name.

- **Returns**:
  - Data type of the column.

---

#### `get_query_first_value`
Simplifies query results to a single value or tuple.

```python
Database.get_query_first_value(query_result: list[tuple])
```

- **Parameters**:
  - `query_result` (list[tuple]): Raw query results.

- **Returns**:
  - Simplified query result.

---

#### `does_entry_exist`
Checks if an entry exists in a table.

```python
Database.does_entry_exist(table: str, id: int)
```

- **Parameters**:
  - `table` (str): Table name.
  - `id` (int): Entry ID.

- **Returns**:
  - `True` if the entry exists, `False` otherwise.

---

#### `get_table_unique_entries`
Retrieves unique entries from a specific table.

```python
Database.get_table_unique_entries(table: str)
```

- **Parameters**:
  - `table` (str): Table name.

- **Returns**:
  - A generator yielding unique IDs.

---

#### `get_unique_entries_for_database`
Retrieves unique entries from all tables.

```python
Database.get_unique_entries_for_database()
```

- **Returns**:
  - List of unique IDs.

---

#### `get_id_sql_name`
Retrieves the primary key column name of a table.

```python
Database.get_id_sql_name(table: str)
```

- **Parameters**:
  - `table` (str): Table name.

- **Returns**:
  - SQL name of the primary key.

---

### Summary

The `Database` class provides a comprehensive toolkit for managing SQLite databases. 
Its methods simplify database operations, ensuring efficiency and consistency.
