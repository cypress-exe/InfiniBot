import unittest
import random
import uuid

from custom_types import UNSET_VALUE
from database import Database
from server import Server
import server

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
    def __init__(self, methodName:str = ...) -> None:
        super().__init__(methodName)
        # Overwrite variables
        server.database_url = f"sqlite:///"
        server.init_database() # Hijack the database url to make it a testing database
    
    def test_server_creation(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        self.assertEqual(server.server_id, server_id)

        server.remove_all_data()

    def run_test_on_property(self, primary_server_instance, table_name, property_name:str, default_value, test_values):
        print(f'Testing property "{property_name}". Default value: {default_value}, test values: {test_values}')
        
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
        
        def __init__(self, server: 'Server', table_name: str, test_values: list, iterations: list):
            self.server = server
            self.table_name = table_name
            self.test_values = test_values
            self.iterations = iterations

            # Ensure the minimum number of iterations is 2
            if self.iterations[0] < 2:
                self.iterations[0] = 2
                print("WARNING: Iterations[0] must be at least 2. Value changed.")

        def generate_test_data_for_integrated_lists(self):
            """Generates the test data with consistent secondary keys across iterations."""
            secondary_key_name = self.test_values[0].split(":")[0]
            secondary_key_values = []

            test_data = []

            for iteration_index in range(self.iterations[0]):
                iteration = []

                # For each row in this iteration
                for row_index in range(self.iterations[1]):
                    row_data = {}
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

                    iteration.append(row_data)
                # Scramble iteration
                random.shuffle(iteration)
                test_data.append(iteration)

            return test_data

        def run(self, test_case: unittest.TestCase):
            """Runs tests on the integrated list property for add, edit, and delete operations."""
            print("Running tests on integrated list property: " + self.table_name + " with test iterations: " + str(self.iterations))

            test_data = self.generate_test_data_for_integrated_lists()
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

            # Perform edits across iterations
            for iteration_number in range(1, self.iterations[0]):
                edit_test_data = test_data[iteration_number]

                for test_entry in edit_test_data:
                    secondary_key_value = list(test_entry.values())[0]
                    property.edit(secondary_key_value, **test_entry)

                self._verify_data_in_new_server_instance(test_case, self.server.server_id, edit_test_data)

            # Test deletions
            for test_entry in default_test_data:
                secondary_key_value = list(test_entry.values())[0]
                property.delete(secondary_key_value)

            # Verify all entries are deleted
            new_server_instance = Server(self.server.server_id)
            property = getattr(new_server_instance, self.table_name)
            test_case.assertEqual(len(property), 0)
            del new_server_instance

            print("Finished running tests on integrated list property: " + self.table_name)

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
        self.run_test_on_property(server, "profanity_moderation_profile", "custom_words", [], [["hello", "world"], ["apple", "banana", "orange", "pineapple", "grape"], []])

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


if __name__ == "__main__":
    unittest.main()