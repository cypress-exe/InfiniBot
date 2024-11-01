import unittest
import random
import uuid
import logging
import os

from src.custom_types import UNSET_VALUE
from src.log_manager import setup_logging

from src.database import Database
from src.server import Server
from src.file_manager import JSONFile
from src.global_settings import get_global_kill_status, get_persistent_data
from src.utils import feature_is_active

import src.server as server

def hijack_database_url():
    logging.warning("Hijacking database url to use memory database")
    server.database_url = "sqlite:///"
    server.init_database()

# Database Tests
class TestDatabase(unittest.TestCase):
    def get_memory_database(self):
        return Database("sqlite://", "resources/test_db_build.sql")
    
    def create_test_row(self, database:Database, table, id):
        column_defaults = database.all_column_defaults[table]
        query_values = ", ".join(list(column_defaults.values()))
        query = f"INSERT OR IGNORE INTO {table} VALUES ({id}, {query_values})"
        database.execute_query(query, commit = True)

    def test_setup(self):
        logging.info("Testing database setup...")
        database = self.get_memory_database()

    def test_database_integrity(self):
        logging.info("Testing database integrity...")
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
        logging.info("Testing that the database can execute queries...")
        database = self.get_memory_database()

        self.create_test_row(database, "table_1", 1234)

        result = database.execute_query(f"SELECT * FROM table_1", multiple_values=True)

        self.assertEqual(result, [(1234, 0, '{"status": "UNSET", "value": null}', 3, '[]')])

    def test_optimization(self):
        logging.info("Testing database optimization...")
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
        logging.info("Testing database force remove entry...")
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
        logging.info("Testing database get column default...")
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
        logging.info("Testing database does entry exist...")
        database = self.get_memory_database()

        self.create_test_row(database, "table_1", 123456789)

        # Check if entry exists
        result = database.does_entry_exist("table_1", 123456789)
        self.assertEqual(result, True)

        # Check if entry doesn't exist
        result = database.does_entry_exist("table_1", 123456788)
        self.assertEqual(result, False)

    def test_get_table_unique_entries(self):
        logging.info("Testing database get table unique entries...")
        database = self.get_memory_database()

        test_servers = [random.randint(0, 1000000000) for _ in range(20)]
        
        for test_server in test_servers:
            self.create_test_row(database, "table_1", test_server)

        # Get unique entries
        unique_entries_generator = database.get_table_unique_entries("table_1")
        unique_entries = [server for server in unique_entries_generator] # generator to list
        self.assertEqual(unique_entries, test_servers)

    def test_get_table_unique_entries(self):
        logging.info("Testing database get table unique entries...")
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
        logging.info("Testing database get id sql name...")
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
    def __init__(self, methodName:str = ...) -> None:
        super().__init__(methodName)
    
    def test_server_creation(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        self.assertEqual(server.server_id, server_id)

        server.remove_all_data()

    def run_test_on_property(self, primary_server_instance, table_name, property_name:str, default_value, test_values):
        logging.debug(f'Testing property "{property_name}". Default value: {default_value}, test values: {test_values}')
        
        def get_property(server, table_name, property_name):
            """Fetches the property from the server, handling itemized properties."""
            split_property_name = property_name.split("[")
            if len(split_property_name) == 2:
                item_name = split_property_name[1][:-1]  # Remove trailing "]"
                return getattr(getattr(server, table_name), split_property_name[0])[item_name]
            return getattr(getattr(server, table_name), property_name)

        def set_property(server, table_name, property_name, value):
            """Sets the property on the server, handling itemized properties."""
            split_property_name = property_name.split("[")
            if len(split_property_name) == 2:
                item_name = split_property_name[1][:-1]  # Remove trailing "]"
                prop = getattr(getattr(server, table_name), split_property_name[0])
                prop[item_name] = value
                setattr(getattr(server, table_name), split_property_name[0], prop)
            else:
                setattr(getattr(server, table_name), property_name, value)

        # Check the default value
        self.assertEqual(get_property(primary_server_instance, table_name, property_name), default_value, msg=f"Default value for \"{property_name}\" is claimed to be \"{default_value}\", but is \"{get_property(primary_server_instance, table_name, property_name)}\".")

        # Ensure test_values is a list
        if not isinstance(test_values, list):
            test_values = [test_values]

        # Check each test value
        for test_value in test_values:
            set_property(primary_server_instance, table_name, property_name, test_value)
            self.assertEqual(get_property(primary_server_instance, table_name, property_name), test_value)

            # Create a new server instance and verify the property value is consistent
            new_server_instance = Server(getattr(primary_server_instance, table_name).server_id)
            self.assertEqual(get_property(new_server_instance, table_name, property_name), test_value)
            del new_server_instance

    class RunTestOnIntegratedListProperty:
        """Helper class to generate test data and perform tests on integrated list properties."""
        
        def __init__(self, server: 'Server', table_name: str, test_values: list, iterations: list, extra_keys_to_query: list = []):
            self.server = server
            self.table_name = table_name
            self.test_values = test_values
            self.iterations = iterations # [iteration_count, rows_per_iteration]
            self.ektq = extra_keys_to_query

            # Ensure the minimum number of iterations is correct
            minimum_iterations = 2 + len(self.ektq)
            if self.iterations[0] < minimum_iterations:
                self.iterations[0] = minimum_iterations
                logging.warning(f"Iterations[0] must be at least {minimum_iterations}. Value changed.")

            minimum_rows = 0 if len(self.ektq) == 0 else 3
            if self.iterations[1] < minimum_rows:
                self.iterations[1] = minimum_rows
                logging.warning(f"Iterations[1] must be at least {minimum_rows}. Value changed.")

            self.ektq_row_values = {}
            self.ektw_row_mappings = {}

        def generate_test_data_for_integrated_lists(self):
            """Generates the test data with consistent secondary keys across iterations."""
            secondary_key_name = self.test_values[0].split(":")[0]
            secondary_key_values = []

            test_data = []

            for iteration_index in range(self.iterations[0]):
                iteration = []

                ektq_row_name = None
                ektq_row_value = None
                ektq_row_mapping = None
                index_of_ektq = iteration_index + len(self.ektq) - self.iterations[0]
                if index_of_ektq >= 0:
                    ektq_row_name = self.ektq[index_of_ektq]
                    ektq_row_value = UNSET_VALUE
                    
                    # Generate valid subset for consistent keys mapping
                    ektq_row_mapping = self._generate_valid_subset_for_ektq(self.iterations[1] - 1)

                # For each row in this iteration
                for row_index in range(self.iterations[1]):
                    row_data = {}
                    ektq_row = False
                    if ektq_row_mapping is not None:
                        if row_index in ektq_row_mapping:
                            ektq_row = True

                    for value in self.test_values:
                        value_name, value_type = value.split(":")

                        # If this is the secondary_key, we need special handling
                        if value_name == secondary_key_name:
                            # On the first iteration, generate unique secondary_key values
                            if iteration_index == 0:
                                if value_type == "int":
                                    key_value = random.randint(0, 1000000000)
                                    while key_value in secondary_key_values:
                                        key_value = random.randint(0, 1000000000)
                                elif value_type == "str":
                                    key_value = str(uuid.uuid4())
                                    while key_value in secondary_key_values:
                                        key_value = str(uuid.uuid4())
                                
                                # Store the unique secondary_key value for future iterations
                                secondary_key_values.append(key_value)

                            # In subsequent iterations, use the previously stored secondary_key
                            row_data[value_name] = secondary_key_values[row_index]
                        
                        # Handle other properties (non-secondary_key)
                        else:
                            valid = False
                            while not valid:
                                if value_type == "str":
                                    row_data[value_name] = str(uuid.uuid4())
                                elif value_type == "int":
                                    row_data[value_name] = random.randint(0, 1000000000)
                                elif value_type == "bool":
                                    row_data[value_name] = bool(random.randint(0, 1))
                                elif value_type == "float":
                                    row_data[value_name] = float(random.random() * random.randint(0, 1000000000))
                                elif value_type == "date":
                                    row_data[value_name] = f"{random.randint(1000, 9999)}-{random.randint(1, 12)}-{random.randint(1, 28)}"
                                
                                # Ensure the value is unique for non-secondary_key fields
                                valid = all(row_data[value_name] != row.get(value_name) for row in iteration)

                                # Overwrite the value if using a constant key
                                if ektq_row: # Extra Keys to Query in effect
                                    if value_name == ektq_row_name:
                                        if ektq_row_value == UNSET_VALUE: ektq_row_value = row_data[value_name]
                                        else: row_data[value_name] = ektq_row_value
                                        valid = True

                    iteration.append(row_data)

                # Add Extra Keys To Query (etkq) for later reference
                self.ektq_row_values[ektq_row_name] = ektq_row_value
                self.ektw_row_mappings[ektq_row_name] = ektq_row_mapping

                # Scramble iteration
                random.shuffle(iteration)
                test_data.append(iteration)

            return test_data

        def run(self, test_case: unittest.TestCase):
            """Runs tests on the integrated list property for add, edit, and delete operations."""
            logging.info("Running tests on integrated list property: " + self.table_name + " with test iterations: " + str(self.iterations))

            test_data = self.generate_test_data_for_integrated_lists()
            logging.debug("Generated test data")
            default_test_data = test_data[0]

            property = getattr(self.server, self.table_name)
            test_case.assertEqual(len(property), 0)

            # Add test entries
            for test_entry in default_test_data:
                property.add(**test_entry)

            # Verify the entries were added correctly
            self._verify_entries(test_case, property, default_test_data)

            # Verify consistency with a new server instance
            self._verify_data_in_new_server_instance(test_case, self.server.server_id, default_test_data)

            logging.debug(f"Adding entries to integrated list property \"{self.table_name}\" successful.")

            # Perform edits across iterations
            for iteration_number in range(1, self.iterations[0]):
                edit_test_data = test_data[iteration_number]

                for test_entry in edit_test_data:
                    secondary_key_value = list(test_entry.values())[0]
                    property.edit(secondary_key_value, **test_entry)

                self._verify_data_in_new_server_instance(test_case, self.server.server_id, edit_test_data)

                # See if this is an iteration with extra keys to query (ektq)
                index_of_ektq = ((iteration_number) + len(self.ektq)) - self.iterations[0]
                if index_of_ektq >= 0:
                    ektq_row_name = self.ektq[index_of_ektq]
                    ektq_row_value = self.ektq_row_values[ektq_row_name]
                    ektq_row_mapping = self.ektw_row_mappings[ektq_row_name]
                    rows = property.get_matching(**{ektq_row_name: ektq_row_value})
                    
                    test_case.assertEqual(len(rows), len(ektq_row_mapping), msg = "Integrated List Failure: class.get_maching returned incorrect number of rows. Expected: " + str(len(ektq_row_mapping)) + " Actual: " + str(len(rows)))
                    for row in rows:
                        test_case.assertEqual(getattr(row, ektq_row_name), ektq_row_value, msg = "Integrated List Failure: class.get_maching returned at least one incorrect row. Expected: " + str(ektq_row_value) + " Actual: " + str(getattr(row, ektq_row_name)))
                    logging.debug(f"Extra Keys To Query (etkq) successful for iteration {iteration_number + 1}.")


            logging.debug(f"Editing entries in integrated list property \"{self.table_name}\" successful.")

            # Test deletions
            for test_entry in default_test_data:
                secondary_key_value = list(test_entry.values())[0]
                property.delete(secondary_key_value)

            # Verify all entries are deleted
            new_server_instance = Server(self.server.server_id)
            property = getattr(new_server_instance, self.table_name)
            test_case.assertEqual(len(property), 0)
            del new_server_instance

            logging.debug(f"Deleting entries in integrated list property \"{self.table_name}\" successful.")

            logging.info("Finished running tests on integrated list property: " + self.table_name)

        def _verify_entries(self, test_case, property, test_data):
            """Helper function to verify that the entries match the expected data."""
            for test_entry in test_data:
                secondary_key_value = list(test_entry.values())[0]
                for key, value in test_entry.items():
                    test_case.assertEqual(getattr(property[secondary_key_value], key), value)

        def _verify_data_in_new_server_instance(self, test_case, server_id, test_data):
            """Helper function to create a new server instance and verify data consistency."""
            new_server_instance = Server(server_id)
            property = getattr(new_server_instance, self.table_name)

            for test_entry in test_data:
                secondary_key_value = list(test_entry.values())[0]
                data = property[secondary_key_value]
                for key, value in test_entry.items():
                    test_case.assertEqual(getattr(data, key), value)

            del new_server_instance

        def _generate_unique_value(self, existing_values, value_type):
            """Generates a unique value based on the type and ensures it doesn't conflict."""
            if value_type == "str":
                value = str(uuid.uuid4())
                while value in existing_values:
                    value = str(uuid.uuid4())
            elif value_type == "int":
                value = random.randint(0, 1000000000)
                while value in existing_values:
                    value = random.randint(0, 1000000000)
            elif value_type == "bool":
                value = bool(random.randint(0, 1))
            elif value_type == "float":
                value = float(random.random() * random.randint(0, 1000000000))
            return value

        def _generate_valid_subset_for_ektq(self, X):
            """Generates a random valid subset of X elements for constant keys."""
            # Create a range of elements from 0 to X (inclusive)
            full_range = range(0, X + 1)

            # Choose a random subset length between 2 and X (inclusive)
            r = random.randint(2, X)

            # Randomly select a valid combination of size 'r' from the full range
            random_combination = random.sample(full_range, r)

            return random_combination

    # PROFILES
    def test_profainity_moderation_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "profanity_moderation_profile", "active", False, [True, False])
        self.run_test_on_property(server, "profanity_moderation_profile", "channel", UNSET_VALUE, [1234567989, None, UNSET_VALUE])
        self.run_test_on_property(server, "profanity_moderation_profile", "max_strikes", 3, [5, 0])
        self.run_test_on_property(server, "profanity_moderation_profile", "strike_expire_days", 7, [10, 0])
        self.run_test_on_property(server, "profanity_moderation_profile", "timeout_seconds", 3600, [7200, 0])
        self.run_test_on_property(server, "profanity_moderation_profile", "filtered_words", [], [["hello", "world"], ["apple", "banana", "orange", "pineapple", "grape"], []])

        server.remove_all_data()

    def test_spam_moderation_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "spam_moderation_profile", "active", False, [True, False])
        self.run_test_on_property(server, "spam_moderation_profile", "messages_threshold", 5, [12, 0])
        self.run_test_on_property(server, "spam_moderation_profile", "timeout_seconds", 60, [140, 0])
        self.run_test_on_property(server, "spam_moderation_profile", "delete_invites", False, [True, False])

        server.remove_all_data()

    def test_logging_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "logging_profile", "active", False, [True, False])
        self.run_test_on_property(server, "logging_profile", "channel", UNSET_VALUE, [1234567989, UNSET_VALUE])

        server.remove_all_data()

    def test_leveling_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "leveling_profile", "active", False, [True, False])
        self.run_test_on_property(server, "leveling_profile", "channel", UNSET_VALUE, [1234567989, None, UNSET_VALUE])
        self.run_test_on_property(server, "leveling_profile", "level_up_embed[title]", "Congratulations, @displayname!", ["Title_Changed", None])
        self.run_test_on_property(server, "leveling_profile", "level_up_embed[description]", "Congrats @member! You reached level [level]!", ["Description_Changed"])
        self.run_test_on_property(server, "leveling_profile", "points_lost_per_day", 5, [12, 0])
        self.run_test_on_property(server, "leveling_profile", "exempt_channels", [], [[1234567989, 256468532], [1234567989, 256468532, 494621612]])
        self.run_test_on_property(server, "leveling_profile", "allow_leveling_cards", True, [False, True])

        server.remove_all_data()

    def test_join_message_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "join_message_profile", "active", False, [True, False])
        self.run_test_on_property(server, "join_message_profile", "channel", UNSET_VALUE, [1234567989, UNSET_VALUE])
        self.run_test_on_property(server, "join_message_profile", "embed[title]", "@displayname just joined the server!", ["Title_Changed", None])
        self.run_test_on_property(server, "join_message_profile", "embed[description]", "Welcome to the server, @member!", ["Description_Changed"])
        self.run_test_on_property(server, "join_message_profile", "allow_join_cards", True, [False, True])

        server.remove_all_data()

    def test_leave_message_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "leave_message_profile", "active", False, [True, False])
        self.run_test_on_property(server, "leave_message_profile", "channel", UNSET_VALUE, [1234567989, UNSET_VALUE])
        self.run_test_on_property(server, "leave_message_profile", "embed[title]", "@displayname just left the server.", ["Title_Changed", None])
        self.run_test_on_property(server, "leave_message_profile", "embed[description]", "@member left.", ["Description_Changed"])

        server.remove_all_data()

    def test_birthdays_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "birthdays_profile", "channel", UNSET_VALUE, [1234567989, None, UNSET_VALUE])
        self.run_test_on_property(server, "birthdays_profile", "embed[title]", "Happy Birthday, @realname!", ["Title_Changed", None])
        self.run_test_on_property(server, "birthdays_profile", "embed[description]", "@member just turned @age!", ["Description_Changed"])
        self.run_test_on_property(server, "birthdays_profile", "runtime", "8:00", ["12:00", "8:00", "18:00", "0:00"])

        server.remove_all_data()

    def test_infinibot_settings_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "infinibot_settings_profile", "get_updates", True, [False, True])

        server.remove_all_data()

    # SIMPLE LISTS
    def test_join_to_create_vcs(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "join_to_create_vcs", "channels", [], [[1234567989, 256468532], [1234567989, 256468532, 494621612]])

        server.remove_all_data()

    def test_default_roles(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "default_roles", "default_roles", [], [[1234567989, 256468532], [1234567989, 256468532, 494621612]])

        server.remove_all_data()

    # INTEGRATED LISTS
    def test_moderation_strikes(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_integrated_list_property
        test = self.RunTestOnIntegratedListProperty(server, "moderation_strikes", ["member_id:int", "strikes:int", "last_strike:date"], [5, 20])
        test.run(self)

        server.remove_all_data()

    def test_level_rewards(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_integrated_list_property
        test = self.RunTestOnIntegratedListProperty(server, "level_rewards", ["role_id:int", "level:int"], [5, 20])
        test.run(self)
        
        server.remove_all_data()

    def test_birthdays(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_integrated_list_property
        test = self.RunTestOnIntegratedListProperty(server, "birthdays", ["member_id:int", "birth_date:date", "real_name:str"], [5, 20])
        test.run(self)

        server.remove_all_data()

    def test_autobans(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_integrated_list_property
        test = self.RunTestOnIntegratedListProperty(server, "autobans", ["member_id:int", "member_name:str"], [5, 20])
        test.run(self)

        server.remove_all_data()

    # MESSAGE LOGS
    def test_embeds(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_integrated_list_property
        test = self.RunTestOnIntegratedListProperty(server, "embeds", ["message_id:int", "channel_id:int", "author_id:int"], [3, 10], extra_keys_to_query=["channel_id"])
        test.run(self)

        server.remove_all_data()

    def test_reaction_roles(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_integrated_list_property
        test = self.RunTestOnIntegratedListProperty(server, "reaction_roles", ["message_id:int", "channel_id:int", "author_id:int"], [3, 10], extra_keys_to_query=["channel_id"])
        test.run(self)

        server.remove_all_data()

    
    def test_role_messages(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_integrated_list_property
        test = self.RunTestOnIntegratedListProperty(server, "role_messages", ["message_id:int", "channel_id:int", "author_id:int"], [3, 10], extra_keys_to_query=["channel_id"])
        test.run(self)

        server.remove_all_data()

class TestFileManager(unittest.TestCase):
    def test_json_file(self):
        logging.info("Testing FileManager -> JSONFile...")
        test_file = JSONFile("test_file")
        path = test_file.path

        self.assertEqual(test_file.file_name, "test_file.json")

        test_file.add_variable("bool1", True)
        test_file.add_variable("bool2", False)
        test_file.add_variable("bool3", True)

        self.assertTrue(test_file["bool1"])
        self.assertFalse(test_file["bool2"])
        self.assertTrue(test_file["bool3"])

        self.assertTrue(len(test_file) == 3)

        test_file["bool2"] = True
        test_file["bool3"] = False

        del test_file

        # New instance
        test_file = JSONFile("test_file")

        self.assertTrue(test_file["bool1"])
        self.assertTrue(test_file["bool2"])
        self.assertFalse(test_file["bool3"])

        for variable in test_file:
            self.assertTrue(variable in ["bool1", "bool2", "bool3"])

        test_file.delete_file()
        self.assertTrue(not os.path.exists(path))

        logging.info("Finished testing FileManager -> JSONFile...")

class TestGlobalSettings(unittest.TestCase):
    def test_global_kill_status(self):
        logging.info("Testing GlobalKillStatus...")

        # Clear file
        get_global_kill_status().reset()

        self.assertFalse(get_global_kill_status()["profanity_moderation"])

        get_global_kill_status()["profanity_moderation"] = True
        self.assertTrue(get_global_kill_status()["profanity_moderation"])

        self.assertRaises(AttributeError, get_global_kill_status().__getitem__, "fake_item")

        self.assertRaises(AttributeError, get_global_kill_status().__setitem__, "fake_item", True)

        logging.info("Finished testing GlobalKillStatus...")

    def test_persistent_data(self):
        logging.info("Testing PersistentData...")

        # Clear file
        get_persistent_data().reset()

        self.assertFalse(get_persistent_data()["login_response_guildID"])

        get_persistent_data()["login_response_guildID"] = True
        self.assertTrue(get_persistent_data()["login_response_guildID"])

        self.assertRaises(AttributeError, get_persistent_data().__getitem__, "fake_item")

        self.assertRaises(AttributeError, get_persistent_data().__setitem__, "fake_item", True)

        logging.info("Finished testing PersistentData...")

class TestUtils(unittest.TestCase):
    def test_feature_is_active(self):
        logging.info("Testing feature_is_active...")

        # Clear global kill status file to get consistent results
        get_global_kill_status().reset()

        # BEGIN TESTING 
        self.assertFalse(feature_is_active(server_id=1, feature="profanity_moderation"),
                        "Should have returned False as the feature is not globally killed, but the server has the feature disabled by default")

        # Test that if the server has the feature disabled, it will return False
        server = Server(random.randint(0, 1000000000))
        server.profanity_moderation_profile.active = True

        self.assertTrue(feature_is_active(server=server, feature="profanity_moderation"),
                         "Should have returned True as the feature is enabled in the server and is not globally killed")

        server.remove_all_data()

        # Test that if the feature is globally killed, it will return False regardless of the server's settings
        get_global_kill_status()["profanity_moderation"] = True

        self.assertFalse(feature_is_active(server_id=1, feature="profanity_moderation"),
                         "Should have returned False as the feature is globally killed")

        server = Server(random.randint(0, 1000000000))
        server.profanity_moderation_profile.active = True

        self.assertFalse(feature_is_active(server=server, feature="profanity_moderation"),
                         "Should have returned False as the feature is globally killed")
        
        server.remove_all_data()

        get_global_kill_status().reset()

        logging.info("Finished testing feature_is_active...")

if __name__ == "__main__":
    print("RUNNING ---------------------------------------------------------------------------------------------------------")
    setup_logging(logging.DEBUG)

    hijack_database_url()

    logging.info("######################## Running Tests ########################")
    unittest.main()