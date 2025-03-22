# Documentation for `Simple_TableManager` and `IntegratedList_TableManager`

This document provides an overview of the `Simple_TableManager` and `IntegratedList_TableManager` classes, their purposes, properties, and methods. These classes facilitate interaction with SQL tables for managing data linked by a primary key.

---

## `Simple_TableManager`
The `Simple_TableManager` class provides an abstraction for managing individual entries in a specific SQL table keyed by a primary key.

### Constructor
```python
Simple_TableManager(primary_id: int, table_name: str)
```
#### Parameters:
- `primary_id` (int): The primary ID that the table entry corresponds to.
- `table_name` (str): The name of the SQL table.

---

### Properties

#### `primary_id`
- **Type**: `int`
- The ID that this manager interacts with.

#### `table_name`
- **Type**: `str`
- The name of the SQL table this manager interacts with.

#### `primary_id_sql_name`
- **Type**: `str`
- The name of the primary key column in the SQL table.

#### `_entry_exists_in_table`
- **Type**: `bool`
- Indicates whether the entry exists in the table for the specified ID.

---

### Methods

#### `__str__`
Returns a string representation of the manager with column names and their types.

#### `__dict__`
Returns a dictionary of column names and their corresponding values from the SQL table.

#### `get_column_names_and_types`
Returns:
- **Type**: `dict`
- A dictionary mapping column names to their SQL types.

#### `get_column_names_and_defaults`
Returns:
- **Type**: `dict`
- A dictionary mapping column names to their default values.

#### `_ensure_existence`
Ensures an entry with the primary_id exists in the table. Creates the entry if it does not exist.

#### `_init_regular_entry`
Creates a new entry for with the primary_id.
- **Parameters**:
  - `table` (str): The table name.
  - `primary_id` (int): The primary ID.

#### `_get_variable`
Retrieves a variable from the SQL table.
- **Parameters**:
  - `table` (str): The table name.
  - `column` (str): The column name.
  - `primary_id` (int): The primary ID.

#### `_set_variable`
Updates a variable in the SQL table.
- **Parameters**:
  - `table` (str): The table name.
  - `column` (str): The column name.
  - `id` (int): The ID value to target.
  - `value` (Any): The value to set.

#### Decorators for Properties

##### `custom_property`
Defines a custom property for handling SQL data.
- **Parameters**:
  - `property_name` (str): The name of the property.
  - `getter_modifier` (callable, optional): A function to modify the value when retrieved.
  - `setter_modifier` (callable, optional): A function to modify the value when set.

##### `integer_property`
Defines a regular property for integers.
Set `accept_none_value` to false to mark none values as invalid input.

##### `float_property`
Defines a regular property for floats.

##### `boolean_property`
Defines a regular property for booleans.

##### `string_property`
Defines a regular property for strings.
Set `accept_none_value` to true to mark none values as valid input.

##### `typed_property`
Defines a regular property for integers, floats, booleans, and strings with support for `None` and `UNSET_VALUE`.
Set `accept_none_value` to false to mark none values as invalid input.
Set `accept_unset_value` to false to mark UNSET values as invalid input.
Set `enforce_numerical_values` to true to disable strings as valid input. Numerical strings will be automatically converted to integers.

##### `list_property`
Defines a regular property for lists.
Set `accept_duplicate_values` to false to mark duplicate values as invalid input.

##### `embed_property`
Defines an irregular property for embeds, supporting serialization and deserialization.
- Custom Properties:
  - Add / Edit property:
    ```python
    embed = this.profile.embed_property
    embed["color"] = "Blue"
    this.profile.embed_property = embed 
    ```
  - Remove property:
    ```python
    embed = this.profile.embed_property
    embed.["color"] = None
    this.profile.embed_property = embed 
    ```
  - Convert to Discord embed:
    ```python
    embed:nextcord.Embed = this.profile.embed_property.to_embed()
    ```
---

#### Editing Regular Properties

When working with regular properties, editing follows an intutive, pythonic structure.

```python
this.profile.active = True
```

#### Editing Irregular Properties

When working with some properties, editing must follow a specific pattern due to the hierarchical structure of these properties and the inability to automatically save hierarchical elements. Here's how you can edit irregular properties:

```python
prop = this.profile.irregular_property
prop["subproperty"] = "Hello world"
this.profile.irregular_property = prop
```

**Key Points:**
- You must first retrieve the property into a variable.
- Modify the variable, such as changing a subproperty.
- Assign the modified variable back to the property.

---

## `IntegratedList_TableManager`
The `IntegratedList_TableManager` class provides tools for managing lists of complex, keyed data in SQL tables. This is useful for managing relationships with primary and secondary keys.

### Constructor
```python
IntegratedList_TableManager(
    table_name: str,
    primary_key_sql_name: str,
    primary_key_value: str,
    secondary_key_sql_name: str
)
```
#### Parameters:
- `table_name` (str): The name of the SQL table.
- `primary_key_sql_name` (str): The primary key column name.
- `primary_key_value` (str): The value of the primary key.
- `secondary_key_sql_name` (str): The secondary key column name.

---

### Methods

#### `dataclass`
Represents a row in the table.
- **Methods**:
  - `get_data()`: Returns a dictionary representation of the row.
  - `__str__()`: Returns a string representation of the row.

#### `_get_entry`
Retrieves an entry based on the secondary key value.
- **Parameters**:
  - `second_key_value` (str): The secondary key value.

#### `_get_all_entries`
Yields all entries in the list.
- **Returns**:
  - Generator of `dataclass` instances.

#### `_get_all_secondary_values`
Returns all unique secondary key values.

#### `_get_all_matching_indexes`
Finds all secondary key values matching specified criteria.
- **Parameters**:
  - `columns` (dict): The column-value pairs to match.

#### `_package_list_into_dataclass`
Packages a SQL row into a `dataclass`.

#### `_check_entry_existence`
Checks if an entry exists for a given secondary key.
- **Parameters**:
  - `secondary_key_value` (str): The secondary key value.

#### `_sync_dictionary_with_table`
Syncs a dictionary with the SQL table to validate data.
- **Parameters**:
  - `data_dict` (dict): The dictionary to validate.

#### `_update_entry_using_dict`
Updates an entry using a dictionary of values.
- **Parameters**:
  - `secondary_key_value` (str): The secondary key value.
  - `data_dict` (dict): The dictionary of data to update.

#### CRUD Operations

##### `add`
Adds a new entry to the table.
- **Parameters**:
  - `kwargs`: Key-value pairs for the new entry.

##### `edit`
Edits an existing entry.
- **Parameters**:
  - `secondary_key_value` (str): The secondary key value.
  - `kwargs`: Key-value pairs for the updated data.

##### `delete`
Deletes an entry based on the secondary key value.
- **Parameters**:
  - `secondary_key_value` (str): The secondary key value.

#### Viewing Data

##### Access an Entry
To retrieve a specific entry using its secondary key:
```python
entry = table_manager[secondary_key_value]
print(entry)  # Outputs the dataclass representation of the entry
```

##### List All Entries
To view all entries in the table:
```python
for entry in table_manager:
    print(entry)
```

##### View a Specific Column of an Entry
To retrieve the value of a specific column for an entry:
```python
entry = table_manager[secondary_key_value]
specific_column_value = entry.column_name
print(specific_column_value)
```

#### Editing Data

##### Modify an Entry
To edit an existing entry:
```python
table_manager.edit(secondary_key_value, column_name=value, ...)
```
- Replace `secondary_key_value` with the secondary key for the entry.
- Provide column-value pairs for the fields you want to update.

##### Add a New Entry
To add a new entry:
```python
table_manager.add(column_name=value, ...)
```
- Ensure all required fields are included as keyword arguments.

##### Delete an Entry
To delete an entry:
```python
table_manager.delete(secondary_key_value)
```

---

### Dunder Methods

- `__getitem__(self, second_key_value)`:
  - Retrieves an entry using the `[]` operator.

- `__len__()`:
  - Returns the number of entries.

- `__contains__(self, secondary_key_value)`:
  - Checks if an entry exists in the table.

- `__iter__()`:
  - Returns an iterator for all entries.

- `__str__()`:
  - Returns a string representation of all entries.