from typing import Any
import unittest
import random
import string

from custom_types import UNSET_VALUE
from database import Database
from server import Server, Server_TableManager
from utils import format_var_to_pythonic_type
import server

# Database Tests
class TestDatabase(unittest.TestCase):
    def get_memory_database(self):
        return Database("sqlite://", "resources/test_db_build.sql")
    
    def create_test_row(self, database: Database, table, id):
        column_defaults = database.all_column_defaults[table]
        query_values = ", ".join(list(column_defaults.values()))
        query = f"INSERT OR IGNORE INTO {table} VALUES ({id}, {query_values})"
        database.execute_query(query, commit = True)

    def test_setup(self):
        database = self.get_memory_database()

    def test_database_integrity(self):
        database = self.get_memory_database()
        self.assertEqual(len(database.tables), 3)

        self.assertEqual(database.tables_to_optimize, ["table_1", "table_3"])
        self.assertEqual(database.all_column_defaults, 
                        {'table_1': {'example_bool': 'false', 'example_channel': '\'{"status": "UNSET", "value": null}\'', 'example_integer': '3', 'example_list': "'[]'"}, 
                         'table_2': {'example_bool': 'false'},
                         'table_3': {'example_bool': 'false', 'example_channel': '\'{"status": "UNSET", "value": null}\'', 'example_integer': '3', 'example_list': "'[]'"}})
        self.assertEqual(database.all_column_types, {'table_1': {'primary_key': 'INT', 'example_bool': 'BOOLEAN', 'example_channel': 'TEXT', 'example_integer': 'INT', 'example_list': 'TEXT'},
                                                     'table_2': {'primary_key_1': 'INT', 'primary_key_2': 'INT', 'example_integer': 'INT', 'example_bool': 'BOOLEAN'},
                                                     'table_3': {'primary_key': 'INT', 'example_bool': 'BOOLEAN', 'example_channel': 'TEXT', 'example_integer': 'INT', 'example_list': 'TEXT'}})
        self.assertEqual(database.all_column_names, {'table_1': ['primary_key', 'example_bool', 'example_channel', 'example_integer', 'example_list'], 
                                                     'table_2': ['primary_key_1', 'primary_key_2', 'example_integer', 'example_bool'],
                                                     'table_3': ['primary_key', 'example_bool', 'example_channel', 'example_integer', 'example_list']})
        self.assertEqual(database.all_primary_keys, {'table_1': 'primary_key', 'table_2': 'primary_key_1', 'table_3': 'primary_key'})

    def test_execute_query(self):
        database = self.get_memory_database()

        self.create_test_row(database, "table_1", 1234)

        result = database.execute_query(f"SELECT * FROM table_1", multiple_values=True)

        self.assertEqual(result, [(1234, 0, '{"status": "UNSET", "value": null}', 3, '[]')])

    def test_optimization(self):
        database = self.get_memory_database()

        test_servers = [random.randint(0, 1000000000) for _ in range(20)]
        
        for test_server in test_servers:
            self.create_test_row(database, "table_1", test_server)

        # Make changes on the first three
        for test_server in test_servers[:3]:
            query = f"UPDATE table_1 SET example_bool = 'true' WHERE primary_key = {test_server}"
            database.execute_query(query, commit = True)

        # Optimize Database
        database.optimize_database()

        # Check if only first three servers are still in the database
        results = database.execute_query("SELECT * FROM table_1", multiple_values=True)
        for result in results:
            self.assertIn(result[0], test_servers[:3])
        
        # Check if the rest of the servers are not in the database
        for test_server in test_servers[3:]:
            results = database.execute_query(f"SELECT * FROM table_1 WHERE primary_key = {test_server}", multiple_values=True)
            self.assertEqual(results, [])

    def test_force_remove_entry(self):
        database = self.get_memory_database()
        
        self.create_test_row(database, "table_1", 123456789)

        # Make changes
        query = f"UPDATE table_1 SET example_integer = 12 WHERE primary_key = 123456789"
        database.execute_query(query, commit = True)

        # Force remove entry
        database.force_remove_entry("table_1", 123456789)

        # Check if entry is removed
        results = database.execute_query(f"SELECT * FROM table_1 WHERE primary_key = 123456789", multiple_values=True)
        self.assertEqual(results, [])

    def test_get_column_default(self):
        database = self.get_memory_database()

        test_values_no_format = {
            "table_1": {
                "example_bool": 'false',
                "example_channel": '\'{"status": "UNSET", "value": null}\'',
                "example_integer": '3',
                "example_list": '\'[]\'',
                "primary_key": UNSET_VALUE
            },
            "table_2": {
                "example_integer": UNSET_VALUE,
                "example_bool": 'false',
                "primary_key_1": UNSET_VALUE,
                "primary_key_2": UNSET_VALUE
            }
        }

        test_values_with_format = {
            "table_1": {
                "example_bool": False,
                "example_channel": '{"status": "UNSET", "value": null}',
                "example_integer": 3,
                "example_list": '[]',
                "primary_key": UNSET_VALUE
            },
            "table_2": {
                "example_integer": UNSET_VALUE,
                "example_bool": False,
                "primary_key_1": UNSET_VALUE,
                "primary_key_2": UNSET_VALUE
            }
        }

        # Check without formatting
        for table in test_values_no_format:
            for column in test_values_no_format[table]:
                value = database.get_column_default(table, column, format = False)
                self.assertEqual(value, test_values_no_format[table][column])

        # Check with formatting
        for table in test_values_with_format:
            for column in test_values_with_format[table]:
                value = database.get_column_default(table, column, format = True)
                self.assertEqual(value, test_values_with_format[table][column])

    def test_does_entry_exist(self):
        database = self.get_memory_database()

        self.create_test_row(database, "table_1", 123456789)

        # Check if entry exists
        result = database.does_entry_exist("table_1", 123456789)
        self.assertEqual(result, True)

        # Check if entry doesn't exist
        result = database.does_entry_exist("table_1", 123456788)
        self.assertEqual(result, False)

    def test_get_table_unique_entries(self):
        database = self.get_memory_database()

        test_servers = [random.randint(0, 1000000000) for _ in range(20)]
        
        for test_server in test_servers:
            self.create_test_row(database, "table_1", test_server)

        # Get unique entries
        unique_entries_generator = database.get_table_unique_entries("table_1")
        unique_entries = [server for server in unique_entries_generator] # generator to list
        self.assertEqual(unique_entries, test_servers)

    def test_get_table_unique_entries(self):
        database = self.get_memory_database()

        test_servers = [random.randint(100000, 199999) for _ in range(20)]
        test_servers_unique_table_1 = [random.randint(200000, 299999) for _ in range(10)]
        test_servers_unique_table_3 = [random.randint(300000, 399999) for _ in range(10)]
        
        test_servers_table_1 = test_servers + test_servers_unique_table_1
        test_servers_table_3 = test_servers + test_servers_unique_table_3

        # Scramble the lists
        random.shuffle(test_servers_table_1)
        random.shuffle(test_servers_table_3)

        for test_server in test_servers_table_1:
            self.create_test_row(database, "table_1", test_server)

        for test_server in test_servers_table_3:
            self.create_test_row(database, "table_3", test_server)

        # Get unique entries for database
        unique_entries_generator = database.get_unique_entries_for_database()
        unique_entries = [server for server in unique_entries_generator] # generator to list

        # Check that all entries are unique
        unique_entries_set = set(unique_entries)
        self.assertEqual(len(unique_entries), len(unique_entries_set))
        
        # Check that the unique entries are the same as the test servers
        self.assertEqual(set(unique_entries), set(test_servers + test_servers_unique_table_1 + test_servers_unique_table_3))

    def test_get_id_sql_name(self):
        database = self.get_memory_database()

        answers = {
            "table_1": "primary_key",
            "table_2": "primary_key_1",
            "table_3": "primary_key"
        }

        for table in answers:
            result = database.get_id_sql_name(table)
            self.assertEqual(result, answers[table])

class TestServer(unittest.TestCase):
    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)
        # Overwrite variables
        server.database_url = f"sqlite://"
        server.init_database() # Hijack the database url to make it a memory database
    
    def test_server_creation(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        self.assertEqual(server.server_id, server_id)

        server.remove_all_data()

    def test_profainity_moderation_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)
        profile = server.profanity_moderation_profile

        self.assertEqual(profile.server_id, server_id)
        self.assertEqual(profile.active, False)
        self.assertEqual(profile.channel, UNSET_VALUE)
        self.assertEqual(profile.max_strikes, 3)
        self.assertEqual(profile.strike_expire_days, 7)
        self.assertEqual(profile.timeout_seconds, 3600)
        self.assertEqual(profile.custom_words, [])

        server.remove_all_data()

    def test_all_server_profiles(self):
        tables_to_check = ["profanity_moderation_profile"]

        values_to_check = {
            "int": lambda: random.choice([None] + [random.randint(0, 1000) for _ in range(10)]),
            "text": lambda: random.choice([""] + [random.choice(string.ascii_letters) for _ in range(10)]),
            "float": lambda: random.choice([None] + [random.uniform(0, 1000) for _ in range(10)]),
            "boolean": lambda: [random.choice([True, False]) for _ in range(10)],
            "date": lambda: random.choice([None] + [(str(random.randint(1000, 2024)) + "-" + 
                                                        str(random.randint(1, 12)).zfill(2) + "-" + 
                                                        str(random.randint(1, 28)).zfill(2)) for _ in range(10)])
        }

        def get_type(attr):
            if isinstance(attr, Server_TableManager.integer_property): return "int"
            if isinstance(attr, Server_TableManager.float_property): return "float"
            if isinstance(attr, Server_TableManager.boolean_property): return "boolean"
            if isinstance(attr, Server_TableManager.string_property): return "string"
            if isinstance(attr, Server_TableManager.channel_property): return "channel"
            if isinstance(attr, Server_TableManager.list_property): return "list"
            if isinstance(attr, Server_TableManager.embed_property): return "embed"

        servers_to_check = [random.randint(0, 1000000000) for _ in range(10)]

        for server_id in servers_to_check:
            for table in tables_to_check:
                inital_server = Server(server_id)
                self.assertTrue(hasattr(inital_server, table)) # Check table existence

                profile = getattr(inital_server, table)
                column_names_and_types = profile.get_column_names_and_types()
                column_names_and_defaults = profile.get_column_names_and_defaults()

                original_values = {}
                new_values = {}

                for attr in profile.__dict__().keys(): # For each attribute
                    self.assertTrue(hasattr(profile, attr)) # This should always be true

                    # Get the initial value
                    original_values[attr] = getattr(profile, attr)

                    attr_type = get_type(profile.__dict__()[attr])
                    new_value = values_to_check[attr_type.lower()]()
                    while new_value == original_values[attr]: # Don't let it be the default value
                        new_value = values_to_check[attr_type.lower()]()

                    print(f"Setting {attr} to {new_value}")
                    print(f"Original value: {original_values[attr]}")
                    print(f"Type: {attr_type}")
                    

                    new_values[attr] = new_value

                    setattr(profile, attr, new_values[attr])

                del inital_server
                    
                secondary_server = Server(server_id)

                for attr in profile.__dict__().keys(): # For each attribute
                    self.assertTrue(hasattr(profile, attr)) # This should always be true
                    
                    value = getattr(profile, attr)
                
                    self.assertEqual(value, new_values[attr])

                secondary_server.remove_all_data()
                del secondary_server

                third_server = Server(server_id)

                for attr in profile.__dict__().keys(): # For each attribute
                    self.assertTrue(hasattr(profile, attr)) # This should always be true
                    
                    value = getattr(profile, attr)
                    attr_type = column_names_and_types[attr]
                    self.assertEqual(value, original_values[attr])

                del third_server



if __name__ == "__main__":
    unittest.main()