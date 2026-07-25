"""
Tests for the generic :class:`modules.database.Database` machinery.

These run against the fixture schema in ``resources/test_db_build.sql`` — three
tables covering column defaults, table tags and a composite primary key — rather
than InfiniBot's real schema, so the expected values stay stable as the bot's
tables change.

The old harness ran all ten of these as ``stepN_*`` methods inside a single
``entrypoint`` test: the first failure aborted the rest, and the wrapper stringified
the exception, throwing away the traceback. They are ordinary tests now.
"""

from __future__ import annotations

import pytest

from modules.custom_types import UNSET_VALUE
from modules.database import Database

UNSET_CHANNEL_JSON = '{"status": "UNSET", "value": null}'


def insert_default_row(database: Database, table: str, row_id: int) -> None:
    """Insert a row into ``table`` with every non-key column at its schema default."""
    column_defaults = database.all_column_defaults[table]
    values = ", ".join(column_defaults.values())
    database.execute_query(
        f"INSERT OR IGNORE INTO {table} VALUES ({row_id}, {values})", commit=True
    )


# --------------------------------------------------------------------------- #
# Schema indexing
# --------------------------------------------------------------------------- #


def test_build_creates_every_table_in_the_schema(fixture_db: Database) -> None:
    assert len(fixture_db.tables) == 3


def test_table_tags_are_parsed_from_the_build_file(fixture_db: Database) -> None:
    assert fixture_db.tags == {
        "table_1": {"optimize": True, "remove-if-guild-invalid": "example_integer"},
        "table_3": {"optimize": True, "test-tag": "argument"},
    }


def test_column_defaults_are_indexed(fixture_db: Database) -> None:
    shared_defaults = {
        "example_bool": "false",
        "example_channel": f"'{UNSET_CHANNEL_JSON}'",
        "example_integer": "3",
        "example_list": "'[]'",
    }
    assert fixture_db.all_column_defaults == {
        "table_1": shared_defaults,
        "table_2": {"example_bool": "false"},
        "table_3": shared_defaults,
    }


def test_column_types_are_indexed(fixture_db: Database) -> None:
    shared_types = {
        "primary_key": "INT",
        "example_bool": "BOOLEAN",
        "example_channel": "TEXT",
        "example_integer": "INT",
        "example_list": "TEXT",
    }
    assert fixture_db.all_column_types == {
        "table_1": shared_types,
        "table_2": {
            "primary_key_1": "INT",
            "primary_key_2": "INT",
            "example_integer": "INT",
            "example_bool": "BOOLEAN",
        },
        "table_3": shared_types,
    }


def test_column_names_preserve_declaration_order(fixture_db: Database) -> None:
    shared_names = [
        "primary_key",
        "example_bool",
        "example_channel",
        "example_integer",
        "example_list",
    ]
    assert fixture_db.all_column_names == {
        "table_1": shared_names,
        "table_2": ["primary_key_1", "primary_key_2", "example_integer", "example_bool"],
        "table_3": shared_names,
    }


def test_primary_keys_are_indexed(fixture_db: Database) -> None:
    assert fixture_db.all_primary_keys == {
        "table_1": "primary_key",
        "table_2": "primary_key_1",
        "table_3": "primary_key",
    }


@pytest.mark.parametrize(
    ("table", "expected"),
    [("table_1", "primary_key"), ("table_2", "primary_key_1"), ("table_3", "primary_key")],
)
def test_get_id_sql_name_returns_the_primary_key(
    fixture_db: Database, table: str, expected: str
) -> None:
    """For a composite key, the *first* column is the ID."""
    assert fixture_db.get_id_sql_name(table) == expected


# --------------------------------------------------------------------------- #
# Queries
# --------------------------------------------------------------------------- #


def test_inserted_row_reads_back_with_schema_defaults(fixture_db: Database) -> None:
    insert_default_row(fixture_db, "table_1", 1234)

    result = fixture_db.execute_query("SELECT * FROM table_1", multiple_values=True)

    assert result == [(1234, 0, UNSET_CHANNEL_JSON, 3, "[]")]


def test_does_entry_exist_finds_a_present_row(fixture_db: Database) -> None:
    insert_default_row(fixture_db, "table_1", 123456789)

    assert fixture_db.does_entry_exist("table_1", 123456789) is True


def test_does_entry_exist_is_false_for_an_absent_row(fixture_db: Database) -> None:
    insert_default_row(fixture_db, "table_1", 123456789)

    assert fixture_db.does_entry_exist("table_1", 123456788) is False


def test_force_remove_entry_deletes_the_row(fixture_db: Database) -> None:
    insert_default_row(fixture_db, "table_1", 123456789)
    fixture_db.execute_query(
        "UPDATE table_1 SET example_integer = 12 WHERE primary_key = 123456789",
        commit=True,
    )

    fixture_db.force_remove_entry("table_1", 123456789)

    assert (
        fixture_db.execute_query(
            "SELECT * FROM table_1 WHERE primary_key = 123456789", multiple_values=True
        )
        == []
    )


# --------------------------------------------------------------------------- #
# get_column_default
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("table", "column", "expected"),
    [
        ("table_1", "example_bool", "false"),
        ("table_1", "example_channel", f"'{UNSET_CHANNEL_JSON}'"),
        ("table_1", "example_integer", "3"),
        ("table_1", "example_list", "'[]'"),
        ("table_1", "primary_key", UNSET_VALUE),
        ("table_2", "example_bool", "false"),
        ("table_2", "example_integer", UNSET_VALUE),
        ("table_2", "primary_key_1", UNSET_VALUE),
        ("table_2", "primary_key_2", UNSET_VALUE),
    ],
)
def test_get_column_default_unformatted_returns_the_raw_sql_literal(
    fixture_db: Database, table: str, column: str, expected
) -> None:
    assert fixture_db.get_column_default(table, column, format=False) == expected


@pytest.mark.parametrize(
    ("table", "column", "expected"),
    [
        ("table_1", "example_bool", False),
        ("table_1", "example_channel", UNSET_CHANNEL_JSON),
        ("table_1", "example_integer", 3),
        ("table_1", "example_list", "[]"),
        ("table_1", "primary_key", UNSET_VALUE),
        ("table_2", "example_bool", False),
        ("table_2", "example_integer", UNSET_VALUE),
        ("table_2", "primary_key_1", UNSET_VALUE),
        ("table_2", "primary_key_2", UNSET_VALUE),
    ],
)
def test_get_column_default_formatted_returns_a_python_value(
    fixture_db: Database, table: str, column: str, expected
) -> None:
    """Quotes stripped, ``false`` -> ``False``, ``3`` -> ``int``."""
    assert fixture_db.get_column_default(table, column, format=True) == expected


# --------------------------------------------------------------------------- #
# Unique entries and optimization
# --------------------------------------------------------------------------- #


def test_get_table_unique_entries_returns_every_primary_key(fixture_db: Database) -> None:
    ids = list(range(1000, 1020))
    for row_id in ids:
        insert_default_row(fixture_db, "table_1", row_id)

    assert sorted(fixture_db.get_table_unique_entries("table_1")) == ids


def test_get_unique_entries_for_database_unions_tables_without_duplicates(
    fixture_db: Database,
) -> None:
    shared = list(range(100_000, 100_020))
    only_table_1 = list(range(200_000, 200_010))
    only_table_3 = list(range(300_000, 300_010))

    for row_id in shared + only_table_1:
        insert_default_row(fixture_db, "table_1", row_id)
    for row_id in shared + only_table_3:
        insert_default_row(fixture_db, "table_3", row_id)

    entries = list(fixture_db.get_unique_entries_for_database())

    assert len(entries) == len(set(entries)), "IDs present in both tables were emitted twice"
    assert set(entries) == set(shared + only_table_1 + only_table_3)


def test_optimize_database_keeps_rows_that_differ_from_their_defaults(
    fixture_db: Database,
) -> None:
    """
    Optimization drops rows that carry nothing but defaults — they are
    indistinguishable from an absent row, and at InfiniBot's scale that is most
    of the table.
    """
    ids = list(range(1000, 1020))
    for row_id in ids:
        insert_default_row(fixture_db, "table_1", row_id)

    modified, untouched = ids[:3], ids[3:]
    for row_id in modified:
        fixture_db.execute_query(
            f"UPDATE table_1 SET example_bool = 'true' WHERE primary_key = {row_id}",
            commit=True,
        )

    fixture_db.optimize_database()

    remaining = [row[0] for row in fixture_db.execute_query(
        "SELECT * FROM table_1", multiple_values=True
    )]
    assert sorted(remaining) == modified


def test_optimize_database_drops_rows_left_at_their_defaults(fixture_db: Database) -> None:
    ids = list(range(1000, 1020))
    for row_id in ids:
        insert_default_row(fixture_db, "table_1", row_id)
    fixture_db.execute_query(
        f"UPDATE table_1 SET example_bool = 'true' WHERE primary_key = {ids[0]}",
        commit=True,
    )

    fixture_db.optimize_database()

    for row_id in ids[1:]:
        assert (
            fixture_db.execute_query(
                f"SELECT * FROM table_1 WHERE primary_key = {row_id}", multiple_values=True
            )
            == []
        )
