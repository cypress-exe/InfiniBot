import asyncio
import datetime
import json
import logging
import nextcord
from nextcord import Embed as NextcordEmbed
import psutil

from components.utils import format_var_to_pythonic_type, get_discord_color_from_string
from config.global_settings import get_bot_load_status, get_configs
from modules.database import Database, DatabaseContextManager
from modules.custom_types import UNSET_VALUE

# Database Paths
database_url = "sqlite:///./generated/files/prod.db"
database_build_file_path = "./resources/db_build.sql"

# Constants
MAX_SQLITE_INT = 9000000000000000000 # Technically 9223372036854775807, but brought down for margin
MAX_SQLITE_FLOAT = 1e+308 # Technically 1.7976931348623157e+308, but brought down for margin

class DatabaseForInfiniBot(Database): # Alters Database to add InfiniBot-specific functions
    """
    Retrieves all entries from the database.
    """

    def get_all_entries(self) -> list:
        """
        An alias for `get_unique_entries_for_database()`. Returns all unique entries for the database.

        :return: A list of unique entries from the database.
        :rtype: list
        """
        return self.get_unique_entries_for_database()
    
    

database = None
def init_database() -> None:
    """
    Initialize the database for InfiniBot.

    This function sets up the database by creating an instance of `DatabaseForInfiniBot`
    using the specified URL and build file path. The `database` variable is set
    to this instance, and the database context is managed using `DatabaseContextManager`.

    :return: None
    :rtype: None
    """
    global database
    with DatabaseContextManager():
        database = DatabaseForInfiniBot(database_url, database_build_file_path)

def get_database() -> DatabaseForInfiniBot:
    """
    Retrieve the current database instance.

    This function returns the current instance of `DatabaseForInfiniBot`.
    If the database has not been initialized yet, this function will
    return `None`.

    :return: The current database instance or `None` if not initialized.
    :rtype: DatabaseForInfiniBot
    """
    return database

def cleanup_database() -> None:
    """
    Clean up the database.

    This function closes the database engine and disposes of all its resources.
    It should be called when the bot is shutting down to ensure a clean exit.

    :return: None
    :rtype: None
    """
    global database
    database.cleanup()

class TableManager:
    """
    An abstract class for managing entries in a SQL table.
    """

    def serialize(self) -> dict:
        """
        Returns a dictionary representation of the object, including nested objects.
        This is useful for serialization or debugging purposes.
        """
        result = {}
        try:
            for key, value in self.to_dict().items():
                if hasattr(value, 'recursive_dict'):
                    # If the value has a recursive_dict method, call it
                    result[key] = value.recursive_dict()
                    continue
                
                if hasattr(value, 'to_dict'):
                    # If the value has a to_dict attribute, convert it to a dict
                    result[key] = value.to_dict()
                    continue
                
                # Otherwise, just store the value as is
                result[key] = value
        except (TypeError, AttributeError) as e:
            # Handle cases where to_dict() fails fall back to basic object representation
            result['error'] = f"Could not serialize object: {str(e)}"
            result['type'] = type(self).__name__
            if hasattr(self, 'table_name'):
                result['table_name'] = self.table_name
            if hasattr(self, 'primary_key_value'):
                result['primary_key_value'] = self.primary_key_value
            if hasattr(self, 'secondary_key_sql_name'):
                result['secondary_key_sql_name'] = self.secondary_key_sql_name
            
        return result

class Simple_TableManager(TableManager):
    """
    A class for managing entries in a SQL table.

    :param primary_id: The primary ID of the entry.
    :type primary_id: int
    :param table_name: The name of the SQL table.
    :type table_name: str

    :var database: The database instance.
    :type database: DatabaseForInfiniBot
    :var primary_id: The primary ID of the entry.
    :type primary_id: int
    :var table_name: The name of the SQL table.
    :type table_name: str
    :var primary_id_sql_name: The name of the primary key column in the SQL table.
    :type primary_id_sql_name: str
    :var _entry_exists_in_table: A flag indicating whether the entry exists in the table.
    :type _entry_exists_in_table: bool

    :return: The string representation of the manager with column names and their types.
    :rtype: str
    """
    def __init__(self, primary_id:int, table_name:str):
        self.database = get_database()
        self.primary_id = primary_id
        self.table_name = table_name
        self.primary_id_sql_name = self.database.all_primary_keys[table_name]

        self._entry_exists_in_table = self.database.does_entry_exist(self.table_name, self.primary_id)

    def __str__(self):
        column_names_and_types = self.get_column_names_and_types()
        properties = self.to_dict()

        return "\n".join(f"{prop} ({column_names_and_types[prop]}): {getattr(self, prop)}" for prop in properties)

    def to_dict(self) -> dict:
        column_names_and_types = self.get_column_names_and_types()
        column_names = [*column_names_and_types]
        properties = {}
        for row in column_names:
            if row in dir(self):
                properties[row] = getattr(self, row)

        return properties
    
    def __dict__(self):
        """
        Returns a dictionary representation of the object, including nested objects.
        This is useful for serialization or debugging purposes.
        """
        return self.to_dict()
       
    def get_column_names_and_types(self):
        return self.database.all_column_types[self.table_name]
    
    def get_column_names_and_defaults(self):
        return self.database.all_column_defaults[self.table_name]

    def _ensure_existence(self):
        if not self._entry_exists_in_table:
            self._init_regular_entry(self.table_name, self.primary_id)

    def _init_regular_entry(self, table: str, primary_id: int):
        '''Creates an entry with a primary_id. Warning: This will ignore if an entry with the primary_id already exists and will not warn.''' 
        column_defaults = self.database.all_column_defaults[table]

        # Create the query
        query_values = ", ".join(list(column_defaults.values()))
        query = f"INSERT OR IGNORE INTO {table} VALUES ({primary_id}, {query_values})"
        
        self.database.execute_query(query, commit = True)

    def _get_variable(self, table, column, primary_id):
        # Get the response
        response = self.database.execute_query(f"Select {column} FROM {table} WHERE {self.primary_id_sql_name} = {primary_id}")

        # Clean up the response
        cleaned_response = self.database.get_query_first_value(response)

        # Get the type of the column
        _type = self.database.get_column_type(table, column)

        # Format the response
        return format_var_to_pythonic_type(_type, cleaned_response)

    def _set_variable(self, table, column, id, value):
        self.database.execute_query(f"UPDATE {table} SET {column} = :value WHERE {self.primary_id_sql_name} = {id}", args = {"value": value}, commit = True)

    def custom_property(property_name, getter_modifier=None, setter_modifier=None, **kwargs):
        """
        Custom decorator for creating properties that are either booleans, integers, floats, or strings.
        Handles SQL retrieval, setting, cleaning, etc...

        Args:
            property_name (str): The name of the column associated with the property. Also the name of the property.
            getter_modifier (function, optional): A function that modifies the property when retrieved.
            setter_modifier (function, optional): A function that modifies the property when set.

        Uses:
            ```
            @ServerTableManager.custom_property("property_name")
            def property_name(self): pass
            ```
        """
        data_structure = kwargs["data_structure"] if "data_structure" in kwargs else None
        
        # A private variable needs to be created for every public one. This allows the value of the variable to be saved,
        # Eliminating the need to make an SQL query for every time the variable is retrieved.
        private_name = f"_{property_name}"

        def decorator(method):
            # Getter function for the property
            def getter(self):
                # Create the private attribute if it doesn't exist
                if private_name not in dir(self):
                    setattr(self, private_name, UNSET_VALUE)
                
                # If the private attribute doesn't have a value, get it from the SQL database
                if getattr(self, private_name) is UNSET_VALUE:
                    value = (
                        self._get_variable(self.table_name, property_name, self.primary_id)
                        if self._entry_exists_in_table
                        else self.database.get_column_default(self.table_name, property_name, format=True)
                    )
                    value = getter_modifier(value) if getter_modifier else value
                    value = data_structure(value) if data_structure is not None else value
                    
                    # Cache the value for future use
                    setattr(self, private_name, value)

                    # Return the value
                    return value
                
                return getattr(self, private_name)

            # Setter function for the property
            def setter(self, value):
                # If the value is of type datastruct, request the values to save
                if data_structure is not None and isinstance(value, data_structure):
                    value = value.serialize()
                
                # Modify the value to be what it should be saved as
                modified_value = setter_modifier(value) if setter_modifier else value
                
                # Save variable
                self._ensure_existence()
                self._set_variable(self.table_name, property_name, self.primary_id, modified_value)
                
                # Cache the value for future use
                value = data_structure(value) if data_structure is not None else value # Because values were serialized earlier, they need to be deserialized into the data_stucture
                setattr(self, private_name, value)
                self._entry_exists_in_table = self.database.does_entry_exist(self.table_name, self.primary_id)

            return property(getter, setter)

        return decorator
    
    def integer_property(property_name:int, accept_none_value=True, allow_negative_values=False, **kwargs):
        """
        Custom decorator for creating properties that are integers.
        Handles SQL retrieval, setting, cleaning, etc...

        Args:
            property_name (str): The name of the column associated with the property. Also the name of the property.

        Uses:
            ```
            @ServerTableManager.integer_property("property_name")
            def property_name(self): pass
            ```
        """

        data_structure = kwargs["data_structure"] if "data_structure" in kwargs else None

        def setter_modifier(value):
            if value == None: 
                if not accept_none_value:
                    raise TypeError('This property has been modified to not accept None values.')
                return None
            if isinstance(value, str):
                if value.isdigit(): value = int(value)
            if isinstance(value, float):
                if not value.is_integer(): logging.warning("Value is not an integer. It will be rounded to the nearest integer.")
                value = int(round(value))
                
            if isinstance(value, int):
                if (not allow_negative_values) and value < 0: raise ValueError('This property has been modified to only accept positive values.')
                
                # SQLite INTEGER bounds checking and clamping
                if value > MAX_SQLITE_INT:
                    logging.warning(f"Integer value {value} exceeds SQLite maximum. Clamping to {MAX_SQLITE_INT}")
                    value = MAX_SQLITE_INT
                elif value < -MAX_SQLITE_INT:
                    logging.warning(f"Integer value {value} below SQLite minimum. Clamping to {-MAX_SQLITE_INT}")
                    value = -MAX_SQLITE_INT
                
                return value
            
            if isinstance(value, UNSET_VALUE): return value
            if data_structure and isinstance(value, data_structure): return value
            raise TypeError('Must be of type Int')

        return Simple_TableManager.custom_property(property_name, setter_modifier=setter_modifier, **kwargs)

    def float_property(property_name:float, accept_none_value=True, allow_negative_values=False, **kwargs):
        """
        Custom decorator for creating properties that are floats.
        Handles SQL retrieval, setting, cleaning, etc...

        Args:
            property_name (str): The name of the column associated with the property. Also the name of the property.

        Uses:
            ```
            @ServerTableManager.float_property("property_name")
            def property_name(self): pass
            ```
        """

        def setter_modifier(value):
            if value == None: 
                if not accept_none_value:
                    raise TypeError('This property has been modified to not accept None values.')
                return None
            if isinstance(value, str):
                if value.isdigit(): value = float(value)
            if isinstance(value, int):
                value = float(value)
            if isinstance(value, float):
                if (not allow_negative_values) and value < 0: raise ValueError('This property has been modified to only accept positive values.')
                
                # SQLite FLOAT bounds checking and clamping
                if value > MAX_SQLITE_FLOAT:
                    logging.warning(f"Float value {value} exceeds SQLite maximum. Clamping to {MAX_SQLITE_FLOAT}")
                    value = MAX_SQLITE_FLOAT
                elif value < -MAX_SQLITE_FLOAT:
                    logging.warning(f"Float value {value} below SQLite minimum. Clamping to {-MAX_SQLITE_FLOAT}")
                    value = -MAX_SQLITE_FLOAT
                
                return value
            raise TypeError('Must be of type Float')

        return Simple_TableManager.custom_property(property_name, setter_modifier=setter_modifier, **kwargs)

    def boolean_property(property_name:bool, **kwargs):
        """
        Custom decorator for creating properties that are booleans.
        Handles SQL retrieval, setting, cleaning, etc...

        Args:
            property_name (str): The name of the column associated with the property. Also the name of the property.

        Uses:
            ```
            @ServerTableManager.boolean_property("property_name")
            def property_name(self): pass
            ```
        """

        def setter_modifier(value):
            if isinstance(value, int):
                if value == 0: value = False
                if value == 1: value = True
            if isinstance(value, bool):
                return value
            raise TypeError('Must be of type Boolean')

        return Simple_TableManager.custom_property(property_name, setter_modifier=setter_modifier, **kwargs)

    def string_property(property_name:str, accept_none_value=False, **kwargs):
        """
        Custom decorator for creating properties that are strings.
        Handles SQL retrieval, setting, cleaning, etc...

        Args:
            property_name (str): The name of the column associated with the property. Also the name of the property.

        Uses:
            ```
            @ServerTableManager.string_property("property_name")
            def property_name(self): pass
            ```
        """

        def setter_modifier(value):
            if value == None: 
                if not accept_none_value:
                    raise TypeError('This property has been modified to not accept None values.')
                return None
            if not isinstance(value, str):
                try:
                    value = str(value)
                except ValueError:
                    raise TypeError('Must be of type String')
            return value

        return Simple_TableManager.custom_property(property_name, setter_modifier=setter_modifier, **kwargs)

    def typed_property(property_name:(int | UNSET_VALUE | None), accept_unset_value=True, accept_none_value=True, enforce_numerical_values=False, **kwargs):
        """
        Custom decorator for creating properties that can be equal to None, UNSET_VALUE, integer, float, or string.
        Handles SQL retrieval, setting, cleaning, etc...
        Also has support for None and UNSET types.

        Args:
            property_name (str): The name of the column associated with the property. Also the name of the property.
            accept_unset_value (bool): Whether to accept UNSET_VALUE. Default: True
            accept_none_value (bool): Whether to accept None. Default: True
            enforce_numerical_values (bool): Whether to enforce numerical values. Default: False

        Uses:
            ```
            @ServerTableManager.typed_property("property_name")
            def property_name(self): pass
            ```
        """

        def getter_modifier(value):
            if value is None: # This case should never happen. In the senario that it does, this is a good fallback value.
                if accept_unset_value: return UNSET_VALUE
                elif accept_none_value: return None
                else: return 0

            # value = {"status": ('SET'|'UNSET'|'NONE'), "value": ______}
            packet = json.loads(str(value))
            if packet['status'] == 'UNSET':
                return UNSET_VALUE
            if packet['status'] == 'NONE':
                return None

            return packet['value']

        def setter_modifier(value):
            if not accept_unset_value: 
                if value is UNSET_VALUE: raise TypeError('This variable has been modified to not accept UNSET values.')
            if not accept_none_value: 
                if value is None: raise TypeError('This variable has been modified to not accept None values.')

            if value is UNSET_VALUE:
                return json.dumps({'status': 'UNSET', 'value': None})
            if value is None:
                return json.dumps({'status': 'NONE', 'value': None})
            if isinstance(value, str):
                if value.isdigit(): value = int(value)
                elif enforce_numerical_values: raise TypeError('This variable has been modified to only accept numerical values.')
                else: return json.dumps({'status': 'SET', 'value': value})
            if isinstance(value, int):
                return json.dumps({'status': 'SET', 'value': value})
            if isinstance(value, float):
                return json.dumps({'status': 'SET', 'value': value})
            raise TypeError('Must be of type None, UNSET_VALUE, integer, or float. Strings are supported if enforce_numerical_values is False.')

        return Simple_TableManager.custom_property(property_name, getter_modifier=getter_modifier, setter_modifier=setter_modifier, **kwargs)

    def list_property(property_name:(list | None), accept_duplicate_values=True, **kwargs):
        """
        Custom decorator for creating properties that are lists.
        Handles SQL retrieval, setting, cleaning, etc...

        Args:
            property_name (str): The name of the column associated with the property. Also the name of the property.
            accept_duplicate_values (bool): Whether to accept duplicate values in the list. Default: True
            getter_super_modifier (function, optional): A function that modifies the property when retrieved.
            setter_super_modifier (function, optional): A function that modifies the property when set.

        Uses:
            ```
            @ServerTableManager.list_property("property_name")
            def property_name(self): pass
            ```
        """

        # Support getter and setter super modifiers
        getter_super_modifier = kwargs.get("getter_super_modifier", None)
        setter_super_modifier = kwargs.get("setter_super_modifier", None)

        def getter_modifier(value):
            if value is None: # This case should never happen.
                return None

            value_deserialized = json.loads(str(value))
            if getter_super_modifier:
                value_deserialized = getter_super_modifier(value_deserialized)
            return value_deserialized

        def setter_modifier(value):
            if isinstance(value, list) or value is None: 
                if not accept_duplicate_values:
                    if len(set(value)) != len(value): raise ValueError('This variable has been modified to not accept duplicate values.')
                if setter_super_modifier:
                    value = setter_super_modifier(value)
                return json.dumps(value)
            raise TypeError('Must be of type List or None')

        return Simple_TableManager.custom_property(property_name, getter_modifier=getter_modifier, setter_modifier=setter_modifier, **kwargs)

    def embed_property(property_name:(int | None), **kwargs): # IRREGULAR PROPERTY
        """
        Custom decorator for creating properties that are embeds. Stores any embed properties.
        Handles SQL retrieval, setting, cleaning, etc...

        Args:
            property_name (str): The name of the column associated with the property. Also the name of the property.

        Uses:
            ```
            @ServerTableManager.embed_property("property_name")
            def property_name(self): pass
            ```
        """
        valid_arguments = ["title", "description", "url", "timestamp", "color", "footer", "image", "thumbnail", "author", "fields"]

        class EmbedProperty:
            def __init__(self, **kwargs):
                # Populate properties
                self.properties = {}
                for key, value in kwargs.items():
                    if key not in valid_arguments:
                        raise KeyError(f"Invalid embed property: {key}")
                    self.properties[key] = value
                    
            def __getitem__(self, key):
                if key in self.properties:
                    return self.properties[key]
                else:
                    if key in valid_arguments:
                        return None
                    else:
                        raise KeyError(f"Invalid embed property: {key}")
                    
            def __setitem__(self, key, value):
                if key in valid_arguments:
                    if value is None:
                        if key in self.properties: self.properties.pop(key)
                    else:
                        self.properties[key] = value

                else:
                    raise KeyError(f"Invalid embed property: {key}")
                
            def __delitem__(self, key):
                if key in self.properties:
                    self.properties.pop(key)
                else:
                    raise KeyError(f"Invalid embed property: {key}")

            def __str__(self):
                return json.dumps(self.properties)
            
            def to_dict(self):
                return self.properties
                
            def to_embed(self):
                properties = self.properties
                if "color" in properties:
                    properties["color"] = get_discord_color_from_string(properties["color"])
                
                return NextcordEmbed(**properties)
            
            def get(self, key, default=None):
                if key in self.properties:
                    return self.properties[key]
                else:
                    return default
            
        def getter_modifier(value):
            if value is None: # This case should never happen.
                return EmbedProperty()

            # value = {"title":"Embed Title", "description":"Embed Description...", "color":"Blue", ...}
            value_decoded = json.loads(str(value))
            
            # Ensure all embed properties are valid
            for key, value in value_decoded.items():
                if key not in valid_arguments:
                    raise KeyError(f"Invalid embed property: {key}")
            
            return EmbedProperty(**value_decoded)

        def setter_modifier(value):
            if not isinstance(value, EmbedProperty):
                raise TypeError('Must be of type EmbedProperty')
            
            embed_properties = value.properties
            properties_to_save = {}
            for key, value in embed_properties.items():
                if key in valid_arguments:
                    properties_to_save[key] = value
            return json.dumps(properties_to_save)

        return Simple_TableManager.custom_property(property_name, getter_modifier=getter_modifier, setter_modifier=setter_modifier, **kwargs)

class IntegratedList_TableManager(TableManager):
    """
    Manages a list that contains complex keyed data. (Limit 2 complex keys). Primarily used for lists within SQL.

    Args:
        table_name (str): The name of the SQL table.
        primary_key_sql_name (str): The name of the primary key column.
        primary_key_value (str): The value of the primary key.
        secondary_key_sql_name (str): The name of the secondary key column.
    """
    def __init__(self, table_name:str, primary_key_sql_name:str, primary_key_value:str, secondary_key_sql_name:str):
        self.database = get_database()
        self.table_name = table_name
        self.primary_key_sql_name = primary_key_sql_name
        self.primary_key_value = primary_key_value
        self.secondary_key_sql_name = secondary_key_sql_name

    class dataclass:
        """
        A simple dataclass for representing a row in the table.
        """
        def __init__(self, **kwargs):
            """
            Initialize a new dataclass instance.

            Args:
                **kwargs: Keyword arguments for the dataclass attributes.
            """
            self.variable_names = list(kwargs.keys())

            for key, value in kwargs.items():
                setattr(self, key, value)

        def get_data(self):
            """
            Return a dictionary representation of the dataclass.

            Returns:
                dict: A dictionary containing the dataclass attributes and their values.
            """
            return {key: getattr(self, key) for key in self.variable_names}
        
        def __str__(self):
            """
            Return a string representation of the dataclass.

            Returns:
                str: A string representation of the dataclass.
            """
            return str(self.get_data())


    def _get_entry(self, second_key_value):
        """
        Retrieve an entry from the SQL table based on the secondary key value.

        Args:
            second_key_value (str): The value of the secondary key.

        Returns:
            tuple: The SQL row matching the primary and secondary key values, or None if not found.
        """
        response = self.database.execute_query(f"SELECT * FROM {self.table_name} " \
                                      f"WHERE {self.primary_key_sql_name} = {self.primary_key_value} " \
                                      f"AND {self.secondary_key_sql_name} = {second_key_value}")

        return response

    def _get_all_entries(self):
        """
        Generate all entries in the list.

        Yields:
            dataclass: A dataclass representing each entry in the list.
        """
        # Get all entries in the table
        for secondary_key_value in self._get_all_secondary_values():
            data = self._get_entry(secondary_key_value)
            if data is not None:
                yield self._package_list_into_dataclass(data)

    def _get_all_secondary_values(self):
        """
        Retrieve all unique secondary key values for the primary key.

        Returns:
            list: A list of all unique secondary key values.
        """
        # Get all entries in the table
        query = f"SELECT {self.secondary_key_sql_name} FROM {self.table_name} WHERE {self.primary_key_sql_name} = :primary_key_value"
        raw_values = self.database.execute_query(query, {'primary_key_value': self.primary_key_value}, multiple_values=True)
        return [self.database.get_query_first_value(value) for value in raw_values]
    
    def _get_all_matching_indexes(self, columns:dict):
        """
        Retrieve all values in the table with the given columns.

        Args:
            columns (dict): A dictionary of column names and their corresponding values.

        Returns:
            list: A list of all secondary key values in the table with the given columns.
        """
        # Get all entries in the table
        query = f"SELECT {self.secondary_key_sql_name} FROM {self.table_name} WHERE {self.primary_key_sql_name} = :primary_key_value"
        for key, value in columns.items():
            query += f" AND {key} = :{key}"
        raw_values = self.database.execute_query(query, {'primary_key_value': self.primary_key_value, **columns}, multiple_values=True)
        return [self.database.get_query_first_value(value) for value in raw_values]
            

    def _package_list_into_dataclass(self, data:tuple):
        """
        Package a SQL row into a dataclass instance.

        Args:
            data (tuple): The SQL row data.

        Returns:
            dataclass: A dataclass instance representing the SQL row.
        """
        # Package data into dictionary
        data_dict = {}
        types = self.database.all_column_names[self.table_name]
        for index, column_value in enumerate(data):
            name = types[index]
            data_dict[name] = column_value

        return self.dataclass(**data_dict)
    
    def _check_entry_existence(self, secondary_key_value):
        """
        Check if an entry exists for the given secondary key.

        Args:
            secondary_key_value (str): The value of the secondary key.

        Returns:
            bool: True if the entry exists, False otherwise.
        """
        return (self._get_entry(secondary_key_value) != None)
    
    def _sync_dictionary_with_table(self, data_dict) -> dict:
        """
        Sync the dictionary to the table to ensure it is valid. Used for adding a new entry to the table.

        Args:
            data_dict (dict): The dictionary representing the new entry.

        Returns:
            dict: The validated dictionary.

        Raises:
            ValueError: If the primary key does not match or a duplicate entry exists.
            KeyError: If any required keys are missing.
        """
        # Check all sql keys exist in data_dict
        if self.primary_key_sql_name not in data_dict.keys():
            data_dict[self.primary_key_sql_name] = self.primary_key_value
        elif data_dict[self.primary_key_sql_name] != self.primary_key_value:
            raise ValueError(f"Primary key \"{self.primary_key_sql_name}\" ({data_dict[self.primary_key_sql_name]}) does not match \"{self.primary_key_value}\".")

        if self.secondary_key_sql_name not in data_dict.keys():
            raise KeyError(f"Secondary key \"{self.secondary_key_sql_name}\" not found.")
        
        # Check all keys in data_dict exist in table
        for column_name in data_dict.keys():
            if column_name not in self.database.all_column_names[self.table_name]:
                raise KeyError(f"Column \"{column_name}\" not found in table.")
        
        # Check that there are no duplicates
        secondary_key_value = data_dict[self.secondary_key_sql_name]
        if self._check_entry_existence(secondary_key_value):
            raise ValueError(f"{self.primary_key_value}, {secondary_key_value} already exists in database.")
        
        # Check no missing values
        column_names = self.database.all_column_names[self.table_name][2:] # Ignore primary key and secondary key
        for column_name in column_names:
            if column_name not in data_dict.keys():
                if column_name in self.database.all_column_defaults[self.table_name]:
                    continue
                else:
                    raise KeyError(f"Column \"{column_name}\" not found in data. Did you forget to add it?")

        return data_dict
    
    def _validate_dict_values_for_sqlite(self, data_dict:dict) -> dict:
        """
        Validates dictionary values to ensure they are compatible with SQLite data type limits.
        This method checks integer and float values in the provided dictionary to ensure they
        fall within SQLite's supported ranges. Values that exceed the bounds are
        clamped to the maximum/minimum allowed values with a warning logged. 
        Args:
            data_dict (dict): Dictionary containing column names as keys and their corresponding
                                values to be validated for SQLite compatibility.
        Returns:
            dict: The validated dictionary with potentially modified values.
        Note:
            - Values exceeding bounds are automatically clamped to valid ranges
            - A warning is logged when values are clamped
        """
        
        # Check no overflowing int/float values
        for column_name, value in data_dict.items():
            if isinstance(value, int):
                if value > MAX_SQLITE_INT or value < -MAX_SQLITE_INT:
                    clamp_value = MAX_SQLITE_INT if value > 0 else -MAX_SQLITE_INT
                    logging.warning(f"Value for column \"{column_name}\" exceeds SQLite INTEGER bounds. Clamping to {clamp_value}.")
                    data_dict[column_name] = clamp_value
                    
            elif isinstance(value, float):
                if value > MAX_SQLITE_FLOAT or value < -MAX_SQLITE_FLOAT:
                    clamp_value = MAX_SQLITE_FLOAT if value > 0 else -MAX_SQLITE_FLOAT
                    logging.warning(f"Value for column \"{column_name}\" exceeds SQLite FLOAT bounds. Clamping to {clamp_value}.")
                    data_dict[column_name] = clamp_value

        return data_dict

    def _update_entry_using_dict(self, secondary_key_value, data_dict):
        """
        Update an entry in the list using a dictionary of data.

        Args:
            secondary_key_value (str): The value of the secondary key.
            data_dict (dict): The dictionary containing the data to update.

        Raises:
            ValueError: If the primary key does not match.
            KeyError: If any provided keys are not found in the table.
        """
        # Update the database
        params = ', '.join([f"{key}=:{key}" for key in data_dict.keys()])
        values = {key: data_dict[key] for key in data_dict.keys()}
        query = f"UPDATE {self.table_name} SET {params} WHERE {self.primary_key_sql_name} = :primary_key_value AND {self.secondary_key_sql_name} = :secondary_key_value"
        
        # Add the primary key and secondary key to the values dictionary
        values['primary_key_value'] = self.primary_key_value
        values['secondary_key_value'] = secondary_key_value
        
        self.database.execute_query(query, values, commit=True)


    def __getitem__(self, second_key_value): # Called when you use the [] operator
        """
        Retrieve an entry from the list based on the secondary key value.

        Args:
            item (str): The value of the secondary key.
            item (list): The values of keys to match.

        Returns:
            dataclass: The dataclass representing the entry.

        Raises:
            KeyError: If the secondary key is not found.
        """
        data = self._get_entry(second_key_value)
        if data is None: raise KeyError(f"Secondary key \"{second_key_value}\" not found in table.")
        return self._package_list_into_dataclass(data)

    def get(self, secondary_key_value, default=None):
        """
        Get an entry from the list based on the secondary key value.

        Args:
            secondary_key_value (str): The value of the secondary key.
            default: The default value to return if the entry is not found.

        Returns:
            dataclass: The dataclass representing the entry, or the default value if not found.
        """
        try:
            return self[secondary_key_value]
        except KeyError:
            return default

    def get_matching(self, **kwargs):
        """
        Get all entries that match the given criteria.

        Args:
            **kwargs: Keyword arguments representing the criteria to match.

        Returns:
            list: A list of dataclasses representing the matching entries.
        """
        secondary_key_values = self._get_all_matching_indexes(kwargs)
        result = []
        for secondary_key_value in secondary_key_values:
            data = self._get_entry(secondary_key_value)
            if data is not None:
                result.append(self._package_list_into_dataclass(data))
        return result

    def add(self, **kwargs):
        """
        Add a new entry to the list.

        Args:
            **kwargs: Keyword arguments representing the new entry's data.

        Raises:
            ValueError: If the primary key does not match or a duplicate entry exists.
            KeyError: If any required keys are missing.
        """
        data_dict:dict = self._validate_dict_values_for_sqlite(self._sync_dictionary_with_table(kwargs))
        
        # Update the database
        values = {key: data_dict[key] for key in data_dict.keys()}
        placeholders = ', '.join([f":{key}" for key in data_dict.keys()])
        query = f"INSERT INTO {self.table_name} ({', '.join(data_dict.keys())}) VALUES ({placeholders})"
        self.database.execute_query(query, values, commit=True)

    def edit(self, *args, **kwargs):
        """
        Edit an existing entry in the list.

        Args:
            secondary_key_value (str): The value of the secondary key.
            **kwargs: Keyword arguments representing the data to update.

        Raises:
            ValueError: If the entry does not exist or no arguments are given.
            KeyError: If the primary key is being updated incorrectly or any provided keys are not found in the table.
        """
        if len(args) >= 1:
            secondary_key_value = args[0]
        else:
            # Check kwargs
            if self.secondary_key_sql_name not in kwargs.keys():
                raise KeyError(f"Secondary key \"{self.secondary_key_sql_name}\" not found in arguments.")
            secondary_key_value = kwargs[self.secondary_key_sql_name]
            
        if not self._check_entry_existence(secondary_key_value):
            raise ValueError(f"{self.primary_key_value}, {secondary_key_value} does not exist in database.")
        
        # Ensure kwargs are given
        if len(kwargs) == 0:
            raise ValueError("No arguments given to edit.")
        
        # Ensure kwargs's keys all exist in the database
        all_column_names = self.database.all_column_names[self.table_name]
        for key in kwargs.keys():
            if key not in all_column_names:
                raise KeyError(f"Kwarg \"{key}\" not found in database.")
            
        # Ensure primary key is not being updated
        if self.primary_key_sql_name in kwargs.keys():
            if kwargs[self.primary_key_sql_name] != self.primary_key_value:
                raise KeyError(f"Primary key \"{self.primary_key_sql_name}\" cannot be updated.")
            
        # Ensure values are valid for SQLite
        kwargs = self._validate_dict_values_for_sqlite(kwargs)

        self._update_entry_using_dict(secondary_key_value, kwargs)

    def delete(self, secondary_key_value, fail_silently=False):
        """
        Delete an entry from the list.

        Args:
            secondary_key_value (str): The value of the secondary key.

        Raises:
            ValueError: If the entry does not exist.
        """
        if not self._check_entry_existence(secondary_key_value):
            if fail_silently: return
            raise ValueError(f"{self.primary_key_value}, {secondary_key_value} does not exist in database.")

        query = f"DELETE FROM {self.table_name} WHERE {self.primary_key_sql_name} = :primary_key_value AND {self.secondary_key_sql_name} = :secondary_key_value"
        self.database.execute_query(query, {'primary_key_value': self.primary_key_value, 'secondary_key_value': secondary_key_value}, commit=True)

    def delete_all_matching(self, **kwargs):
        """
        Delete all entries from the list that match the given criteria.

        Args:
            **kwargs: Keyword arguments representing the criteria to match. Matches to columns in the db.

        Returns:
            list: A list of dataclasses representing the deleted entries.
        """
        # Validate kwargs
        all_column_names = self.database.all_column_names[self.table_name]
        for key in kwargs.keys():
            if key not in all_column_names:
                raise KeyError(f"Kwarg \"{key}\" not found in database.")

        # Get all entries in the table
        query = f"DELETE FROM {self.table_name} WHERE {self.primary_key_sql_name} = :primary_key_value"
        for key, value in kwargs.items():
            query += f" AND {key} = :{key}"
        self.database.execute_query(query, {'primary_key_value': self.primary_key_value, **kwargs}, commit=True)
        

    def delete_all(self):
        """
        Delete all entries from the list for the primary key.
        """
        query = f"DELETE FROM {self.table_name} WHERE {self.primary_key_sql_name} = :primary_key_value"
        self.database.execute_query(query, {'primary_key_value': self.primary_key_value}, commit=True)


    def __len__(self):
        """
        Return the length of the list.

        Returns:
            int: The length of the list.
        """
        return len(list(self._get_all_entries()))
    
    def __contains__(self, secondary_key_value):
        """
        Check if an entry exists in the list.

        Args:
            secondary_key_value (str): The value of the secondary key.

        Returns:
            bool: True if the entry exists, False otherwise.
        """
        return self._check_entry_existence(secondary_key_value)

    def __iter__(self):
        """
        Return an iterator over the entries in the list.

        Returns:
            Generator: A generator yielding dataclass instances for each entry.
        """
        return self._get_all_entries()
    
    def __next__(self):
        """
        Return the next entry in the list.

        Returns:
            dataclass: A dataclass representing the next entry.
        """
        return next(self._get_all_entries())
    
    def __str__(self) -> str:
        """
        Return a string representation of the list.

        Returns:
            str: A string representation of the list.
        """
        entries = list(self._get_all_entries())
        entries_str = ", ".join(str(entry) for entry in entries)
        return f"[{entries_str}]"
    
    def to_dict(self):
        """
        Return a dictionary representation of the list.

        Returns:
            dict: A dictionary containing the entries in the list.
        """
        result = {}
        for secondary_key_value in self._get_all_secondary_values():
            data = self._get_entry(secondary_key_value)
            if data is not None:
                dataclass_entry = self._package_list_into_dataclass(data)
                result[secondary_key_value] = dataclass_entry.get_data()
        return result

async def daily_database_maintenance(bot: nextcord.Client):
    """
    Perform comprehensive daily database maintenance operations with performance monitoring.
    This function executes a series of database maintenance tasks including WAL checkpointing,
    database optimization, message log cleanup, and removal of orphaned guild entries.
    The operation includes performance tracking and throttling to prevent system overload.
    Args:
        bot (nextcord.Client): The Discord bot client instance used to access guild information
                              for orphaned entry cleanup operations.
    Returns:
        None
    Raises:
        Exception: Any fatal errors during maintenance operations are logged and handled gracefully.
    Performance Features:
        - CPU usage monitoring with throttling at 75% threshold
        - Execution time tracking for each maintenance phase
        - Memory usage reporting
        - Batch processing for large datasets
        - Temporary table optimization for orphaned entry cleanup
    Maintenance Phases:
        1. WAL Checkpoint: Flushes write-ahead log to main database
        2. Database Optimization: Performs VACUUM and other optimization operations
        3. Message Log Cleanup: Removes old message entries based on retention policy
        4. Orphaned Guild Entries: Removes database entries for guilds the bot is no longer in
    Notes:
        - Waits for bot to be ready before starting maintenance
        - Skips execution if bot load status prevents maintenance
        - Logs detailed performance metrics and progress information
        - Includes safety mechanisms to prevent maintenance from exceeding 5 minutes
        - Uses temporary tables for efficient bulk operations
        - Automatically cleans up resources even if errors occur
    """
    await bot.wait_until_ready()
    
    # Initialize performance tracking
    start_time = datetime.datetime.now(datetime.timezone.utc)
    total_deleted = 0
    
    logging.info(f"================================ GLOBAL DATABASE MAINTENANCE ================================")
    
    try:
        if not get_bot_load_status():
            logging.warning("SKIPPING: Bot load status prevents maintenance")
            return
        
        # WAL checkpoint phase -----------------------------------------------------------------------------------
        logging.info("Starting WAL checkpoint...")
        checkpoint_start = datetime.datetime.now(datetime.timezone.utc)
        
        get_database().checkpoint()
        
        checkpoint_duration = datetime.datetime.now(datetime.timezone.utc) - checkpoint_start
        logging.info(f"WAL checkpoint completed in {checkpoint_duration.total_seconds():.2f}s")

        # Database optimization phase -----------------------------------------------------------------------------------
        logging.info("Starting database optimization...")
        optimize_start = datetime.datetime.now(datetime.timezone.utc)
        
        total_deleted += get_database().optimize_database(throttle=True)

        optimize_duration = datetime.datetime.now(datetime.timezone.utc) - optimize_start
        logging.info(f"Optimization completed in {optimize_duration.total_seconds():.2f}s")


        # Message log cleanup phase -----------------------------------------------------------------------------------
        logging.info("Starting message log cleanup...")
        message_log_cleanup_start = datetime.datetime.now(datetime.timezone.utc)

        from config.messages import stored_messages
        total_deleted += stored_messages.cleanup_db()

        message_log_cleanup_duration = datetime.datetime.now(datetime.timezone.utc) - message_log_cleanup_start
        logging.info(f"Message log cleanup completed in {message_log_cleanup_duration.total_seconds():.2f}s")


        # Orphaned Guild Entries cleanup phase -----------------------------------------------------------------------------------
        logging.info(f"Scanning tables for orphaned guild entries...")
        orphaned_guild_entries_cleanup_start = datetime.datetime.now(datetime.timezone.utc)

        total_deleted += cleanup_orphaned_guild_entries(set([int(guild.id) for guild in bot.guilds]), get_database())

        orphaned_guild_entries_cleanup_duration = datetime.datetime.now(datetime.timezone.utc) - orphaned_guild_entries_cleanup_start
        logging.info(f"Orphaned guild entries cleanup completed in {orphaned_guild_entries_cleanup_duration.total_seconds():.2f}s")

        # Final report
        total_duration = datetime.datetime.now(datetime.timezone.utc) - start_time
        logging.info(
            f"MAINTENANCE COMPLETE\n"
            f"Duration: {total_duration}\n"
            f"Deleted: {total_deleted} entries\n"
            f"Current CPU: {psutil.cpu_percent()}%\n"
            f"Memory usage: {psutil.virtual_memory().percent}%"
        )

    except Exception as err:
        logging.error(f"Fatal maintenance error: {err}", exc_info=True)
    finally:
        if (datetime.datetime.now(datetime.timezone.utc) - start_time) > datetime.timedelta(minutes=5):
            logging.warning("Database maintenance exceeded 5 minute threshold!")

def cleanup_orphaned_guild_entries(all_guild_ids:set, database:Database=None):
    """
    Remove database entries that reference guilds the bot is not currently in.

    Args:
        all_guild_ids (set): A set of all guild IDs to keep.
        database (Database, optional): The database manager instance. If None, uses the default database.

    Returns:
        int: Total number of orphaned entries that were deleted.
    """
    total_deleted = 0
    if database is None:
        database = get_database()

    try:
        # Create temporary table for valid guild IDs - much more efficient than large IN clauses
        database.execute_query("DROP TABLE IF EXISTS temp_valid_guilds")
        database.execute_query("CREATE TEMPORARY TABLE temp_valid_guilds (guild_id INTEGER PRIMARY KEY)")

        # Insert all valid guild IDs in batches to avoid parameter limits
        batch_size = 500  # SQLite parameter limit is typically 999
        guild_ids_list = list(all_guild_ids)
        
        for i in range(0, len(guild_ids_list), batch_size):
            batch = guild_ids_list[i:i + batch_size]
            query_values = ",".join(f"({int(gid)})" for gid in batch)
            database.execute_query(
            f"INSERT INTO temp_valid_guilds (guild_id) VALUES {query_values}",
            commit=True
            )

        for table in database.tables:
            try:
                table_start = datetime.datetime.now(datetime.timezone.utc)

                # Get the guild row
                if table not in database.tags: continue
                if "remove-if-guild-invalid" not in database.tags[table]: continue
                guild_row = database.tags[table]["remove-if-guild-invalid"]

                if guild_row not in database.all_column_names[table]:
                    logging.warning(f"Table {table} does not have the reported guild column '{guild_row}'. Skipping.")
                    continue

                table_primary_key = database.all_primary_keys[table]
                if table_primary_key is None:
                    logging.warning(f"Table {table} does not have a primary key. Skipping.")
                    continue
                
                logging.info(f"Processing table {table} with guild column '{guild_row}'")
                
                # Delete orphaned entries using LEFT JOIN - much more efficient than large IN clause
                # SQLite will tell us how many rows were affected, so no need to count first
                deleted_count = database.execute_query(
                    f"""DELETE FROM {table} 
                        WHERE {table}.{table_primary_key} IN (
                            SELECT {table}.{table_primary_key} FROM {table} 
                            LEFT JOIN temp_valid_guilds ON {table}.{guild_row} = temp_valid_guilds.guild_id 
                            WHERE temp_valid_guilds.guild_id IS NULL
                        )""",
                    commit=True,
                    return_affected_rows=True
                )
                
                if deleted_count > 0:
                    total_deleted += deleted_count
                    logging.info(f"Deleted {deleted_count} orphaned entries from {table}")
                else:
                    logging.info(f"No orphaned entries found in {table}")
                
                logging.info(f"Completed {table} in {datetime.datetime.now(datetime.timezone.utc) - table_start}")

            except Exception as table_err:
                logging.error(f"Table {table} processing failed: {table_err}", exc_info=True)

    finally:
        # Cleanup temporary table
        database.execute_query("DROP TABLE IF EXISTS temp_valid_guilds")

    return total_deleted