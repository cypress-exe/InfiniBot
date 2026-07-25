"""
Tests for :mod:`core.db_manager`: pinned connections and orphan cleanup.

A pinned connection exists so that statements depending on per-connection state
(SQLite ``TEMPORARY`` tables) all land on the same physical connection, which
``Database.execute_query`` cannot promise — it checks out a pooled connection per
call. These use ``file_fixture_db`` rather than an in-memory database, because
every connection to ``sqlite://`` is a separate, empty database and the tests
below need two connections that see the same data.
"""

from __future__ import annotations

import json
import random

import pytest

import core.db_manager as db_manager
from modules.database import Database


@pytest.fixture
def warm_pool(file_fixture_db: Database):
    """
    Leave several distinct connections idle in the pool.

    Without this the pool holds a single connection, so a connection released
    mid-block is immediately handed back on the next statement and a
    release-on-commit bug stays invisible. QueuePool is FIFO by default
    (``use_lifo=False``), so with older idle connections queued ahead of it, a
    released connection is *not* the one returned next.
    """

    def _warm(count: int = 3) -> None:
        connections = [file_fixture_db.engine.connect() for _ in range(count)]
        for connection in connections:
            connection.close()

    return _warm


# --------------------------------------------------------------------------- #
# Pinned connections
# --------------------------------------------------------------------------- #


def test_temp_table_is_visible_to_later_queries(file_fixture_db: Database) -> None:
    """The whole point: a TEMP table stays visible to later statements on the pin."""
    with file_fixture_db.pinned_connection() as connection:
        connection.execute_query("CREATE TEMPORARY TABLE temp_ids (id INTEGER PRIMARY KEY)")
        connection.execute_query("INSERT INTO temp_ids (id) VALUES (1), (2), (3)", commit=True)

        assert connection.execute_query("SELECT COUNT(*) FROM temp_ids")[0] == 3

        connection.execute_query("DROP TABLE IF EXISTS temp_ids")


def test_temp_table_survives_a_commit(file_fixture_db: Database, warm_pool) -> None:
    """
    Regression for D1. A Session releases its connection back to the pool on
    commit, so a committing write would move later statements onto a different
    connection and lose the TEMP table.

    The warm pool is what makes this bite: with other connections queued ahead, a
    released connection is not the one handed back next — the real condition D1
    described, maintenance committing while other checkouts are live.
    """
    warm_pool()

    with file_fixture_db.pinned_connection() as connection:
        connection.execute_query("CREATE TEMPORARY TABLE temp_ids (id INTEGER PRIMARY KEY)")

        # Each commit is a chance for the connection to be swapped out from under us.
        for value in range(5):
            connection.execute_query(f"INSERT INTO temp_ids (id) VALUES ({value})", commit=True)
            assert connection.execute_query("SELECT COUNT(*) FROM temp_ids")[0] == value + 1

        connection.execute_query("DROP TABLE IF EXISTS temp_ids")


def test_temp_table_is_private_to_the_pinned_connection(
    file_fixture_db: Database, warm_pool
) -> None:
    """
    The failure D1 hinged on: statements that leak onto another pooled connection
    either don't see the table at all, or see a stale copy of it.
    """
    warm_pool()

    with file_fixture_db.pinned_connection() as connection:
        connection.execute_query("CREATE TEMPORARY TABLE temp_ids (id INTEGER PRIMARY KEY)")
        connection.execute_query("INSERT INTO temp_ids (id) VALUES (1)", commit=True)

        # The pin is still checked out, so this takes a different pooled
        # connection, which has no such table.
        with pytest.raises(Exception):
            file_fixture_db.execute_query("SELECT COUNT(*) FROM temp_ids")

        connection.execute_query("DROP TABLE IF EXISTS temp_ids")


def test_dropped_temp_table_does_not_outlive_the_block(file_fixture_db: Database) -> None:
    """Pooled connections are long-lived, so a dropped TEMP table must really be gone."""
    with file_fixture_db.pinned_connection() as connection:
        connection.execute_query("CREATE TEMPORARY TABLE temp_ids (id INTEGER PRIMARY KEY)")
        connection.execute_query("INSERT INTO temp_ids (id) VALUES (1)", commit=True)
        connection.execute_query("DROP TABLE IF EXISTS temp_ids")

    # Pinning again hands back the connection just released, so a leaked table
    # would still be there.
    with file_fixture_db.pinned_connection() as connection:
        with pytest.raises(Exception):
            connection.execute_query("SELECT COUNT(*) FROM temp_ids")


def test_pinned_writes_persist_to_the_real_database(file_fixture_db: Database) -> None:
    with file_fixture_db.pinned_connection() as connection:
        connection.execute_query(
            "INSERT INTO table_1 (primary_key, example_integer) VALUES (55, 777)", commit=True
        )

    result = file_fixture_db.execute_query(
        "SELECT example_integer FROM table_1 WHERE primary_key = 55"
    )
    assert result[0] == 777


def test_pinned_multiple_values_matches_execute_query(file_fixture_db: Database) -> None:
    file_fixture_db.execute_query(
        "INSERT INTO table_1 (primary_key, example_integer) VALUES (1, 10), (2, 20)", commit=True
    )
    query = "SELECT example_integer FROM table_1 ORDER BY primary_key"

    with file_fixture_db.pinned_connection() as connection:
        assert connection.execute_query(query, multiple_values=True) == (
            file_fixture_db.execute_query(query, multiple_values=True)
        )


def test_pinned_single_value_collapses_to_the_first_row(file_fixture_db: Database) -> None:
    file_fixture_db.execute_query(
        "INSERT INTO table_1 (primary_key, example_integer) VALUES (1, 10), (2, 20)", commit=True
    )
    query = "SELECT example_integer FROM table_1 ORDER BY primary_key"

    with file_fixture_db.pinned_connection() as connection:
        assert connection.execute_query(query) == file_fixture_db.execute_query(query)


def test_pinned_query_with_no_rows_returns_none(file_fixture_db: Database) -> None:
    with file_fixture_db.pinned_connection() as connection:
        assert (
            connection.execute_query(
                "SELECT example_integer FROM table_1 WHERE primary_key = 999"
            )
            is None
        )


def test_pinned_return_affected_rows_reports_the_write_count(
    file_fixture_db: Database,
) -> None:
    file_fixture_db.execute_query(
        "INSERT INTO table_1 (primary_key, example_integer) VALUES (1, 10), (2, 20)", commit=True
    )

    with file_fixture_db.pinned_connection() as connection:
        affected = connection.execute_query(
            "UPDATE table_1 SET example_integer = 99", commit=True, return_affected_rows=True
        )

    assert affected == 2


def test_a_failed_pinned_query_reraises_and_leaves_the_connection_usable(
    file_fixture_db: Database,
) -> None:
    """Callers depend on the original exception type, and the rollback must heal the pin."""
    with file_fixture_db.pinned_connection() as connection:
        with pytest.raises(Exception):
            connection.execute_query("SELECT * FROM a_table_that_does_not_exist")

        connection.execute_query(
            "INSERT INTO table_1 (primary_key, example_integer) VALUES (7, 70)", commit=True
        )
        result = connection.execute_query(
            "SELECT example_integer FROM table_1 WHERE primary_key = 7"
        )

    assert result[0] == 70


def test_the_connection_is_released_when_the_block_raises(file_fixture_db: Database) -> None:
    """Otherwise repeated failures would exhaust the pool."""

    class ExpectedError(Exception):
        pass

    for _ in range(10):  # more iterations than the pool size (5)
        with pytest.raises(ExpectedError):
            with file_fixture_db.pinned_connection() as connection:
                connection.execute_query("SELECT 1")
                raise ExpectedError()

    assert file_fixture_db.execute_query("SELECT 1")[0] == 1


# --------------------------------------------------------------------------- #
# cleanup_orphaned_guild_entries
# --------------------------------------------------------------------------- #


def test_orphan_cleanup_refuses_an_empty_guild_set(file_fixture_db: Database) -> None:
    """
    With no valid guilds every row looks orphaned. The cleanup must decline rather
    than empty the tables — this is the guard that stops a failed guild fetch from
    wiping the database.
    """
    file_fixture_db.execute_query(
        "INSERT INTO table_1 (primary_key, example_integer) VALUES (1, 111), (2, 222)",
        commit=True,
    )

    deleted = db_manager.cleanup_orphaned_guild_entries(set(), file_fixture_db)

    assert deleted == 0
    assert file_fixture_db.execute_query("SELECT COUNT(*) FROM table_1")[0] == 2


@pytest.fixture
def populated_guild_rows(fixture_db: Database):
    """
    Fill ``table_1`` with rows spread across 5000 guild IDs, many duplicated.

    The tag ``remove-if-guild-invalid: example_integer`` means the *guild* ID
    lives in ``example_integer``, not the primary key — hence rows keyed by index
    with the guild ID in a data column. Returns ``(valid_ids, invalid_ids)``.
    """
    rng = random.Random(20260725)  # fixed seed: failures reproduce
    all_guild_ids = rng.sample(range(1, 999999999999999999), 5000)
    valid_guild_ids, invalid_guild_ids = all_guild_ids[:3000], all_guild_ids[3000:]

    # Duplicate IDs so the cleanup has to handle repeats, not just a clean set.
    noisy = all_guild_ids + [rng.choice(all_guild_ids) for _ in range(10000)]
    rng.shuffle(noisy)

    for index, guild_id in enumerate(noisy):
        channel_status = rng.choice(["SET", "UNSET"])
        channel_value = "null" if channel_status == "UNSET" else str(rng.randint(100000, 999999))
        channel_json = f'{{"status": "{channel_status}", "value": {channel_value}}}'
        list_value = json.dumps([rng.randint(0, 1000) for _ in range(rng.randint(0, 5))])

        fixture_db.execute_query(
            "INSERT INTO table_1 "
            "(primary_key, example_bool, example_channel, example_integer, example_list) "
            f"VALUES ({index}, {str(rng.choice([True, False])).lower()}, "
            f"'{channel_json}', {guild_id}, '{list_value}')",
            commit=True,
        )

    return valid_guild_ids, invalid_guild_ids


@pytest.mark.slow
def test_orphan_cleanup_keeps_rows_for_valid_guilds(
    fixture_db: Database, populated_guild_rows
) -> None:
    valid_guild_ids, _ = populated_guild_rows

    db_manager.cleanup_orphaned_guild_entries(
        all_guild_ids=valid_guild_ids, database=fixture_db
    )

    remaining = {
        row[0]
        for row in fixture_db.execute_query(
            "SELECT example_integer FROM table_1", multiple_values=True
        )
    }
    assert set(valid_guild_ids) <= remaining


@pytest.mark.slow
def test_orphan_cleanup_removes_rows_for_departed_guilds(
    fixture_db: Database, populated_guild_rows
) -> None:
    valid_guild_ids, invalid_guild_ids = populated_guild_rows

    db_manager.cleanup_orphaned_guild_entries(
        all_guild_ids=valid_guild_ids, database=fixture_db
    )

    remaining = {
        row[0]
        for row in fixture_db.execute_query(
            "SELECT example_integer FROM table_1", multiple_values=True
        )
    }
    assert remaining.isdisjoint(invalid_guild_ids)
