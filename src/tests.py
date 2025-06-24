#!/usr/bin/env python3

import nextcord
import datetime
import json
import logging
import os
import random
import shutil
import sys
import unittest
import uuid
from typing import Any, List, Dict
from zoneinfo import ZoneInfo

import core.db_manager as db_manager
from components.utils import feature_is_active
from config.file_manager import JSONFile, update_base_path as file_manager_update_base_path, read_txt_to_list
from config.global_settings import required_permissions, get_global_kill_status
from config.member import Member
from config.server import Server
from config.stored_messages import StoredMessage, cleanup, get_all_messages, get_message, remove_message, store_message
from core.log_manager import setup_logging, update_base_path as log_manager_update_base_path
from modules.custom_types import UNSET_VALUE
from modules.database import Database

"""
This file contains a collection of tests for the database module.

The tests are run using the unittest framework provided by Python.

The tests are run in a separate thread to prevent blocking the main thread.

Available arguments:
--run-all: Run all tests in this file, regardless of specific_tests_to_run status.
--retry-once-on-failure: If a test fails, retry it once before returning failure.
"""


def update_database_url() -> None:
    """
    Updates the database URL to use an in-memory database for testing purposes.

    :return: None
    :rtype: None
    """
    logging.warning("Updating database url to use memory database")
    db_manager.database_url = "sqlite:///./generated/test-files/files/test.db"
    db_manager.init_database()

def generate_test_message(**kwargs) -> StoredMessage:
    message = StoredMessage(
        message_id=random.randint(0, 1000000000),
        guild_id=random.randint(0, 1000000000),
        channel_id=random.randint(0, 1000000000),   
        author_id=random.randint(0, 1000000000),
        content="".join([random.choice(r"abcdefghijklmnopqrstuvwxyz!@#$%^&*()_+-=[]{};:'<>,./? ") for _ in range(random.randint(1, 4000))]),
        last_updated=datetime.datetime.now(ZoneInfo("UTC"))
    )

    for key, value in kwargs.items():
        setattr(message, key, value)

    return message

# Database Tests
class TestDatabase(unittest.TestCase):
    def _steps(self):
        for name in dir(self): # dir() result is implicitly sorted
            if name.startswith("step"):
                yield name, getattr(self, name) 

    def entrypoint(self):
        for name, step in self._steps():
            try:
                step()
            except Exception as e:
                self.fail("{} failed ({}: {})".format(name, type(e), e))

    def get_memory_database(self) -> Database:
        """
        Retrieves an instance of the `Database` class, but with the database
        URL alterned to use an in-memory database for testing purposes.

        :return: An instance of the `Database` class connected to an
            in-memory database.
        :rtype: Database
        """
        return Database("sqlite://", "resources/test_db_build.sql")
    
    def cleanup(self, database: Database) -> None:
        """Cleanup after test"""
        database.cleanup()

    def create_test_row(self, database: Database, table: str, id: int) -> None:
        """
        Creates a test row in the given table.

        :param database: The database to use.
        :type database: Database
        :param table: The table to insert the row into.
        :type table: str
        :param id: The primary key of the row to insert.
        :type id: int
        :return: None
        :rtype: None
        """
        column_defaults = database.all_column_defaults[table]
        query_values = ", ".join(list(column_defaults.values()))
        query = f"INSERT OR IGNORE INTO {table} VALUES ({id}, {query_values})"
        database.execute_query(query, commit = True)

    def step1_test_setup(self) -> None:
        """
        Tests the setup of the database.

        :return: None
        :rtype: None
        """
        logging.info("Testing database setup...")
        database = self.get_memory_database()

        self.cleanup(database)

    def step2_test_database_integrity(self) -> None:
        """
        Tests the integrity of the database.

        Ensures that the database has been properly set up and that the
        database's integrity is maintained.

        :return: None
        :rtype: None
        """
        logging.info("Testing database integrity...")
        database = self.get_memory_database()
        self.assertEqual(len(database.tables), 3)

        self.assertEqual(database.tags, {"table_1": {"optimize": True, "remove-if-guild-invalid": "example_integer"}, "table_3": {"optimize": True, "test-tag": "argument"}})
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

        self.cleanup(database)

    def step3_test_execute_query(self) -> None:
        """
        Tests that the database can execute queries properly.

        :param: None
        :type: None
        :return: None
        :rtype: None
        """
        logging.info("Testing that the database can execute queries...")
        database = self.get_memory_database()

        self.create_test_row(database, "table_1", 1234)

        result = database.execute_query(f"SELECT * FROM table_1", multiple_values=True)

        self.assertEqual(result, [(1234, 0, '{"status": "UNSET", "value": null}', 3, '[]')])

        self.cleanup(database)

    def step4_test_optimization(self) -> None:
        """
        Tests database optimization.

        :param: None
        :type: None
        :return: None
        :rtype: None
        """
        logging.info("Testing database optimization...")

        database = self.get_memory_database()

        test_servers = [random.randint(0, 1000000000) for _ in range(20)]
        
        for test_server in test_servers:
            self.create_test_row(database, "table_1", test_server)

        # Make changes on the first three
        for test_server in test_servers[:3]:
            query = f"UPDATE table_1 SET example_bool = 'true' WHERE primary_key = {test_server}"
            database.execute_query(query, commit=True)

        # Optimize Database
        database.optimize_database()

        # Check if only first three servers are still in the database
        results = database.execute_query("SELECT * FROM table_1", multiple_values=True)
        for result in results:
            self.assertIn(result[0], test_servers[:3], msg=f"Optimization failed. Server {result[0]} is not in the set of servers {test_servers[:3]} that should be in the database.\nServers that should have been removed: {test_servers[3:]}")
        
        # Check if the rest of the servers are not in the database
        for test_server in test_servers[3:]:
            results = database.execute_query(f"SELECT * FROM table_1 WHERE primary_key = {test_server}", multiple_values=True)
            self.assertEqual(results, [])

        self.cleanup(database)

    def step5_test_force_remove_entry(self) -> None:
        """
        Tests database force remove entry.

        :param: None
        :type: None
        :return: None
        :rtype: None
        """
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

        self.cleanup(database)

    def step6_test_get_column_default(self) -> None:
        """
        Tests the `get_column_default` method of the `Database` class.

        Checks if the default values of columns in tables are correctly retrieved
        both with and without formatting.

        :param: None
        :type: None
        :return: None
        :rtype: None
        """
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

        self.cleanup(database)

    def step7_test_does_entry_exist(self) -> None:
        """
        Tests the does_entry_exist function of the database.

        :param self: The instance of the TestDatabase object.
        :type self: TestDatabase
        :return: None
        :rtype: None
        """
        logging.info("Testing database does entry exist...")
        database = self.get_memory_database()

        self.create_test_row(database, "table_1", 123456789)

        # Check if entry exists
        result = database.does_entry_exist("table_1", 123456789)
        self.assertEqual(result, True)

        # Check if entry doesn't exist
        result = database.does_entry_exist("table_1", 123456788)
        self.assertEqual(result, False)

        self.cleanup(database)

    def step8_test_get_table_unique_entries(self) -> None:
        """
        Tests the get_table_unique_entries function of the database.

        :param self: The instance of the TestDatabase object.
        :type self: TestDatabase
        :return: None
        :rtype: None
        """
        logging.info("Testing database get table unique entries...")
        database = self.get_memory_database()

        test_servers = [random.randint(0, 1000000000) for _ in range(20)]
        
        for test_server in test_servers:
            self.create_test_row(database, "table_1", test_server)

        # Get unique entries
        unique_entries_generator = database.get_table_unique_entries("table_1")
        unique_entries = [server for server in unique_entries_generator] # generator to list

        self.assertEqual(sorted(unique_entries), sorted(test_servers))
        
        self.cleanup(database)

    def step9_test_get_unique_entries_for_database(self) -> None:
        """
        Tests the get_unique_entries_for_database function of the database.

        :param self: The instance of the TestDatabase object.
        :type self: TestDatabase
        :return: None
        :rtype: None
        """
        logging.info("Testing database get unique entries for database...")
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

        self.cleanup(database)

    def step10_test_get_id_sql_name(self) -> None:
        """
        Tests the get_id_sql_name function of the database.

        :param self: The instance of the TestDatabase object.
        :type self: TestDatabase
        :return: None
        :rtype: None
        """
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

        self.cleanup(database)

class TestStoredMessages(unittest.TestCase):
    def _steps(self):
        for name in dir(self): # dir() result is implicitly sorted
            if name.startswith("step"):
                yield name, getattr(self, name) 

    def entrypoint(self):
        for name, step in self._steps():
            try:
                step()
            except Exception as e:
                self.fail("{} failed ({}: {})".format(name, type(e), e))

    def step1_test_add_message(self) -> None:
        """
        Tests the addition of a message to the database.

        :param self: The instance of the TestStoredMessages object.
        :type self: TestStoredMessages
        :return: None
        :rtype: None
        """
        logging.info("Testing addition of a message to the database...")

        # Test a large message
        content = "".join([random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(4000)]) # Max 4000 characters size for discord messages

        # Other data
        message_id = random.randint(0, 1000000000)
        guild_id = random.randint(0, 1000000000)
        channel_id = random.randint(0, 1000000000)
        author_id = random.randint(0, 1000000000)
        last_updated = datetime.datetime.now(ZoneInfo("UTC"))

        # Create a test message
        test_message = StoredMessage(
            message_id=message_id,
            guild_id=guild_id,
            channel_id=channel_id,
            author_id=author_id,
            content=content,
            last_updated=last_updated
        )

        # Check that StoredMessage behaves correctly
        self.assertEqual(test_message.message_id, message_id)
        self.assertEqual(test_message.guild_id, guild_id)
        self.assertEqual(test_message.channel_id, channel_id)
        self.assertEqual(test_message.author_id, author_id)
        self.assertEqual(test_message.content, content)
        self.assertEqual(test_message.last_updated, last_updated)

        # Store the message
        store_message(test_message, override_checks=True)

        # Check that the message was stored correctly
        message_result = get_message(test_message.message_id)

        self.assertEqual(message_result.message_id, test_message.message_id)
        self.assertEqual(message_result.guild_id, test_message.guild_id)
        self.assertEqual(message_result.channel_id, test_message.channel_id)
        self.assertEqual(message_result.author_id, test_message.author_id)
        self.assertEqual(message_result.content, test_message.content)

        # Remove the test message
        remove_message(test_message.message_id)

        logging.info("Test for addition of a message to the database completed successfully.")

    def step2_test_message_destruction(self) -> None:
        """
        Tests the destruction of a message in the database.

        :param self: The instance of the TestStoredMessages object.
        :type self: TestStoredMessages
        :return: None
        :rtype: None
        """
        logging.info("Testing destruction of a message in the database...")

        # Create a test message
        test_message = generate_test_message()

        store_message(test_message, override_checks=True)

        remove_message(test_message.message_id)

        # Check that the message was removed
        query = f"SELECT * FROM messages WHERE message_id = {test_message.message_id}"
        result = db_manager.get_database().execute_query(query, multiple_values=True)

        self.assertEqual(len(result), 0)

        logging.info("Test for destruction of a message in the database completed successfully.")

    def step3_test_get_all_messages(self) -> None:
        """
        Tests the retrieval of all messages from the database.

        :param self: The instance of the TestStoredMessages object.
        :type self: TestStoredMessages
        :return: None
        :rtype: None
        """
        logging.info("Testing retrieval of all messages from the database...")

        # Clear the database
        db_manager.get_database().execute_query("DELETE FROM messages", commit=True)

        # Generate a set of unique guild IDs
        unique_guilds = set()
        while len(unique_guilds) < 17: # Arbitrary number of guilds
            unique_guilds.add(random.randint(0, 1000000000))
        unique_guilds = list(unique_guilds)

        # Create some test messages
        test_messages = [generate_test_message(guild_id=random.choice(unique_guilds)) for _ in range(250)]

        test_messages_to_store = test_messages
        random.shuffle(test_messages_to_store)

        # Store the test messages
        for message in test_messages_to_store:
            store_message(message, override_checks=True)

        # Retrieve all messages
        messages = get_all_messages()

        # Check that all messages were retrieved
        for message in test_messages:
            self.assertIn(message, messages)

        # Remove the test messages
        for message in test_messages:
            remove_message(message.message_id)

        # Ensure the database is empty
        messages = get_all_messages()
        self.assertEqual(len(messages), 0)

        # Delete all messages in the database to prepare for the next test (should be empty anyway, but doesn't hurt)
        db_manager.get_database().execute_query("DELETE FROM messages", commit=True)

        logging.info("Test for retrieving all messages from the database completed successfully.")

    def step4_test_quantity_based_cleanup(self, guilds=10, max_messages_to_keep_per_guild=50) -> None:
        """
        Tests the cleanup of the database based on message quantity limits.

        This test verifies that the number of messages per guild does not exceed 
        the configured maximum (`max_messages_to_keep_per_guild`).

        :param self: The instance of the TestStoredMessages object.
        :param guilds: The number of unique guilds to generate test data for. Defaults to 10.
        :param max_messages_to_keep_per_guild: The maximum number of messages to keep per guild. Defaults to 50.
        :return: None
        :rtype: None
        """
        logging.info("Testing cleanup (quantity based) of the database...")

        # Generate a TON of messages
        unique_guilds = set()
        while len(unique_guilds) < guilds:
            unique_guilds.add(random.randint(0, 1000000000))
        unique_guilds = list(unique_guilds)

        persistent_messages = []
        overflow_messages = []

        overflowed_guilds = round(len(unique_guilds) * (1/2)) # 1/2 of the guilds will be over-filled

        # First few guilds will be over-filled (more than discord-message-logging.max_messages_to_keep_per_guild)
        for i in range(overflowed_guilds):
            guild = unique_guilds[i]

            # Generate a TON of messages
            extra_messages = random.randint(1, round(max_messages_to_keep_per_guild/10))
            messages_for_this_guild = [
                generate_test_message(guild_id=guild)
                for _ in range(max_messages_to_keep_per_guild + extra_messages)
            ]
            
            persistent_messages.extend(messages_for_this_guild[-max_messages_to_keep_per_guild:])
            overflow_messages.extend(messages_for_this_guild[:-max_messages_to_keep_per_guild])
            logging.info(f"Part 1 - Generated {len(messages_for_this_guild)} messages for guild {guild}")

        # The rest of the guilds will be under-filled (less than discord-message-logging.max_messages_to_keep_per_guild)
        for i in range(overflowed_guilds, len(unique_guilds)):
            guild = unique_guilds[i]

            # Generate a TON of messages (but less than max_messages_to_keep_per_guild)
            messages_for_this_guild = []
            for _ in range(random.randint(1, max_messages_to_keep_per_guild - 1)):
                messages_for_this_guild.append(generate_test_message(guild_id=guild))

            persistent_messages.extend(messages_for_this_guild)
            logging.info(f"Part 2 - Generated {len(messages_for_this_guild)} messages for guild {guild}")

        all_messages = persistent_messages + overflow_messages

        # Store the test messages
        messages_stored = 0
        for message in all_messages:
            store_message(message, override_checks=True)
            messages_stored += 1

            if messages_stored % 100 == 0:
                logging.info(f"Part 3 - Stored {messages_stored} messages (currently storing messages for guild {message.guild_id})")

        logging.info(f"Stored {messages_stored} messages in total.")
        logging.info(f"Persistent messages: {len(persistent_messages)}")

        # Run the cleanup
        logging.info("Running cleanup...")
        cleanup(max_messages_to_keep_per_guild=max_messages_to_keep_per_guild)
        logging.info("Cleanup complete.")

        # Check that the correct number of messages were deleted
        retrieved_messages = get_all_messages()

        logging.info(f"Retrieved {len(retrieved_messages)} messages from the database after cleanup.")
        
        # Turn them into a set to remove duplicates
        retrieved_messages_set = set(retrieved_messages)
        self.assertEqual(len(retrieved_messages), len(retrieved_messages_set), msg="Duplicate messages found in the database after cleanup.")

        all_messages_set = set(all_messages)
        self.assertEqual(len(all_messages), len(all_messages_set), msg="Duplicate messages found in the test data.")

        persistent_messages_set = set(persistent_messages)
        self.assertEqual(len(persistent_messages), len(persistent_messages_set), msg="Duplicate messages found in the retrieved data.")

        # Check that the correct number of messages were kept
        self.assertEqual(len(persistent_messages), len(retrieved_messages), msg="Incorrect number of messages found in the database after cleanup.")

        # Check that the correct number of messages were deleted
        self.assertEqual(retrieved_messages_set, persistent_messages_set, msg="Incorrect content of messages left in the database after cleanup.")

        # Delete all messages in the database to prepare for the next test
        db_manager.get_database().execute_query("DELETE FROM messages", commit=True)

        logging.info("Test for cleanup of the database (quantity based) completed successfully.")

    def step5_test_age_based_cleanup(self, guilds=10) -> None:
        """
        Tests the cleanup of the database based on message age and count limits.

        This test verifies that messages older than 7 days are removed.
        > Note: This threshold is hardcoded in this test, but is not representative of the actual threshold for the production code.

        :param self: The instance of the TestStoredMessages object.
        :param guilds: The number of unique guilds to generate test data for. Defaults to 10.
        :return: None
        """
        logging.info("Testing cleanup (age based) of the database...")

        max_days_to_keep = 7

        # Generate a TON of messages
        unique_guilds = set()
        while len(unique_guilds) < guilds:
            unique_guilds.add(random.randint(0, 1000000000))
        unique_guilds = list(unique_guilds)

        persistent_messages = []
        overdue_messages = []

        overdue_guilds = round(len(unique_guilds) * (1/2)) # 1/2 of the guilds will have overdue messages

        # First few guilds will have overdue messages (older than max_days_to_keep)
        for i in range(overdue_guilds):
            guild = unique_guilds[i]

            # Generate some overdue messages
            overdue_messages_count = random.randint(1, 30)
            messages_for_this_guild = [
                generate_test_message(guild_id=guild, 
                                      last_updated=datetime.datetime.now(ZoneInfo("UTC")) - datetime.timedelta(seconds=random.randint((max_days_to_keep+1)*24*60*60, (max_days_to_keep+100)*24*60*60)))
                for _ in range(overdue_messages_count)
            ]

            # Generate some recent messages
            recent_messages_count = random.randint(1, 30)
            messages_for_this_guild.extend([
                generate_test_message(guild_id=guild, 
                                      last_updated=datetime.datetime.now(ZoneInfo("UTC")) - datetime.timedelta(seconds=random.randint(1*24*60*60, max_days_to_keep*24*60*60)))
                for _ in range(recent_messages_count)
            ])
            
            persistent_messages.extend(messages_for_this_guild[overdue_messages_count:])
            overdue_messages.extend(messages_for_this_guild[:overdue_messages_count])
            logging.info(f"Part 1 - Generated {len(messages_for_this_guild)} messages for guild {guild}")

        # The rest of the guilds will not have overdue messages
        for i in range(overdue_guilds, len(unique_guilds)):
            guild = unique_guilds[i]

            # Generate some recent messages
            messages_for_this_guild = [
                generate_test_message(guild_id=guild, 
                                      last_updated=datetime.datetime.now(ZoneInfo("UTC")) - datetime.timedelta(seconds=random.randint(1*24*60*60, max_days_to_keep*24*60*60)))
                for _ in range(random.randint(1, 30))
            ]

            persistent_messages.extend(messages_for_this_guild)
            logging.info(f"Part 2 - Generated {len(messages_for_this_guild)} messages for guild {guild}")

        all_messages = persistent_messages + overdue_messages

        # Store the test messages
        messages_stored = 0
        for message in all_messages:
            store_message(message, override_checks=True)
            messages_stored += 1

            if messages_stored % 100 == 0:
                logging.info(f"Part 3 - Stored {messages_stored} messages (currently storing messages for guild {message.guild_id})")

        logging.info(f"Stored {messages_stored} messages in total.")
        logging.info(f"Persistent messages: {len(persistent_messages)}")

        # Run the cleanup
        logging.info("Running cleanup...")
        cleanup(max_days_to_keep=max_days_to_keep)
        logging.info("Cleanup complete.")

        # Check that the correct number of messages were deleted
        retrieved_messages = get_all_messages()

        logging.info(f"Retrieved {len(retrieved_messages)} messages from the database after cleanup.")
        
        # Turn them into a set to remove duplicates
        retrieved_messages_set = set(retrieved_messages)
        self.assertEqual(len(retrieved_messages), len(retrieved_messages_set), msg="Duplicate messages found in the database after cleanup.")

        all_messages_set = set(all_messages)
        self.assertEqual(len(all_messages), len(all_messages_set), msg="Duplicate messages found in the test data.")

        persistent_messages_set = set(persistent_messages)
        self.assertEqual(len(persistent_messages), len(persistent_messages_set), msg="Duplicate messages found in the retrieved data.")

        # Check that the correct number of messages were kept
        self.assertEqual(len(persistent_messages), len(retrieved_messages), msg="Incorrect number of messages found in the database after cleanup.")

        # Check that the correct number of messages were deleted
        self.assertEqual(retrieved_messages_set, persistent_messages_set, msg="Incorrect content of messages left in the database after cleanup.")

        # Delete all messages in the database to prepare for the next test
        db_manager.get_database().execute_query("DELETE FROM messages", commit=True)     

class TestServer(unittest.TestCase):
    INVALID_INT_TESTS = [(ValueError, -1), (TypeError, "abc"), (TypeError, None)]
    INVALID_FLOAT_TESTS = [(ValueError, -1), (TypeError, "abc"), (TypeError, None)]
    INVALID_BOOL_TESTS = [(TypeError, "abc"), (TypeError, None)]
    INVALID_CHANNEL_TESTS = [(TypeError, "abc")]
    
    def __init__(self, methodName:str = ...) -> None:
        super().__init__(methodName)
    
    def test_server_creation(self) -> None:
        """
        Tests the creation of a Server instance and its functionalities.

        :param self: The instance of the TestServer object.
        :type self: TestServer
        :return: None
        :rtype: None
        """
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        self.assertEqual(server.server_id, server_id)

        server.remove_all_data()

    def test_server_destruction(self) -> None:
        """
        Tests the destruction of a Server instance and its functionalities.

        :param self: The instance of the TestServer object.
        :type self: TestServer
        :return: None
        :rtype: None
        """
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)
        
        # Set some random data for the server
        server.profanity_moderation_profile.active = True
        server.profanity_moderation_profile.channel = 123456789
        server.profanity_moderation_profile.strike_system_active = True
        server.profanity_moderation_profile.max_strikes = 3

        server.spam_moderation_profile.active = True
        server.spam_moderation_profile.score_threshold = 100

        server.leveling_profile.active = True
        server.leveling_profile.channel = 123456789
        
        level_up_embed = server.leveling_profile.level_up_embed
        level_up_embed["title"] = "Changed Title"
        level_up_embed["description"] = "Changed Description"
        level_up_embed["color"] = 0x00FF00
        server.leveling_profile.level_up_embed = level_up_embed
        
        server.leveling_profile.points_lost_per_day = 0

        server.birthdays.add(member_id="123456789", birth_date="2023-01-01", real_name=None)
        server.birthdays.add(member_id="987654321", birth_date="2023-01-02", real_name="John Doe")

        default_roles:list = server.default_roles.default_roles
        default_roles.append("123456789")
        server.default_roles.default_roles = default_roles

        server.join_message_profile.active = True

        # Add some messages
        for _ in range(5):
            store_message(generate_test_message(guild_id=server_id), override_checks=True)

        server.remove_all_data()

        del server

        server = Server(server_id)

        self.assertEqual(server.profanity_moderation_profile.active, False)
        self.assertEqual(server.profanity_moderation_profile.channel, UNSET_VALUE)
        self.assertEqual(server.profanity_moderation_profile.strike_system_active, True)
        self.assertEqual(server.profanity_moderation_profile.max_strikes, 3)

        self.assertEqual(server.spam_moderation_profile.active, False)
        self.assertEqual(server.spam_moderation_profile.score_threshold, 100)

        self.assertEqual(server.leveling_profile.active, False)
        self.assertEqual(server.leveling_profile.channel, UNSET_VALUE)

        level_up_embed = server.leveling_profile.level_up_embed
        self.assertEqual(level_up_embed["title"], "Congratulations, @displayname!")
        self.assertEqual(level_up_embed["description"], "Congrats @mention! You reached level [level]!")
        self.assertEqual(level_up_embed["color"], "White")

        self.assertEqual(server.leveling_profile.points_lost_per_day, 0)

        self.assertEqual(len(server.birthdays), 0)

        self.assertEqual(len(server.default_roles.default_roles), 0)

        self.assertEqual(server.join_message_profile.active, False)

        self.assertEqual(get_all_messages(guild_id=server_id), [])


    def run_test_on_property(self, primary_server_instance, table_name, property_name: str, default_value, test_values, invalid_values) -> None:
        """
        Runs a test on a property of a Server instance.

        :param primary_server_instance: The primary server instance to test.
        :type primary_server_instance: Server
        :param table_name: The name of the table that the property is in.
        :type table_name: str
        :param property_name: The name of the property to test.
        :type property_name: str
        :param default_value: The default value of the property.
        :param test_values: A list of values to test the property with.
        :param invalid_values: A list of invalid values to test the property with. Should raise an error. (Optional)
        :return: None
        :rtype: None
        """
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

        # Check invalid values
        for invalid_value in invalid_values:
            with self.assertRaises(invalid_value[0], msg=f"Wrong or no error raised for invalid value \"{invalid_value[1]}\" for \"{property_name}\"."):
                set_property(primary_server_instance, table_name, property_name, invalid_value[1])

    class RunTestOnIntegratedListProperty:
        """Helper class to generate test data and perform tests on integrated list properties."""
        
        def __init__(self, server: 'Server', table_name: str, test_values: list, iterations: list, extra_keys_to_query: list = None) -> None:
            """
            Helper class to generate test data and perform tests on integrated list properties.

            :param server: The server instance to use.
            :type server: Server
            :param table_name: The name of the table to use.
            :type table_name: str
            :param test_values: A list of values to test.
            :type test_values: list
            :param iterations: A list containing the number of iterations to perform, and the number of rows to add per iteration.
            :type iterations: list
            :param extra_keys_to_query: A list of extra keys to query when creating a new server instance.
            :type extra_keys_to_query: list
            :return: None
            :rtype: None
            """
            self.server = server
            self.table_name = table_name
            self.test_values = test_values
            self.iterations = iterations # [iteration_count, rows_per_iteration]
            self.ektq = extra_keys_to_query if extra_keys_to_query is not None else []

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

        def generate_test_data_for_integrated_lists(self) -> list:
            """
            Generates the test data with consistent secondary keys across iterations.

            :return: A list containing test data for each iteration. Each iteration is represented 
                     by a list of dictionaries containing the test data for each row.
            :rtype: list
            """
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

        def run(self, test_case: unittest.TestCase) -> None:
            """
            Runs tests on the integrated list property for add, edit, and delete operations.
            
            :param test_case: The unittest.TestCase to run the tests on
            :type test_case: unittest.TestCase
            """
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

            # Test deletions using individual delete
            for test_entry in default_test_data:
                secondary_key_value = list(test_entry.values())[0]
                property.delete(secondary_key_value)

            # Verify all entries are deleted
            new_server_instance = Server(self.server.server_id)
            property = getattr(new_server_instance, self.table_name)
            test_case.assertEqual(len(property), 0)
            del new_server_instance

            logging.debug(f"Deleting entries in integrated list property \"{self.table_name}\" successful.")

            # Test delete_all_matching and delete_all
            # Re-add entries to test new deletion methods
            for test_entry in default_test_data:
                getattr(self.server, self.table_name).add(**test_entry)

            # Verify entries are re-added
            self._verify_entries(test_case, getattr(self.server, self.table_name), default_test_data)

            # Test delete_all_matching with a sample field and value
            if default_test_data:
                sample_entry = default_test_data[0]
                field_name = list(sample_entry.keys())[0]
                field_value = sample_entry[field_name]
                getattr(self.server, self.table_name).delete_all_matching(**{field_name: field_value})

                # Verify entries matching the field are deleted
                remaining_entries = [entry for entry in default_test_data if entry.get(field_name) != field_value]
                self._verify_entries(test_case, getattr(self.server, self.table_name), remaining_entries)

                # Test delete_all to remove remaining entries
                getattr(self.server, self.table_name).delete_all()

                # Verify all entries are deleted again
                new_server_instance = Server(self.server.server_id)
                property = getattr(new_server_instance, self.table_name)
                test_case.assertEqual(len(property), 0)
                del new_server_instance

            logging.debug(f"Tests for delete_all_matching and delete_all successful.")

            logging.info("Finished running tests on integrated list property: " + self.table_name)

        def _verify_entries(self, test_case: unittest.TestCase, property: db_manager.IntegratedList_TableManager, test_data: List[Dict[str, Any]]) -> None:
            """
            Helper function to verify that the entries match the expected data.

            :param test_case: The test case to assert upon.
            :type test_case: unittest.TestCase
            :param property: The property to verify data for.
            :type property: db_manager.IntegratedList_TableManager
            :param test_data: The test data to verify against.
            :type test_data: List[Dict[str, Any]]
            :return: None
            :rtype: None
            """
            for test_entry in test_data:
                secondary_key_value = list(test_entry.values())[0]
                for key, value in test_entry.items():
                    test_case.assertEqual(getattr(property[secondary_key_value], key), value)

        def _verify_data_in_new_server_instance(self, test_case: unittest.TestCase, server_id: int, test_data: List[Dict[str, Any]]) -> None:
            """
            Helper function to create a new server instance and verify data consistency.

            :param test_case: The test case to assert upon.
            :type test_case: unittest.TestCase
            :param server_id: The ID of the server to use.
            :type server_id: int
            :param test_data: The test data to verify against.
            :type test_data: List[Dict[str, Any]]
            :return: None
            :rtype: None
            """
            new_server_instance = Server(server_id)
            property = getattr(new_server_instance, self.table_name)

            for test_entry in test_data:
                secondary_key_value = list(test_entry.values())[0]
                data = property[secondary_key_value]
                for key, value in test_entry.items():
                    test_case.assertEqual(getattr(data, key), value)

            del new_server_instance

        def _generate_unique_value(self, existing_values, value_type) -> Any:
            """
            Generates a unique value based on the type and ensures it doesn't conflict.

            :param existing_values: A set of values that the generated value should not conflict with.
            :type existing_values: set
            :param value_type: The type of value to generate. Can be "str", "int", "bool", or "float".
            :type value_type: str
            :return: A unique value of the specified type that is not in existing_values.
            :rtype: Any
            """
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

        def _generate_valid_subset_for_ektq(self, X: int) -> List[int]:
            """
            Generates a random valid subset of X elements for constant keys.

            :param X: The maximum number of elements in the subset.
            :type X: int
            :return: A list of X elements, where each element is an integer between 0 and X (inclusive).
            :rtype: List[int]
            """
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
        self.run_test_on_property(server, "profanity_moderation_profile", "active", False, [True, False], self.INVALID_BOOL_TESTS)
        self.run_test_on_property(server, "profanity_moderation_profile", "channel", UNSET_VALUE, [1234567989, None, UNSET_VALUE], self.INVALID_CHANNEL_TESTS)
        self.run_test_on_property(server, "profanity_moderation_profile", "strike_system_active", True, [False, True], self.INVALID_BOOL_TESTS)
        self.run_test_on_property(server, "profanity_moderation_profile", "max_strikes", 3, [5, 0], self.INVALID_INT_TESTS)
        self.run_test_on_property(server, "profanity_moderation_profile", "strike_expiring_active", True, [False, True], self.INVALID_BOOL_TESTS)
        self.run_test_on_property(server, "profanity_moderation_profile", "strike_expire_days", 7, [10, 0], self.INVALID_INT_TESTS)
        self.run_test_on_property(server, "profanity_moderation_profile", "timeout_seconds", 3600, [7200, 0], self.INVALID_INT_TESTS)
        
        # For filtered words, there is a custom implementation where it defaults to the items stored in default_profane_words.txt
        # Need to get this list to compare with.
        profane_words = read_txt_to_list("default_profane_words.txt")
        self.run_test_on_property(server, "profanity_moderation_profile", "filtered_words", profane_words, [["hello", "world"], ["apple", "banana", "orange", "pineapple", "grape"], profane_words], 
                                  [(ValueError, ["apple", "grape", "apple", "orange"])])

        server.remove_all_data()

    def test_spam_moderation_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "spam_moderation_profile", "active", False, [True, False], self.INVALID_BOOL_TESTS)
        self.run_test_on_property(server, "spam_moderation_profile", "score_threshold", 100, [12, 1500, 0], self.INVALID_INT_TESTS)
        self.run_test_on_property(server, "spam_moderation_profile", "time_threshold_seconds", 60, [500, 0], self.INVALID_INT_TESTS)
        self.run_test_on_property(server, "spam_moderation_profile", "timeout_seconds", 60, [140, 0], self.INVALID_INT_TESTS)
        self.run_test_on_property(server, "spam_moderation_profile", "delete_invites", False, [True, False], self.INVALID_BOOL_TESTS)

        server.remove_all_data()

    def test_logging_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "logging_profile", "active", False, [True, False], self.INVALID_BOOL_TESTS)
        self.run_test_on_property(server, "logging_profile", "channel", UNSET_VALUE, [1234567989, UNSET_VALUE], self.INVALID_CHANNEL_TESTS + [(TypeError, None)])

        server.remove_all_data()

    def test_leveling_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "leveling_profile", "active", False, [True, False], self.INVALID_BOOL_TESTS)
        self.run_test_on_property(server, "leveling_profile", "channel", UNSET_VALUE, [1234567989, UNSET_VALUE, 0, None], self.INVALID_CHANNEL_TESTS)
        self.run_test_on_property(server, "leveling_profile", "level_up_embed[title]", "Congratulations, @displayname!", ["Title_Changed", None], [])
        self.run_test_on_property(server, "leveling_profile", "level_up_embed[description]", "Congrats @mention! You reached level [level]!", ["Description_Changed"], [])
        self.run_test_on_property(server, "leveling_profile", "level_up_embed[color]", "White", ["Red", "Orange", "Yellow", "Green", 0x00FF00, 0x0000FF], [])
        self.run_test_on_property(server, "leveling_profile", "points_lost_per_day", 0, [12, 0, 1], self.INVALID_INT_TESTS)
        self.run_test_on_property(server, "leveling_profile", "max_points_per_message", 40, [200, None, 0, 20, 500], [i for i in self.INVALID_INT_TESTS if i != (TypeError, None)]) # Allow None values
        self.run_test_on_property(server, "leveling_profile", "exempt_channels", [], [[1234567989, 256468532], [1234567989, 256468532, 494621612]], [(ValueError, [1234, 9876, 1234])]) # No duplicates
        self.run_test_on_property(server, "leveling_profile", "allow_leveling_cards", True, [False, True], self.INVALID_BOOL_TESTS)

        server.remove_all_data()

    def test_join_message_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "join_message_profile", "active", False, [True, False], self.INVALID_BOOL_TESTS)
        self.run_test_on_property(server, "join_message_profile", "channel", UNSET_VALUE, [1234567989, UNSET_VALUE], self.INVALID_CHANNEL_TESTS + [(TypeError, None)])
        self.run_test_on_property(server, "join_message_profile", "embed[title]", "@displayname just joined the server!", ["Title_Changed", None], [])
        self.run_test_on_property(server, "join_message_profile", "embed[description]", "Welcome to the server, @mention!", ["Description_Changed"], [])
        self.run_test_on_property(server, "join_message_profile", "embed[color]", "Blurple", ["Red", "Orange", "Yellow", "Green", 0x00FF00, 0x0000FF], [])
        self.run_test_on_property(server, "join_message_profile", "allow_join_cards", True, [False, True], self.INVALID_BOOL_TESTS)

        server.remove_all_data()

    def test_leave_message_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "leave_message_profile", "active", False, [True, False], self.INVALID_BOOL_TESTS)
        self.run_test_on_property(server, "leave_message_profile", "channel", UNSET_VALUE, [1234567989, UNSET_VALUE], self.INVALID_CHANNEL_TESTS + [(TypeError, None)])
        self.run_test_on_property(server, "leave_message_profile", "embed[title]", "@displayname just left the server.", ["Title_Changed", None], [])
        self.run_test_on_property(server, "leave_message_profile", "embed[description]", "@mention left.", ["Description_Changed"], [])
        self.run_test_on_property(server, "leave_message_profile", "embed[color]", "Blurple", ["Red", "Orange", "Yellow", "Green", 0x00FF00, 0x0000FF], [])

        server.remove_all_data()

    def test_birthdays_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "birthdays_profile", "channel", UNSET_VALUE, [1234567989, None, UNSET_VALUE], self.INVALID_CHANNEL_TESTS)
        self.run_test_on_property(server, "birthdays_profile", "embed[title]", "Happy Birthday, [realname]!", ["Title_Changed", None], [])
        self.run_test_on_property(server, "birthdays_profile", "embed[description]", "@mention just turned [age]!", ["Description_Changed"], [])
        self.run_test_on_property(server, "birthdays_profile", "embed[color]", "Gold", ["Red", "Orange", "Yellow", "Green", 0x00FF00, 0x0000FF], [])
        self.run_test_on_property(server, "birthdays_profile", "runtime", UNSET_VALUE, ["12:00 MDT", "8:00 PDT", "18:00 UTC", "0:00 EST", UNSET_VALUE], [(TypeError, None)])

        server.remove_all_data()

    def test_infinibot_settings_profile(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "infinibot_settings_profile", "get_updates", True, [False, True], self.INVALID_BOOL_TESTS)
        self.run_test_on_property(server, "infinibot_settings_profile", "timezone", UNSET_VALUE, [ZoneInfo("America/Los_Angeles").key, ZoneInfo("America/New_York").key, UNSET_VALUE], 
                                  [(TypeError, None)])

        server.remove_all_data()

    # SIMPLE LISTS
    def test_join_to_create_vcs(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "join_to_create_vcs", "channels", [], [[1234567989, 256468532], [1234567989, 256468532, 494621612]], 
                                  [(ValueError, [1234567989, 256468532, 1234567989])]) # No Duplicate values

        server.remove_all_data()

    def test_default_roles(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_property
        self.run_test_on_property(server, "default_roles", "default_roles", [], [[1234567989, 256468532], [1234567989, 256468532, 494621612]],
                                  [(ValueError, [1234567989, 256468532, 1234567989])]) # No Duplicate values

        server.remove_all_data()

    # INTEGRATED LISTS
    def test_moderation_strikes(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_integrated_list_property
        test = self.RunTestOnIntegratedListProperty(server, "moderation_strikes", ["member_id:int", "strikes:int", "last_strike:date"], [5, 20])
        test.run(self)

        server.remove_all_data()

    def test_member_levels(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_integrated_list_property
        test = self.RunTestOnIntegratedListProperty(server, "member_levels", ["member_id:int", "points:int"], [5, 20])
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

    def test_managed_messages(self):
        server_id = random.randint(0, 1000000000)

        server = Server(server_id)

        # Using run_test_on_integrated_list_property
        test = self.RunTestOnIntegratedListProperty(server, "managed_messages", ["message_id:int", "channel_id:int", "author_id:int", "message_type:str", "json_data:str"], [5, 20])
        test.run(self)

        server.remove_all_data()

class TestMember(unittest.TestCase):
    def __init__(self, methodName:str = ...) -> None:
        super().__init__(methodName)

    def test_member_creation(self) -> None:
        """
        Tests the creation of a Member instance.

        :return: None
        :rtype: None
        """
        logging.info("Testing Member...")

        member = Member(123456789)
        self.assertEqual(member.member_id, 123456789)

        member.remove_all_data()

    def run_test_on_property(self, primary_member_instance:Member, property_name:str, default_value, test_values) -> None:
        """
        Runs a test on a Member property.

        :param primary_member_instance: The primary Member instance to test
        :type primary_member_instance: Member
        :param property_name: The name of the property to test
        :type property_name: str
        :param default_value: The default value to test
        :param test_values: The test values to test
        :return: None
        :rtype: None
        """
        logging.debug(f'Testing property "{property_name}". Default value: {default_value}, test values: {test_values}')
        
        def get_property(member, property_name):
            """Fetches the property from Member, handling itemized properties."""
            split_property_name = property_name.split("[")
            if len(split_property_name) == 2:
                item_name = split_property_name[1][:-1]  # Remove trailing "]"
                return getattr(member, split_property_name[0])[item_name]
            return getattr(member, property_name)

        def set_property(member, property_name, value):
            """Sets the property with Member, handling itemized properties."""
            split_property_name = property_name.split("[")
            if len(split_property_name) == 2:
                item_name = split_property_name[1][:-1]  # Remove trailing "]"
                prop = getattr(member, split_property_name[0])
                prop[item_name] = value
                setattr(member, split_property_name[0], prop)
            else:
                setattr(member, property_name, value)

        # Check the default value
        self.assertEqual(get_property(primary_member_instance, property_name), default_value, msg=f"Default value for \"{property_name}\" is claimed to be \"{default_value}\", but is \"{get_property(primary_member_instance, property_name)}\".")

        # Ensure test_values is a list
        if not isinstance(test_values, list):
            test_values = [test_values]

        # Check each test value
        for test_value in test_values:
            set_property(primary_member_instance, property_name, test_value)
            self.assertEqual(get_property(primary_member_instance, property_name), test_value)

            # Create a new server instance and verify the property value is consistent
            new_member_instance = Member(primary_member_instance.member_id)
            self.assertEqual(get_property(new_member_instance, property_name), test_value)
            del new_member_instance

    def test_member_profile(self):
        member_id = random.randint(0, 1000000000)

        member = Member(member_id)

        # Using run_test_on_property
        self.run_test_on_property(member, "level_up_card_enabled", False, [True, False])
        self.run_test_on_property(member, "join_card_enabled", False, [True, False])
        self.run_test_on_property(member, "level_up_card_embed[title]", "Yum... Levels", ["Title_Changed", None])
        self.run_test_on_property(member, "level_up_card_embed[description]", "I am level [level]!", ["Description_Changed"])
        self.run_test_on_property(member, "level_up_card_embed[color]", "Purple", ["Red", "Green", "White", None, 0x00FF00, 0x0000FF])
        self.run_test_on_property(member, "join_card_embed[title]", "About Me", ["Title_Changed", None])
        self.run_test_on_property(member, "join_card_embed[description]", "I am human", ["Description_Changed"])
        self.run_test_on_property(member, "join_card_embed[color]", "Green", ["Red", "Purple", "White", None, 0x00FF00, 0x0000FF])
        self.run_test_on_property(member, "direct_messages_enabled", True, [False, True])

        member.remove_all_data()

class TestFileManager(unittest.TestCase):
    def test_json_file(self) -> None:
        """
        Tests the JSONFile class.

        :return: None
        :rtype: None
        """
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
    def test_global_kill_status(self) -> None:
        """
        Tests the GlobalKillStatus class.

        :return: None
        :rtype: None
        """
        logging.info("Testing GlobalKillStatus...")

        # Clear file
        get_global_kill_status().reset()

        self.assertFalse(get_global_kill_status()["moderation__profanity"]) # USES PROFANITY MODERATION AS A TEST

        get_global_kill_status()["moderation__profanity"] = True
        self.assertTrue(get_global_kill_status()["moderation__profanity"])

        self.assertRaises(AttributeError, get_global_kill_status().__getitem__, "fake_item")

        self.assertRaises(AttributeError, get_global_kill_status().__setitem__, "fake_item", True)

        logging.info("Finished testing GlobalKillStatus...")

class TestUtils(unittest.TestCase):
    def test_feature_is_active(self) -> None:
        """
        Tests the feature_is_active function.

        :param self: The unittest.TestCase to run the tests on
        :type self: unittest.TestCase
        :return: None
        :rtype: None
        """
        logging.info("Testing feature_is_active...")

        # Clear global kill status file to get consistent results
        get_global_kill_status().reset()

        # BEGIN TESTING 
        self.assertFalse(feature_is_active(server_id=1, feature="moderation__profanity"),
                        "Should have returned False as the feature is not globally killed, but the server has the feature disabled by default")

        # Test that if the server has the feature disabled, it will return False
        server = Server(random.randint(0, 1000000000))
        server.profanity_moderation_profile.active = True

        self.assertTrue(feature_is_active(server=server, feature="moderation__profanity"),
                         "Should have returned True as the feature is enabled in the server and is not globally killed")

        server.remove_all_data()

        # Test that if the feature is globally killed, it will return False regardless of the server's settings
        get_global_kill_status()["moderation__profanity"] = True

        self.assertFalse(feature_is_active(server_id=1, feature="moderation__profanity"),
                         "Should have returned False as the feature is globally killed")

        server = Server(random.randint(0, 1000000000))
        server.profanity_moderation_profile.active = True

        self.assertFalse(feature_is_active(server=server, feature="moderation__profanity"),
                         "Should have returned False as the feature is globally killed")
        
        server.remove_all_data()

        get_global_kill_status().reset()

        logging.info("Finished testing feature_is_active...")

    def test_required_permissions_validity(self) -> None:
        """
        Tests the required_permissions_validity function.

        :return: None
        :rtype: None
        """
        global required_permissions

        for _section_name, permissions in required_permissions.items():
            for _perm_name, backend_perm_dependencies in permissions.items():
                for backend_perm in backend_perm_dependencies:
                    # Ensure that it exists
                    if not hasattr(nextcord.Permissions, backend_perm):
                        self.fail(f"Required permission `{backend_perm}` does not exist in nextcord.Permissions")

class TestDailyDBMaintenance(unittest.TestCase):
    # Most of the processes conducted in daily_db_maintenance are previously tested.
    # Only the other, untested processes are tested here.
    def test_cleanup_orphaned_guild_entries(self) -> None:
        """
        Tests the cleanup_orphaned_guild_entries function.
        """
        logging.info("Testing cleanup_orphaned_guild_entries...")

        # Use test_db for testing
        database = Database("sqlite://", "resources/test_db_build.sql")

        # Generate thousands of random mock guild IDs
        all_guild_ids = set(random.sample(range(1, 999999999999999999), 5000))
        all_guild_ids = list(all_guild_ids)  # Convert to list for indexing

        # Split into valid and invalid guild IDs
        valid_guild_ids = all_guild_ids[:3000]
        invalid_guild_ids = all_guild_ids[3000:]

        # Generate a noisy list of guild IDs to simulate multiple existing entries in the database
        noisy_guild_ids = all_guild_ids.copy()
        for _ in range(10000):
            noisy_guild_ids.append(random.choice(noisy_guild_ids))

        random.shuffle(noisy_guild_ids)  # Shuffle to randomize the order

        # Generate mock entries in the database
        for index, guild_id in enumerate(noisy_guild_ids):
            bool_val = "true" if random.choice([True, False]) else "false"
            ch_status = random.choice(["SET", "UNSET"])
            if ch_status == "UNSET":
                ch_value = "null"
            else:
                ch_value = str(random.randint(100000, 999999))
            ch_json = f'{{"status": "{ch_status}", "value": {ch_value}}}'
            list_val = json.dumps([random.randint(0, 1000) for _ in range(random.randint(0, 5))])

            database.execute_query(
                f"INSERT INTO table_1 "
                f"(primary_key, example_bool, example_channel, example_integer, example_list) "
                f"VALUES ({index}, {bool_val}, '{ch_json}', {guild_id}, '{list_val}')",
                commit=True
            )

        # Call cleanup_orphaned_guild_entries
        db_manager.cleanup_orphaned_guild_entries(
            all_guild_ids=valid_guild_ids, # Slight name mismatch. Intentional.
            database=database
        )

        # Verify that only valid guild IDs are present in the database
        remaining_guild_ids = database.execute_query("SELECT example_integer FROM table_1", multiple_values=True)
        
        for id in remaining_guild_ids:
            self.assertIn(id[0], valid_guild_ids,
                          msg=f"Found orphaned guild ID {id[0]} in the database, which should have been cleaned up.")
            
        for id in valid_guild_ids:
            self.assertIn(id, [row[0] for row in remaining_guild_ids],
                          msg=f"Valid guild ID {id} is missing from the database after cleanup.")
            
        for id in invalid_guild_ids:
            self.assertNotIn(id, [row[0] for row in remaining_guild_ids],
                             msg=f"Invalid guild ID {id} should not be present in the database after cleanup.")

        # Cleanup
        database.execute_query("DELETE FROM table_1", commit=True)
        database.cleanup()

        logging.info("Finished testing cleanup_orphaned_guild_entries...")

def cleanup_environment():
    """
    Cleans up the environment after tests are run.
    """
    shutil.rmtree("./generated/test-files", ignore_errors=True)

    database = db_manager.get_database()
    if database: database.cleanup()

    logging.info("Cleaned up test environment.")

def create_environment():
    """
    Creates the environment required for InfiniBot to run in test mode.
    """
    logging.info("Creating environment...")

    # Clean up old environment
    cleanup_environment()

    def create_folder(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        logging.info(f"Created folder: {folder_path}")
    
    def copy_file(source_path, destination_path):
        if not os.path.exists(destination_path):
            shutil.copy(source_path, destination_path)
            logging.info(f"Copied file: {source_path} to {destination_path}")
 
    # Create directory structure
    create_folder("./generated")
    create_folder("./generated/test-files")
    create_folder("./generated/test-files/files")
    create_folder("./generated/test-files/backups")
    create_folder("./generated/test-files/configure")
    
    # Copy default files
    copy_file("./defaults/default_profane_words.txt", "./generated/test-files/configure/default_profane_words.txt")
    copy_file("./defaults/default_jokes.json", "./generated/test-files/files/jokes.json")

    # Remap base paths
    update_database_url()
    file_manager_update_base_path("./generated/test-files/configure/")
    log_manager_update_base_path("./generated/test-files/logs/")

    logging.info("Environment created successfully.")


def main(_iteration_number: int = 0) -> None:
    """
    Main function to run the tests.
    
    :return: None
    :rtype: None
    """

    print("RUNNING ---------------------------------------------------------------------------------------------------------")
    create_environment()

    setup_logging(logging.DEBUG)

    logging.info(f"{'#'*50} Running Tests {'#'*50}")

    # ===================================== <USE THIS FOR RUNNING SPECIFIC TESTS> =====================================
    # This will disable all other tests and only run the specified ones.
    specific_tests_to_run = [
        # TestUtils('example_test')

    ]
    # ===================================== </USE THIS FOR RUNNING SPECIFIC TESTS> ====================================

    # Run all tests if --run-all argument is provided
    if "--run-all" in sys.argv:
        logging.warning("Due to --run-all argument, overriding specific_tests_to_run to run all tests.")
        specific_tests_to_run = []

    # If no specific tests are provided, run all tests
    if not specific_tests_to_run:
        logging.info("Running all tests...")
        # Create test suite and runner
        test_suite = unittest.TestLoader().discover('tests')

        # Add monolithic tests
        test_suite.addTest(TestDatabase('entrypoint'))
        test_suite.addTest(TestStoredMessages('entrypoint'))

    else:
        logging.warning("Running only specified tests: " + ", ".join([test.id() for test in specific_tests_to_run]))
        test_suite = unittest.TestSuite()
        for test in specific_tests_to_run:
            test_suite.addTest(test)

    runner = unittest.TextTestRunner()
    test_result = runner.run(test_suite)

    cleanup_environment()

    if test_result.wasSuccessful():
        logging.info("All tests passed!")
    else:
        logging.warning("Tests failed")
    
    header = "Finished Tests"
    if test_result.wasSuccessful() and len(test_result.skipped) == 0:
        print(f"{'✅'*25} {header} {'✅'*25}")
    else:
        print(f"{'❌'*25} {header} {'❌'*25}")
    print(f"Tests run: {test_result.testsRun}")
    print(f"Failures: {len(test_result.failures)}")
    print(f"Errors: {len(test_result.errors)}")
    print(f"Skipped: {len(test_result.skipped)}")

    print('#'*(50 * 2 + 2 + len(header)))

    if test_result.wasSuccessful():
        exit(0)
    else:
        if "--retry-once-on-failure" in sys.argv and _iteration_number == 0:
            logging.warning("Retrying tests once due to --retry-once-on-failure argument.")
            # Retry the tests once
            main(_iteration_number=1)
        else:
            exit(1)

if __name__ == "__main__":
    main()