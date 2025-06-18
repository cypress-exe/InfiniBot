import atexit
import logging
import os
import re
import time

from typing import Any, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

from components.utils import format_var_to_pythonic_type
from modules.custom_types import UNSET_VALUE


class DatabaseContextManager:
    def __enter__(self):
        # Setup or initialization if needed
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None:
            if issubclass(exc_type, Exception):
                logging.error("Uncaught exception in database: ", exc_info=(exc_type, exc_value, exc_traceback))
            else:
                logging.critical("Critical uncaught exception in database:", exc_info=(exc_type, exc_value, exc_traceback))

class Database:
    """
    A class for interacting with an SQLite database.

    Args:
        db_url (str): The URL of the SQLite database.
        db_build_file_path (str): Path to the instructions file.

    Attributes:
        engine: SQLAlchemy engine for database connection.
        Session: SQLAlchemy session class.
        tables (list): List of table names.
        all_column_defaults (dict): Dictionary mapping table names to column defaults.
        all_column_types (dict): Dictionary mapping table names to column types.
    """
    def __init__(self, db_url, db_build_file_path):
        """
        Initialize the database connection.

        Args:
            db_url (str): The URL of the SQLite database.
            db_build_file_path (str): Path to the instructions file.

        Returns:
            None
        """
        # Initialize the database connection
        self.engine = create_engine(db_url, pool_size = 5, poolclass = QueuePool) # create_engine runs a validity check on db_url
        self.Session = sessionmaker(bind=self.engine)
        self._dburl = db_url
        self.tables:list[str] = []
        self.tags:dict[str, any] = {}  # Dictionary to store tags for tables
        self.all_column_defaults:dict[str, dict[str, str]] = {}
        self.all_column_types:dict[str, dict[str, str]] = {}
        self.all_column_names:dict[str, list[str]] = {}
        self.all_primary_keys:dict[str, str] = {}

        self.execute_query("PRAGMA journal_mode=WAL;")

        self.build_database(db_build_file_path) # Database must be valid at initialization
        self.index_tables() # Index tables at runtime
        atexit.register(self.cleanup)  # Ensure cleanup at program exit

    def cleanup(self):
        """
        Dispose of the database engine and free resources.
        """
        if hasattr(self, "engine") and self.engine is not None:
            self.engine.dispose()
            self.engine = None  # Mark as disposed
            logging.info("Database engine disposed.")

    def __del__(self):
        self.cleanup()

    def get_db_url(self):
        return self._dburl

    def execute_query(self, sql: str, args: dict = {}, commit: bool = False, multiple_values: bool = False, return_affected_rows: bool = False, **kwargs):
        """
        Execute an SQL query and handle exceptions.

        Args:
            sql (str): The SQL query to execute.
            args (dict, optional): Query parameters.
            commit (bool, optional): Whether to commit changes to the database.
            multiple_values (bool, optional): Whether to return multiple query results.
            return_affected_rows (bool, optional): Whether to return the number of affected rows instead of query results.

        Returns:
            any: 
                return_affected_rows = True: Number of rows affected by INSERT/UPDATE/DELETE operations.
                multiple_values = False: Query result(s) simplified to a single value.
                multiple_values = True: All query results wrapped in a list.
        """
        # Use scoped_session if self.Session isn't already a scoped_session
        session_factory = scoped_session(self.Session) if not isinstance(self.Session, scoped_session) else self.Session

        with session_factory() as session:
            try:
                result = session.execute(text(sql), args)
                
                if return_affected_rows:
                    # For INSERT/UPDATE/DELETE operations, return the number of affected rows
                    affected_count = result.rowcount
                    if commit:
                        session.commit()
                    return affected_count
                else:
                    # For SELECT operations, return the query results
                    data = result.fetchall() if result.returns_rows else None
                    if commit:
                        session.commit()
                    return data if multiple_values else self.get_query_first_value(data)
                    
            except Exception as e:
                logging.error(f"Error executing SQL query: {sql}", exc_info=True)
                session.rollback()
                raise Exception(e)
    
    def build_database(self, build_file_path: str) -> None:
        """
        Build the database by applying instructions from a file.

        Args:
            build_file_path (str): Path to the build file.
        """
        build_file_path = os.path.abspath(build_file_path)
        logging.info(f"Building database from file: {build_file_path}")
        if not os.path.exists(build_file_path):
            raise FileNotFoundError("Database build file not found.")

        with open(build_file_path, 'r') as file:
            sql_instructions = file.read()

        # Split the SQL instructions into separate queries
        for instruction in re.split(r'\n\s*\n', sql_instructions.strip()):
            self.execute_query(instruction, commit=True)

    def index_tables(self) -> None:
        """
        Index all tables and their column defaults.
        """
        self.tables = [row[0] for row in self.execute_query("SELECT name FROM sqlite_master WHERE type='table'", multiple_values=True)]
        self.all_column_defaults = {}
        self.all_column_types = {}
        self.all_column_names = {}
        self.all_primary_keys = {}
        
        for table in self.tables:
            column_defaults = {}
            column_types = {}
            column_names = []
            primary_key = None
            table_info = self.execute_query(f"PRAGMA table_info({table})", multiple_values=True)
            table_schema = self.execute_query(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'",
                                               multiple_values=False)
            
            # Tags
            _tags = self._extract_tags_from_line(table_schema[0].split("\n")[0]) if table_schema else {}
            if _tags:
                self.tags[table] = _tags


            for col_info in table_info:
                column_names.append(col_info[1])
                if len(col_info) < 5: continue

                col_name, _type, _, default_value, primary_key_status = col_info[1:6]
                if default_value is not None:
                    column_defaults[col_name] = default_value
                column_types[col_name] = _type

                if primary_key_status == 1:
                    primary_key = col_name
            
            self.all_column_defaults[table] = column_defaults
            self.all_column_types[table] = column_types
            self.all_column_names[table] = column_names
            self.all_primary_keys[table] = primary_key

    def _extract_tags_from_line(self, line: str) -> dict[str, any]:
        """
        Extract tags from a line of SQL code, including tags with arguments.

        Args:
            line (str): A line of SQL code.

        Returns:
            dict(str, any): Dictionary of tags where keys are tag names and values are either True (for simple tags) or the argument string (for tags with arguments).
        """
        tags = {}
        if "--" in line:
            parts = line.split("--")
            for part in parts[1:]:
                if "#" in part:
                    tag_parts = [tag.strip() for tag in part.split("#") if tag.strip()]
                    for tag_part in tag_parts:
                        if "(" in tag_part and tag_part.endswith(")"):
                            # Tag with argument: extract tag name and argument
                            tag_name = tag_part[:tag_part.index("(")]
                            argument = tag_part[tag_part.index("(") + 1:-1]
                            tags[tag_name] = argument
                        else:
                            # Simple tag without argument
                            tags[tag_part] = True
        return tags

    def remove_extraneous_rows(self, table:str, skip_table_validation_check=False) -> None:
        """
        Check if a table has extraneous rows and remove them. (Will only run on tables marked as `#optimize`)

        Args:
            table (str): Table name.
            skip_table_validation_check (bool, optional): If true, skips validation checks ensuring that the table is marked as `#optimize`
        Returns:
            int: Number of rows deleted.
        """
        if not skip_table_validation_check:
            if table not in self.tags or 'optimize' not in self.tags[table]: return 0

        column_defaults = self.all_column_defaults[table]

        # Construct a SQL query to select entries matching the default state
        select_query = f"DELETE FROM {table} WHERE "
        for col_name, default_val in column_defaults.items():
            select_query += f"{col_name} = {default_val} AND "
        select_query = select_query.rstrip(" AND")  # Remove the trailing "AND"

        # Execute the query
        return self.execute_query(select_query, commit=True, return_affected_rows=True)

    def optimize_database(self, throttle: bool = False, throttle_delay: float = 0.1) -> None:
        """
        Synchronous database optimization with throttling and metrics
        - throttle: Enable delay between table optimizations
        - throttle_delay: Seconds to pause between tables (if throttling)

        Args:
            throttle (bool): Whether to enable throttling.
            throttle_delay (float): Delay in seconds between table optimizations.
        Returns:
            int: Total number of rows deleted during optimization.
        """
        tables_to_optimize = [table for table in self.tables if table in self.tags and 'optimize' in self.tags[table]]  

        start_time = time.monotonic()
        total_tables = len(tables_to_optimize)
        processed_tables = 0
        total_throttle_time = 0.0
        rows_deleted = 0

        logging.info(f"Starting database optimization ({total_tables} tables)")

        try:
            for table in tables_to_optimize:
                # Process table directly in main thread
                rows_deleted += self.remove_extraneous_rows(table)
                processed_tables += 1

                if throttle:
                    throttle_start = time.monotonic()
                    time.sleep(throttle_delay)  # Synchronous sleep
                    total_throttle_time += time.monotonic() - throttle_start

        except Exception as e:
            logging.error(f"Optimization failed: {e}")
            raise

        finally:
            total_duration = time.monotonic() - start_time
            avg_per_table = (total_duration - total_throttle_time) / processed_tables if processed_tables else 0

            logging.info(
                f"Database optimization completed\n"
                f"Tables processed: {processed_tables}/{total_tables}\n"
                f"Total duration: {total_duration:.2f}s\n"
                f"Active processing time: {total_duration - total_throttle_time:.2f}s\n"
                f"Throttle time: {total_throttle_time:.2f}s\n"
                f"Avg time per table: {avg_per_table:.2f}s"
            )

        return rows_deleted

    def force_remove_entry(self, table:str, id:int) -> None:
        """
        Force remove an entire entry from a table. BE VERY CAREFUL WITH THIS.

        Args:
            table (str): Table name.
            id (int): Entry ID.
        """
        id_sql_name = self.get_id_sql_name(table)
        self.execute_query(f"DELETE FROM {table} WHERE {id_sql_name} = :id", 
                           args={"id": id}, 
                           commit=True)
        
    def checkpoint(self):
        self.execute_query("PRAGMA wal_checkpoint(RESTART)", commit=True)
    
    def get_column_default(self, table:str, column_name:str, format=False) -> (bool | int | str | UNSET_VALUE | Any):
        """
        Get the default value of a column in a table.

        Args:
            table (str): Table name.
            column_name (str): Column name.
            format (bool, optional): Whether to format the default value into its correct Python type.

        Returns:
            any: Default value of the column. UNSET_VALUE if no default value is set.
        """
        try:
            column_defaults = self.all_column_defaults[table]
        except KeyError:
            raise KeyError(f"Table {table} not found in all_column_defaults.")
        
        try:
            default_value = column_defaults[column_name]
        except KeyError:
            return UNSET_VALUE
        
        if format:
            _type = self.get_column_type(table, column_name)
            default_value = format_var_to_pythonic_type(_type, default_value)

        return default_value
    
    def get_column_type(self, table:str, column_name:str) -> (str | UNSET_VALUE):
        """
        Get the data type of a column in a table.

        Args:
            table (str): Table name.
            column_name (str): Column name.
            skip_validation_checks (bool, optional): Whether to skip validation checks.

        Returns:
            str: Data type of the column. UNSET_VALUE if no default value is set.
        """
        try:  
            column_types = self.all_column_types[table]
        except KeyError:
            raise KeyError(f"Table {table} not found in all_column_types.")
        
        try:
            return column_types[column_name]
        except KeyError:
            return UNSET_VALUE
    
    def get_query_first_value(self, query_result:list[tuple]):
        """
        Cleans up query results to a single value or tuple.
        Should only be used on a raw query

        Args:
            query_result (list[tuple]): Raw query results.

        Returns:
            any: Simplified query result.
        """
        # Ensure that query_result is not None. If so, return None and stop.
        if query_result is None: return None
        
        if len(query_result) > 0: return query_result[0]
        return None

    def does_entry_exist(self, table:str, id: int) -> bool:
        """
        Check if an entry exists in the specified table.

        Args:
            table (str): Table name.
            id (int): Entry ID.

        Returns:
            bool: True if entry exists, False otherwise.
        """
        id_sql_name = self.get_id_sql_name(table)
        entry = self.execute_query(f"SELECT * FROM {table} WHERE {id_sql_name} = :id", 
                                   args={"id": id}, 
                                   multiple_values=True)
        return bool(entry)
    
    def get_table_unique_entries(self, table:str) -> Generator[int, int, int]:
        """
        Get all unique entries from a specific table.

        Yields:
            list[int] (Generator[int, int, int]): Generator yielding integer IDs.
        """
        id_sql_name = self.get_id_sql_name(table)
        ids = self.execute_query(f"SELECT DISTINCT {id_sql_name} FROM {table}", 
                                 multiple_values=True)
        for id_tuple in ids:
            id = id_tuple[0]
            yield id

    def get_unique_entries_for_database(self) -> list[int]:
        """
        Get all unique entries from all tables.
        This will include incomplete entries that do not exist in all tables.

        Returns:
            list[int]: List of integer IDs.
        """
        unique_ids = set()

        for table in self.tables:
            ids = self.get_table_unique_entries(table)
            unique_ids.update(ids)
        
        return list(unique_ids)
    
    def get_id_sql_name(self, table:str) -> str:
        """
        Get the SQL name of the primary key of a table.

        Args:
            table (str): Table name.

        Returns:
            str: SQL name of the primary key.
        """
        if table not in self.all_primary_keys:
            raise KeyError(f"Table {table} not found in all_primary_keys.")

        if self.all_primary_keys[table] == None:
            raise KeyError(f"Table {table} does not have a primary key.")

        return self.all_primary_keys[table]