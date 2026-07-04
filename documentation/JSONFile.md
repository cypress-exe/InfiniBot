# Documentation for `JSONFile`

This document provides an overview of the `JSONFile` class, its purpose, properties, and methods. 
The `JSONFile` class is a utility for interacting with JSON configuration files, offering convenient 
methods to read, write, and manage data stored in JSON format.

---

## `JSONFile`

The `JSONFile` class is designed to simplify interaction with JSON files. It handles file creation, 
reading, writing, and ensures data integrity by validating file content.

### Caching

`JSONFile` keeps a class-level in-memory cache of parsed file contents, keyed by file path and 
shared across all instances pointing at the same file. Reads are served from the cache (no disk 
I/O or JSON parsing after the first read); writes go through to disk and update the cache 
(write-through), so the cache is always authoritative. `delete_file()` evicts the file's cache 
entry.

Two consequences to be aware of:

- **All reads return copies.** Mutating a dict returned by `_get_data()`, `items()`, etc. does 
  not affect the cache or the file — persist changes via `__setitem__`/`add_variable` as usual.
- **External edits are not seen.** Editing a JSON file on disk while the bot is running will not 
  be picked up until restart (or a `clear_cache()` call), because reads no longer touch disk. 
  All runtime writes must go through `JSONFile`.

### Constructor

```python
JSONFile(name: str)
```

#### Parameters:
- `name` (str): The base name of the JSON file (without the `.json` extension). 
  The file will be located at `./generated/configure/{name}.json`.

---

### Properties

#### `name`
- **Type**: `str`
- The base name of the JSON file.

#### `file_name`
- **Type**: `str`
- The complete name of the file, including the `.json` extension.

#### `path`
- **Type**: `str`
- The full file path where the JSON file is stored.

---

### Methods

#### `ensure_existence`
Ensures the JSON file exists and is well-formed. If the file does not exist, it is created with 
an empty JSON object. If the file is malformed, it is deleted and recreated.

```python
JSONFile.ensure_existence()
```

---

#### `_get_data`
Retrieves the content of the JSON file as a Python dictionary.

```python
data = JSONFile._get_data()
```

#### `_set_data`
Writes a Python dictionary to the JSON file, overwriting its content.

```python
JSONFile._set_data(data: dict)
```

- **Parameters**:
  - `data` (dict): The dictionary to save in the JSON file.

---

#### `__contains__`
Checks if a key exists in the JSON file.

```python
key in JSONFile
```

#### `__getitem__`
Retrieves the value associated with a key from the JSON file.

```python
value = JSONFile[key]
```

- **Raises**:
  - `KeyError`: If the key does not exist.

#### `__setitem__`
Updates the value of an existing key in the JSON file.

```python
JSONFile[key] = value
```

- **Raises**:
  - `KeyError`: If the key does not exist. Use `add_variable()` for new keys.

#### `__delitem__`
Deletes a key-value pair from the JSON file.

```python
del JSONFile[key]
```

- **Raises**:
  - `KeyError`: If the key does not exist.

#### `__iter__`
Iterates over the keys in the JSON file.

```python
for key in JSONFile:
    print(key)
```

#### `__str__`
Returns a string representation of the JSON file's content.

```python
str(JSONFile)
```

#### `__len__`
Returns the number of key-value pairs in the JSON file.

```python
len(JSONFile)
```

#### `__dict__`
Returns the content of the JSON file as a dictionary.

```python
dict_representation = JSONFile.__dict__()
```

#### `add_variable`
Adds a new key-value pair to the JSON file.

```python
JSONFile.add_variable(key: str, value: Any)
```

- **Parameters**:
  - `key` (str): The key to add.
  - `value` (Any): The value to associate with the key.

- **Raises**:
  - `KeyError`: If the key already exists. Use `__setitem__()` to update an existing key.

#### `delete_file`
Deletes the JSON file from disk and evicts it from the in-memory cache.

```python
JSONFile.delete_file()
```

- **Warning**: This action is irreversible.

#### `clear_cache`
Evicts this file's entry from the in-memory cache. The next read re-parses the file from disk. 
Only needed if the file was modified outside of `JSONFile` (e.g., a manual edit while running).

```python
JSONFile.clear_cache()
```

---

### Summary

The `JSONFile` class provides an intuitive and efficient way to manage JSON configuration files in Python. 
Its methods ensure data integrity and simplify operations such as adding, updating, or removing entries.
