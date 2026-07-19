import copy
import functools
import json
import logging
import os

base_path = "./generated/configure/"

def update_base_path(new_path: str) -> None:
    """
    Updates the base path for JSON files.

    :param new_path: The new base path.
    :type new_path: str
    :return: None
    :rtype: None
    """
    global base_path
    base_path = new_path
    _read_txt_to_list_cached.cache_clear()

def read_txt_to_list(file_name: str) -> list:
    """
    Reads a text file and returns its contents as a list of lines.  
    Commented out lines (#) and empty lines are ignored.

    :param file_name: The name of the text file.
    :type file_name: str
    :return: A list of lines from the text file.
    :rtype: list
    """
    file_path = os.path.join(base_path, file_name)

    if not os.path.exists(file_path):
        logging.error(f"{file_path} does not exist.")
        return []

    with open(file_path, "r") as file:
        lines = file.readlines()
    
    result = []
    for index, line in enumerate(lines):
        # Ignore empty lines and lines starting with #
        line_strip = line.strip()
        if line_strip == "" or line_strip.startswith("#"):
            continue
        
        result.append(line_strip)

    return result

@functools.lru_cache(maxsize=32)
def _read_txt_to_list_cached(file_name: str, _base_path: str) -> tuple:
    """
    Cached variant of :func:`read_txt_to_list` for internal use.

    :param file_name: The name of the text file.
    :type file_name: str
    :param _base_path: No Op. Used for caching purposes only. The base path for the text file.
    :type _base_path: str
    :return: A tuple of lines from the text file.
    :rtype: tuple
    """
    # _base_path is part of the cache key only; read_txt_to_list reads the global.
    return tuple(read_txt_to_list(file_name))

def read_txt_to_list_cached(file_name: str) -> list:
    """
    Cached variant of :func:`read_txt_to_list` for files that don't change while
    InfiniBot is running (the shipped defaults). Callers on hot paths should use this
    rather than paying a disk read and parse per call.

    Edits to the file are picked up on the next restart.

    :param file_name: The name of the text file.
    :type file_name: str
    :return: A list of lines from the text file.
    :rtype: list
    """
    return list(_read_txt_to_list_cached(file_name, base_path))

class JSONFile:
    """
    Represents a JSON file.

    :param name: The base name of the JSON file (without the `.json` extension).
    :type name: str
    :return: An instance of the JSONFile object.
    :rtype: JSONFile

    How to use:
    >>> file = JSONFile("example")
    >>> file.add_variable("key", "value")
    >>> print(file.get_variable("key"))
    'value'
    """

    _cache: dict[str, dict] = {}   # keyed by absolute path -> parsed data
    
    def __init__(self, name):
        self.name = name
        self.file_name = f"{name}.json"
        self.path = os.path.join(base_path, self.file_name)

    def ensure_existence(self) -> None:
        """
        Ensures that the file exists.

        :param self: The instance of the JSONFile object.
        :type self: JSONFile
        :return: None
        :rtype: None
        """
        if not os.path.exists(self.path):
            logging.info(f"Creating {self.path}.")
            with open(self.path, "w") as file:
                file.write("{}")

        else:
            # Ensure file is not malformed
            try:
                with open(self.path, "r") as file:
                    json.loads(file.read())
            except json.JSONDecodeError:
                logging.error(f"{self.path} is malformed. Deleting file.")
                try:
                    os.rename(self.path, f"{self.path}.bak")
                    self.ensure_existence()
                except OSError as e:
                    logging.error(f"Failed to backup malformed file {self.path}: {e}")
                    try:
                        os.remove(self.path)
                        self.ensure_existence()
                    except OSError as e2:
                        logging.error(f"Failed to remove malformed file {self.path}: {e2}")

    def _get_data(self, mutable: bool = False) -> dict:
        """
        Retrieves the data from the file.

        :param mutable: If True, return a deep copy the caller may mutate (for write
            paths). If False (default), return the cached dict directly — callers
            must treat it as read-only. Read paths are hot (per-message feature
            checks), so they must not deep-copy the whole file.
        :type mutable: bool
        :return: The data from the file.
        :rtype: dict
        """
        if self.path not in self._cache:
            self.ensure_existence()
            with open(self.path, "r") as file:
                self._cache[self.path] = json.loads(file.read())

        data = self._cache[self.path]
        return copy.deepcopy(data) if mutable else data
        
    def _set_data(self, data: dict) -> None:
        """
        Sets the data in the file.

        :param data: The data to set.
        :type data: dict
        :return: None~
        :rtype: None
        """
        self.ensure_existence()

        # Atomic write: dump to a temp file and os.replace() it over the target, so a
        # crash mid-write can't leave malformed JSON (which ensure_existence would
        # 'repair' by silently resetting all settings to defaults).
        serialized = json.dumps(data, indent=2)
        temp_path = f"{self.path}.tmp"
        with open(temp_path, "w") as file:
            file.write(serialized)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, self.path)

        self._cache[self.path] = json.loads(serialized)  # Store a copy to prevent external modifications & ensure consistent formatting

    def _update_nested(self, data: dict, keys: list, value: any) -> None:
        """
        Recursively updates a nested dictionary.

        :param data: The dictionary to update.
        :type data: dict
        :param keys: The list of keys to recursively update.
        :type keys: list
        :param value: The value to set to the last key in the list.
        :type value: any
        :return: None
        :rtype: None
        """
        if len(keys) > 1:
            key = keys[0]
            if key not in data or not isinstance(data[key], dict):
                data[key] = {}
            self._update_nested(data[key], keys[1:], value)
        else:
            data[keys[0]] = value

    def _get_nested(self, data: dict, keys: list) -> any:
        """
        Recursively retrieves a value from a nested dictionary.

        :param data: The dictionary to traverse.
        :type data: dict
        :param keys: The list of keys to recursively traverse.
        :type keys: list
        :return: The value at the nested location.
        :rtype: any
        :raises KeyError: If any key in the path doesn't exist.
        """
        current = data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                raise KeyError(f"Key path {'.'.join(keys)} does not exist")
            current = current[key]
        return current

    def _exists_nested(self, data: dict, keys: list) -> bool:
        """
        Recursively checks if a nested key path exists in a dictionary.

        :param data: The dictionary to check.
        :type data: dict
        :param keys: The list of keys to check.
        :type keys: list
        :return: Whether the nested key path exists.
        :rtype: bool
        """
        current = data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]
        return True

    def __contains__(self, key: str) -> bool:
        """
        Check if a key exists in the JSON file.
        Supports dot notation for nested keys (e.g., 'user.settings.theme').

        :param key: The key to check.
        :type key: str
        :return: Whether the key exists.
        :rtype: bool
        """
        data = self._get_data()
        if isinstance(key, str) and '.' in key:
            keys = key.split('.')
            return self._exists_nested(data, keys)
        else:
            return key in data

    def __getitem__(self, key: str) -> any:
        """
        Retrieves the value associated with a key from the JSON file.
        Supports dot notation for nested keys (e.g., 'user.settings.theme').

        :param key: The key to retrieve.
        :type key: str
        :return: The value associated with the key.
        :type: any
        :raises KeyError: If the key does not exist in the JSON file.
        """
        data = self._get_data()

        try:
            if isinstance(key, str) and '.' in key:
                value = self._get_nested(data, key.split('.'))
            else:
                value = data[key]
        except KeyError:
            raise KeyError(f"{key} does not exist in {self.file_name}.")

        # Deep-copy only the returned value so callers can't mutate the cache
        return copy.deepcopy(value)

    def __setitem__(self, key: str, value: any) -> None:
        """
        Sets the value of a key in the JSON file.

        :param key: The key to set.
        :type key: str
        :param value: The value to set.
        :type value: any
        :return: None
        :rtype: None
        """
        data = self._get_data(mutable=True)
        if isinstance(key, str) and '.' in key:
            keys = key.split('.')
            self._update_nested(data, keys, value)
        else:
            data[key] = value
        self._set_data(data)

    def __delitem__(self, key: str) -> None:
        """
        Deletes a key-value pair from the JSON file.
        Supports dot notation for nested keys (e.g., 'user.settings.theme').

        :param key: The key to delete.
        :type key: str
        :return: None
        :rtype: None
        :raises KeyError: If the key does not exist in the JSON file.
        """
        data = self._get_data(mutable=True)

        if key not in self:
            raise KeyError(f"{key} does not exist in {self.file_name}.")

        if isinstance(key, str) and '.' in key:
            keys = key.split('.')
            # Navigate to the parent and delete the final key
            parent = data
            for k in keys[:-1]:
                parent = parent[k]
            del parent[keys[-1]]
        else:
            del data[key]
        self._set_data(data)

    def __iter__(self) -> iter:
        """
        Return an iterator over the keys in the JSON file.

        :param self: The instance of the JSONFile object.
        :type self: JSONFile
        :return: An iterator over the keys in the JSON file.
        :rtype: iter
        """
        data = self._get_data()
        return iter(list(data))  # snapshot the keys so writes during iteration can't break it
    
    def __str__(self) -> str:
        """
        Return a string representation of the data.

        :param self: The instance of the JSONFile object.
        :type self: JSONFile
        :return: A string representation of the data in the JSON file.
        :rtype: str
        """
        data = self._get_data()
        return str(data)
    
    def __len__(self) -> int:
        """
        Return the number of key-value pairs in the JSON file.

        :param self: The instance of the JSONFile object.
        :type self: JSONFile
        :return: The number of key-value pairs in the JSON file.
        :rtype: int
        """
        data = self._get_data()
        return len(data)
    
    def to_dict(self) -> dict:
        """
        Return a dictionary representation of the data in the JSON file.

        :param self: The instance of the JSONFile object.
        :type self: JSONFile
        :return: A dictionary representation of the data in the JSON file.
        :rtype: dict
        """
        return self._get_data(mutable=True)

    def add_variable(self, key, value) -> None:
        """
        Adds a new key-value pair to the JSON file.
        Supports dot notation for nested keys (e.g., 'user.settings.theme').

        :param key: The key to add.
        :type key: str
        :param value: The value associated with the key.
        :type value: any
        :raises KeyError: If the key already exists.
        :return: None
        :rtype: None
        """
        data = self._get_data(mutable=True)

        if key in self:
            raise KeyError(f"{key} already exists in {self.file_name}. Use __setitem__() instead. Implementation: JSONFile[key] = value")

        if isinstance(key, str) and '.' in key:
            keys = key.split('.')
            self._update_nested(data, keys, value)
        else:
            data[key] = value
        self._set_data(data)

    def delete_file(self) -> None:
        """
        Deletes the actual JSON file. Use with caution.

        :return: None
        :rtype: None
        """
        self._cache.pop(self.path, None)  # Remove from cache if present
        os.remove(self.path)
        logging.warning(f"Deleted {self.path}")

    def clear_cache(self) -> None:
        """
        Clears the cache for this specific JSON file.

        :return: None
        :rtype: None
        """
        self._cache.pop(self.path, None)
        logging.info(f"Cleared cache for {self.path}")

    def get(self, key: str, default=None) -> any:
        """
        Retrieves the value associated with a key from the JSON file.
        Returns a default value if the key does not exist.
        Supports dot notation for nested keys (e.g., 'user.settings.theme').

        :param key: The key to retrieve.
        :type key: str
        :param default: The default value to return if the key does not exist.
        :type default: any
        :return: The value associated with the key or the default value.
        :rtype: any
        """
        try:
            return self[key]
        except KeyError:
            return default
    
    def items(self) -> iter:
        """
        Returns an iterator over the key-value pairs in the JSON file.

        :return: An iterator over the key-value pairs in the JSON file.
        :rtype: iter
        """
        data = self._get_data(mutable=True)  # copy: callers get values they may mutate
        return data.items()