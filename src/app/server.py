import json

from nextcord import Embed as NextcordEmbed

from components.utils import format_var_to_pythonic_type
from core.custom_types import UNSET_VALUE
from core.database import Database

# Database Paths
database_url = "sqlite:///./generated/files/database.db"
database_build_file_path = "./resources/db_build.sql"

class DatabaseForInfiniBot(Database): # Alters Database to add InfiniBot-specific functions
    def get_all_entries(self):
        return self.get_unique_entries_for_database()

database = None
def init_database():
    global database
    database = DatabaseForInfiniBot(database_url, database_build_file_path)

init_database()

class Server_TableManager:
    def __init__(self, server_id:int, table_name:str):
        self.server_id = server_id
        self.table_name = table_name
        self.id_sql_name = database.all_primary_keys[table_name]

        self._entry_exists_in_table = database.does_entry_exist(self.table_name, self.server_id)

    def __str__(self):
        column_names_and_types = self.get_column_names_and_types()
        properties = self.__dict__()

        return "\n".join(f"{prop} ({column_names_and_types[prop]}): {getattr(self, prop)}" for prop in properties)
    
    def __dict__(self):
        column_names_and_types = self.get_column_names_and_types()
        column_names = [*column_names_and_types]
        properties = {}
        for row in column_names:
            if row in dir(self):
                properties[row] = getattr(self, row)

        return properties
    
    def get_column_names_and_types(self):
        return database.all_column_types[self.table_name]
    
    def get_column_names_and_defaults(self):
        return database.all_column_defaults[self.table_name]

    def _ensure_existence(self):
        if not self._entry_exists_in_table:
            self._init_regular_entry(self.table_name, self.server_id)

    def _init_regular_entry(self, table: str, server_id: int):
        '''Creates an entry for a server. Warning: This will ignore if the server already exists and will not warn.''' 
        column_defaults = database.all_column_defaults[table]

        # Create the query
        query_values = ", ".join(list(column_defaults.values()))
        query = f"INSERT OR IGNORE INTO {table} VALUES ({server_id}, {query_values})"
        
        database.execute_query(query, commit = True)

    def _get_variable(self, table, column, server_id):
        # Get the response
        response = database.execute_query(f"Select {column} FROM {table} WHERE {self.id_sql_name} = {server_id}")

        # Clean up the response
        cleaned_response = database.get_query_first_value(response)

        # Get the type of the column
        _type = database.get_column_type(table, column)

        # Format the response
        return format_var_to_pythonic_type(_type, cleaned_response)

    def _set_variable(self, table, column, id, value):
        database.execute_query(f"UPDATE {table} SET {column} = :value WHERE {self.id_sql_name} = {id}", args = {"value": value}, commit = True)

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
                        self._get_variable(self.table_name, property_name, self.server_id)
                        if self._entry_exists_in_table
                        else database.get_column_default(self.table_name, property_name, format=True)
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
                self._set_variable(self.table_name, property_name, self.server_id, modified_value)
                
                # Cache the value for future use
                value = data_structure(value) if data_structure is not None else value # Because values were serialized earlier, they need to be deserialized into the data_stucture
                setattr(self, private_name, value)
                self._entry_exists_in_table = database.does_entry_exist(self.table_name, self.server_id)

            return property(getter, setter)

        return decorator
    
    def integer_property(property_name:int, **kwargs):
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
            if value == None: return None
            if isinstance(value, str):
                if value.isdigit(): value = int(value)
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, UNSET_VALUE): return value
            if isinstance(value, data_structure): return value
            raise TypeError('Must be of type Int')

        return Server_TableManager.custom_property(property_name, setter_modifier=setter_modifier, **kwargs)

    def float_property(property_name:float, **kwargs):
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
            if isinstance(value, str):
                if value.isdigit(): value = float(value)
            if isinstance(value, int):
                value = float(value)
            if isinstance(value, float):
                return value
            raise TypeError('Must be of type Float')

        return Server_TableManager.custom_property(property_name, setter_modifier=setter_modifier, **kwargs)

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

        return Server_TableManager.custom_property(property_name, setter_modifier=setter_modifier, **kwargs)

    def string_property(property_name:str, **kwargs):
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
            if not isinstance(value, str):
                try:
                    value = str(value)
                except ValueError:
                    raise TypeError('Must be of type String')
            return value

        return Server_TableManager.custom_property(property_name, setter_modifier=setter_modifier, **kwargs)

    def typed_property(property_name:(int | UNSET_VALUE | None), accept_unset_value = True, accept_none_value = True, enforce_numerical_values = False, **kwargs):
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

        return Server_TableManager.custom_property(property_name, getter_modifier=getter_modifier, setter_modifier=setter_modifier, **kwargs)

    def list_property(property_name:(list | None), accept_duplicate_values = True, **kwargs):
        """
        Custom decorator for creating properties that are lists.
        Handles SQL retrieval, setting, cleaning, etc...

        Args:
            property_name (str): The name of the column associated with the property. Also the name of the property.

        Uses:
            ```
            @ServerTableManager.list_property("property_name")
            def property_name(self): pass
            ```
        """

        def getter_modifier(value):
            if value is None: # This case should never happen.
                return None

            value_deserialized = json.loads(str(value))
            return value_deserialized

        def setter_modifier(value):
            if isinstance(value, list) or value is None: 
                if not accept_duplicate_values:
                    if len(set(value)) != len(value): raise ValueError('This variable has been modified to not accept duplicate values.')
                return json.dumps(value)
            raise TypeError('Must be of type List or None')

        return Server_TableManager.custom_property(property_name, getter_modifier=getter_modifier, setter_modifier=setter_modifier, **kwargs)

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
                
            def __str__(self):
                return json.dumps(self.properties)
                
            def to_embed(self):
                return NextcordEmbed(**self.properties)
            
            def subsitute_placeholders(self, **kwargs):
                for property_key, property_value in self.properties.items():
                    if isinstance(property_value, str):
                        for kwarg_key, kwarg_value in kwargs.items():
                            self.properties[property_key] = property_value.replace(f"@{kwarg_key}", kwarg_value)
                            
                    if property_key == "fields": # fields is a list
                        for field in property_value:
                            for kwarg_key, kwarg_value in kwargs.items():
                                field["value"].replace(f"@{kwarg_key}", kwarg_value)

        def getter_modifier(value):
            if value is None: # This case should never happen.
                return EmbedProperty()

            # value = {"title":"Embed Title", "description":"Embed Description...", "color": 0x00FFFF, ...}
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

        return Server_TableManager.custom_property(property_name, getter_modifier=getter_modifier, setter_modifier=setter_modifier, **kwargs)

class IntegratedList_TableManager:
    """
    Manages a list that contains complex keyed data. (Limit 2 complex keys). Primarily used for lists within SQL.

    Args:
        table_name (str): The name of the SQL table.
        primary_key_sql_name (str): The name of the primary key column.
        primary_key_value (str): The value of the primary key.
        secondary_key_sql_name (str): The name of the secondary key column.
    """
    def __init__(self, table_name:str, primary_key_sql_name:str, primary_key_value:str, secondary_key_sql_name:str):
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
        response = database.execute_query(f"SELECT * FROM {self.table_name} " \
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
            yield self._get_entry(secondary_key_value)

    def _get_all_secondary_values(self):
        """
        Retrieve all unique secondary key values for the primary key.

        Returns:
            list: A list of all unique secondary key values.
        """
        # Get all entries in the table
        query = f"SELECT {self.secondary_key_sql_name} FROM {self.table_name} WHERE {self.primary_key_sql_name} = :primary_key_value"
        raw_values = database.execute_query(query, {'primary_key_value': self.primary_key_value}, multiple_values=True)
        return [database.get_query_first_value(value) for value in raw_values]
    
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
        raw_values = database.execute_query(query, {'primary_key_value': self.primary_key_value, **columns}, multiple_values=True)
        return [database.get_query_first_value(value) for value in raw_values]
            

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
        types = database.all_column_names[self.table_name]
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
            if column_name not in database.all_column_names[self.table_name]:
                raise KeyError(f"Column \"{column_name}\" not found in table.")
        
        # Check that there are no duplicates
        secondary_key_value = data_dict[self.secondary_key_sql_name]
        if self._check_entry_existence(secondary_key_value):
            raise ValueError(f"{self.primary_key_value}, {secondary_key_value} already exists in database.")
        
        # Check no missing values
        column_names = database.all_column_names[self.table_name][2:] # Ignore primary key and secondary key
        for column_name in column_names:
            if column_name not in data_dict.keys():
                raise KeyError(f"Column \"{column_name}\" not found.")

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
        
        database.execute_query(query, values, commit=True)


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

    def get_matching(self, **kwargs):
        """
        Get all entries that match the given criteria.

        Args:
            **kwargs: Keyword arguments representing the criteria to match.

        Returns:
            list: A list of dataclasses representing the matching entries.
        """
        data = self._get_all_matching_indexes(kwargs)
        return [self._get_entry(row) for row in data]

    def add(self, **kwargs):
        """
        Add a new entry to the list.

        Args:
            **kwargs: Keyword arguments representing the new entry's data.

        Raises:
            ValueError: If the primary key does not match or a duplicate entry exists.
            KeyError: If any required keys are missing.
        """
        data_dict:dict = self._sync_dictionary_with_table(kwargs)
        
        # Update the database
        values = {key: data_dict[key] for key in data_dict.keys()}
        placeholders = ', '.join([f":{key}" for key in data_dict.keys()])
        query = f"INSERT INTO {self.table_name} ({', '.join(data_dict.keys())}) VALUES ({placeholders})"
        database.execute_query(query, values, commit=True)

    def edit(self, secondary_key_value, **kwargs):
        """
        Edit an existing entry in the list.

        Args:
            secondary_key_value (str): The value of the secondary key.
            **kwargs: Keyword arguments representing the data to update.

        Raises:
            ValueError: If the entry does not exist or no arguments are given.
            KeyError: If the primary key is being updated incorrectly or any provided keys are not found in the table.
        """
        if not self._check_entry_existence(secondary_key_value):
            raise ValueError(f"{self.primary_key_value}, {secondary_key_value} does not exist in database.")
        
        # Ensure kwargs are given
        if len(kwargs) == 0:
            raise ValueError("No arguments given to edit.")
        
        # Ensure kwargs's keys all exist in the database
        all_column_names = database.all_column_names[self.table_name]
        for key in kwargs.keys():
            if key not in all_column_names:
                raise KeyError(f"Kwarg \"{key}\" not found in database.")
            
        # Ensure primary key is not being updated
        if self.primary_key_sql_name in kwargs.keys():
            if kwargs[self.primary_key_sql_name] != self.primary_key_value:
                raise KeyError(f"Primary key \"{self.primary_key_sql_name}\" cannot be updated.")

        self._update_entry_using_dict(secondary_key_value, kwargs)

    def delete(self, secondary_key_value):
        """
        Delete an entry from the list.

        Args:
            secondary_key_value (str): The value of the secondary key.

        Raises:
            ValueError: If the entry does not exist.
        """
        if not self._check_entry_existence(secondary_key_value):
            raise ValueError(f"{self.primary_key_value}, {secondary_key_value} does not exist in database.")

        query = f"DELETE FROM {self.table_name} WHERE {self.primary_key_sql_name} = :primary_key_value AND {self.secondary_key_sql_name} = :secondary_key_value"
        database.execute_query(query, {'primary_key_value': self.primary_key_value, 'secondary_key_value': secondary_key_value}, commit=True)

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


class Server:
    def __init__(self, server_id:int):
        self.server_id = server_id

        self._profanity_moderation_profile = None
        self._spam_moderation_profile = None
        self._logging_profile = None
        self._leveling_profile = None
        self._join_message_profile = None
        self._leave_message_profile = None
        self._birthdays_profile = None
        self._infinibot_settings_profile = None
        
        self._join_to_create_vcs = None
        self._default_roles = None
        
        self._moderation_strikes = None
        self._member_levels = None
        self._level_rewards = None
        self._birthdays = None
        self._autobans = None
        
        self._embeds = None
        self._reaction_roles = None
        self._role_messages = None

    def __str__(self):
        return str(self.server_id)

    def remove_all_data(self):
        '''Removes all data relating to this server from the database.'''
        for table in database.tables:
            database.force_remove_entry(table, self.server_id) # This isn't working for some reason.

    # PROFILES
    @property
    def profanity_moderation_profile(self):
        if self._profanity_moderation_profile is None: self._profanity_moderation_profile = self.Profanity_Moderation_Profile(self.server_id)
        return self._profanity_moderation_profile
    class Profanity_Moderation_Profile(Server_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "profanity_moderation_profile")

        @Server_TableManager.boolean_property("active")
        def active(self): pass

        @Server_TableManager.typed_property("channel", enforce_numerical_values = True)
        def channel(self): pass

        @Server_TableManager.boolean_property("strike_system_active")
        def strike_system_active(self): pass

        @Server_TableManager.integer_property("max_strikes")
        def max_strikes(self): pass

        @Server_TableManager.boolean_property("strike_expiring_active")
        def strike_expiring_active(self): pass

        @Server_TableManager.integer_property("strike_expire_days")
        def strike_expire_days(self): pass

        @Server_TableManager.integer_property("timeout_seconds")
        def timeout_seconds(self): pass

        @Server_TableManager.list_property("filtered_words", accept_duplicate_values = False)
        def filtered_words(self): pass

    @property
    def spam_moderation_profile(self):
        if self._spam_moderation_profile is None: self._spam_moderation_profile = self.Spam_Moderation_Profile(self.server_id)
        return self._spam_moderation_profile
    class Spam_Moderation_Profile(Server_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "spam_moderation_profile")

        @Server_TableManager.boolean_property("active")
        def active(self): pass

        @Server_TableManager.integer_property("messages_threshold")
        def messages_threshold(self): pass

        @Server_TableManager.integer_property("timeout_seconds")
        def timeout_seconds(self): pass

        @Server_TableManager.boolean_property("delete_invites")
        def delete_invites(self): pass

    @property
    def logging_profile(self):
        if self._logging_profile is None: self._logging_profile = self.Logging_Profile(self.server_id)
        return self._logging_profile
    class Logging_Profile(Server_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "logging_profile")

        @Server_TableManager.boolean_property("active")
        def active(self): pass

        @Server_TableManager.typed_property("channel", accept_none_value=False, enforce_numerical_values = True)
        def channel(self): pass

    @property
    def leveling_profile(self):
        if self._leveling_profile is None: self._leveling_profile = self.Leveling_Profile(self.server_id)
        return self._leveling_profile
    class Leveling_Profile(Server_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "leveling_profile")

        @Server_TableManager.boolean_property("active")
        def active(self): pass

        @Server_TableManager.typed_property("channel", enforce_numerical_values = True)
        def channel(self): pass

        @Server_TableManager.embed_property("level_up_embed")
        def level_up_embed(self): pass

        @Server_TableManager.integer_property("points_lost_per_day")
        def points_lost_per_day(self): pass

        @Server_TableManager.list_property("exempt_channels")
        def exempt_channels(self): pass

        @Server_TableManager.boolean_property("allow_leveling_cards")
        def allow_leveling_cards(self): pass

    @property
    def join_message_profile(self):
        if self._join_message_profile is None: self._join_message_profile = self.JoinMessageProfile(self.server_id)
        return self._join_message_profile
    class JoinMessageProfile(Server_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "join_message_profile")

        @Server_TableManager.boolean_property("active")
        def active(self): pass

        @Server_TableManager.typed_property("channel", accept_none_value=False, enforce_numerical_values = True)
        def channel(self): pass

        @Server_TableManager.embed_property("embed")
        def embed(self): pass

        @Server_TableManager.boolean_property("allow_join_cards")
        def allow_join_cards(self): pass

    @property
    def leave_message_profile(self):
        if self._leave_message_profile is None: self._leave_message_profile = self.LeaveMessageProfile(self.server_id)
        return self._leave_message_profile
    class LeaveMessageProfile(Server_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "leave_message_profile")

        @Server_TableManager.boolean_property("active")
        def active(self): pass

        @Server_TableManager.typed_property("channel", accept_none_value=False, enforce_numerical_values = True)
        def channel(self): pass

        @Server_TableManager.embed_property("embed")
        def embed(self): pass
        
    @property
    def birthdays_profile(self):
        if self._birthdays_profile is None: self._birthdays_profile = self.BirthdaysProfile(self.server_id)
        return self._birthdays_profile
    class BirthdaysProfile(Server_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "birthdays_profile")

        @Server_TableManager.typed_property("channel", enforce_numerical_values = True)
        def channel(self): pass

        @Server_TableManager.embed_property("embed")
        def embed(self): pass
                
        @Server_TableManager.typed_property("runtime")
        def runtime(self): pass

    @property
    def infinibot_settings_profile(self):
        if self._infinibot_settings_profile is None: self._infinibot_settings_profile = self.InfinibotSettingsProfile(self.server_id)
        return self._infinibot_settings_profile
    class InfinibotSettingsProfile(Server_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "infinibot_settings_profile")

        @Server_TableManager.boolean_property("delete_invites")
        def delete_invites(self): pass

        @Server_TableManager.boolean_property("get_updates")
        def get_updates(self): pass


    # SIMPLE LISTS
    @property
    def join_to_create_vcs(self):
        if self._join_to_create_vcs is None: self._join_to_create_vcs = self.JoinToCreateVCs(self.server_id)
        return self._join_to_create_vcs
    class JoinToCreateVCs(Server_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "join_to_create_vcs")
        
        @Server_TableManager.list_property("channels", accept_duplicate_values = False)
        def channels(self): pass

    @property
    def default_roles(self):
        if self._default_roles is None: self._default_roles = self.DefaultRoles(self.server_id)
        return self._default_roles
    class DefaultRoles(Server_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "default_roles")

        @Server_TableManager.list_property("default_roles", accept_duplicate_values = False)
        def default_roles(self): pass


    # INTEGRATED LISTS
    @property
    def moderation_strikes(self):
        if self._moderation_strikes is None: self._moderation_strikes = self.ModerationStrikes(self.server_id)
        return self._moderation_strikes
    class ModerationStrikes(IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("moderation_strikes", "server_id", server_id, "member_id")
    
    @property
    def member_levels(self):
        if self._member_levels is None: self._member_levels = self.MemberLevels(self.server_id)
        return self._member_levels
    class MemberLevels(IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("member_levels", "server_id", server_id, "member_id")
    
    @property
    def level_rewards(self):
        if self._level_rewards is None: self._level_rewards = self.LevelRewards(self.server_id)
        return self._level_rewards
    class LevelRewards(IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("level_rewards", "server_id", server_id, "role_id")

    @property
    def birthdays(self):
        if self._birthdays is None: self._birthdays = self.Birthdays(self.server_id)
        return self._birthdays
    class Birthdays(IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("birthdays", "server_id", server_id, "member_id")

    @property
    def autobans(self):
        if self._autobans is None: self._autobans = self.AutoBans(self.server_id)
        return self._autobans
    class AutoBans(IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("auto_bans", "server_id", server_id, "member_id")

    # MESSAGE LOGS
    @property
    def embeds(self):
        if self._embeds is None: self._embeds = self.Embeds(self.server_id)
        return self._embeds
    class Embeds(IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("embeds", "server_id", server_id, "message_id")

    @property
    def reaction_roles(self):
        if self._reaction_roles is None: self._reaction_roles = self.ReactionRoles(self.server_id)
        return self._reaction_roles
    class ReactionRoles(IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("reaction_roles", "server_id", server_id, "message_id")

    @property
    def role_messages(self):
        if self._role_messages is None: self._role_messages = self.RoleMessages(self.server_id)
        return self._role_messages
    class RoleMessages(IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("role_messages", "server_id", server_id, "message_id")
