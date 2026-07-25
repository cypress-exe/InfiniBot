"""
Tests for :mod:`config.messages.stored_messages` — the on-disk message store
behind edit/delete logging.

The ``db`` fixture gives each test an empty database.
"""

from __future__ import annotations

import pytest

import core.db_manager as db_manager
from config.messages.stored_messages import (
    MessageRecord,
    cleanup_db,
    get_all_messages_from_db,
    get_message_from_db,
    remove_message_from_db,
    store_message_in_db,
)
from tests.support.factories import aged_message, make_message, next_id, random_content

pytestmark = pytest.mark.integration

# Discord's own message length limit — the largest content the store must handle.
MAX_DISCORD_MESSAGE_LENGTH = 4000


def store_all(messages) -> None:
    for message in messages:
        store_message_in_db(message, override_checks=True)


# --------------------------------------------------------------------------- #
# MessageRecord
# --------------------------------------------------------------------------- #


def test_message_record_keeps_the_fields_it_was_built_with() -> None:
    fields = {
        "message_id": next_id(),
        "guild_id": next_id(),
        "channel_id": next_id(),
        "author_id": next_id(),
        "content": "hello",
    }
    record = MessageRecord(**fields, last_updated=None)

    assert {key: getattr(record, key) for key in fields} == fields


# --------------------------------------------------------------------------- #
# Storing and retrieving
# --------------------------------------------------------------------------- #


def test_a_stored_message_reads_back_intact(db) -> None:
    message = make_message(content=random_content(MAX_DISCORD_MESSAGE_LENGTH))

    assert store_message_in_db(message, override_checks=True) is True

    stored = get_message_from_db(message.message_id)
    assert (
        stored.message_id,
        stored.guild_id,
        stored.channel_id,
        stored.author_id,
        stored.content,
    ) == (
        message.message_id,
        message.guild_id,
        message.channel_id,
        message.author_id,
        message.content,
    )


def test_storing_the_same_message_twice_is_idempotent(db) -> None:
    """Edits re-store an existing message ID; that must not raise or duplicate."""
    message = make_message()
    store_message_in_db(message, override_checks=True)

    assert store_message_in_db(message, override_checks=True) is True
    assert store_message_in_db(message, override_checks=True) is True
    assert len(get_all_messages_from_db()) == 1


def test_removing_a_message_deletes_its_row(db) -> None:
    message = make_message()
    store_message_in_db(message, override_checks=True)

    remove_message_from_db(message.message_id)

    rows = db_manager.get_database().execute_query(
        f"SELECT * FROM messages WHERE message_id = {message.message_id}",
        multiple_values=True,
    )
    assert rows == []


def test_get_all_messages_returns_every_stored_message(db) -> None:
    guild_ids = [next_id() for _ in range(17)]
    messages = [
        make_message(guild_id=guild_ids[index % len(guild_ids)]) for index in range(250)
    ]
    store_all(messages)

    assert set(get_all_messages_from_db()) == set(messages)


def test_get_all_messages_is_empty_once_every_message_is_removed(db) -> None:
    messages = [make_message() for _ in range(20)]
    store_all(messages)

    for message in messages:
        remove_message_from_db(message.message_id)

    assert get_all_messages_from_db() == []


def test_get_all_messages_can_be_filtered_by_guild(db) -> None:
    wanted_guild = next_id()
    wanted = [make_message(guild_id=wanted_guild) for _ in range(5)]
    store_all(wanted + [make_message() for _ in range(5)])

    assert set(get_all_messages_from_db(guild_id=wanted_guild)) == set(wanted)


# --------------------------------------------------------------------------- #
# cleanup_db — quantity based
# --------------------------------------------------------------------------- #

MAX_PER_GUILD = 30


@pytest.fixture
def quantity_capped_messages(db):
    """
    Fill three guilds past ``MAX_PER_GUILD`` and two guilds under it.

    Returns ``(expected_survivors, expected_deletions)``. Cleanup keeps the most
    recently stored ``MAX_PER_GUILD`` messages per guild, so the survivors are the
    *tail* of each over-filled guild's insertion order.
    """
    survivors: list = []
    deletions: list = []

    for overflow in (1, 2, 3):  # over-filled guilds
        guild_id = next_id()
        messages = [
            make_message(guild_id=guild_id) for _ in range(MAX_PER_GUILD + overflow)
        ]
        survivors.extend(messages[overflow:])
        deletions.extend(messages[:overflow])

    for count in (1, MAX_PER_GUILD - 1):  # under-filled guilds
        guild_id = next_id()
        survivors.extend(make_message(guild_id=guild_id) for _ in range(count))

    store_all(survivors + deletions)
    return survivors, deletions


def test_quantity_cleanup_keeps_exactly_the_cap_per_guild(
    db, quantity_capped_messages
) -> None:
    survivors, _ = quantity_capped_messages

    cleanup_db(max_messages_to_keep_per_guild=MAX_PER_GUILD)

    assert len(get_all_messages_from_db()) == len(survivors)


def test_quantity_cleanup_keeps_the_newest_messages(db, quantity_capped_messages) -> None:
    survivors, deletions = quantity_capped_messages

    cleanup_db(max_messages_to_keep_per_guild=MAX_PER_GUILD)

    remaining = set(get_all_messages_from_db())
    assert remaining == set(survivors)
    assert remaining.isdisjoint(deletions)


def test_quantity_cleanup_leaves_under_filled_guilds_alone(db) -> None:
    guild_id = next_id()
    messages = [make_message(guild_id=guild_id) for _ in range(MAX_PER_GUILD - 1)]
    store_all(messages)

    cleanup_db(max_messages_to_keep_per_guild=MAX_PER_GUILD)

    assert set(get_all_messages_from_db()) == set(messages)


# --------------------------------------------------------------------------- #
# cleanup_db — age based
# --------------------------------------------------------------------------- #

MAX_DAYS = 7


@pytest.fixture
def aged_messages(db):
    """
    Three guilds carrying a mix of overdue and recent messages, two carrying only
    recent ones. Returns ``(expected_survivors, expected_deletions)``.
    """
    survivors: list = []
    deletions: list = []

    for overdue_count in (1, 15, 30):
        guild_id = next_id()
        deletions.extend(
            aged_message(MAX_DAYS + 1 + index, guild_id=guild_id)
            for index in range(overdue_count)
        )
        survivors.extend(
            aged_message(1 + (index % (MAX_DAYS - 1)), guild_id=guild_id)
            for index in range(overdue_count)
        )

    for count in (5, 30):
        guild_id = next_id()
        survivors.extend(
            aged_message(1 + (index % (MAX_DAYS - 1)), guild_id=guild_id)
            for index in range(count)
        )

    store_all(survivors + deletions)
    return survivors, deletions


def test_age_cleanup_removes_messages_past_the_retention_window(db, aged_messages) -> None:
    survivors, deletions = aged_messages

    cleanup_db(max_days_to_keep=MAX_DAYS)

    remaining = set(get_all_messages_from_db())
    assert remaining.isdisjoint(deletions)


def test_age_cleanup_keeps_messages_inside_the_retention_window(db, aged_messages) -> None:
    survivors, _ = aged_messages

    cleanup_db(max_days_to_keep=MAX_DAYS)

    assert set(get_all_messages_from_db()) == set(survivors)


def test_age_cleanup_does_not_duplicate_rows(db, aged_messages) -> None:
    """A join gone wrong in cleanup would show up as duplicates rather than losses."""
    cleanup_db(max_days_to_keep=MAX_DAYS)

    remaining = get_all_messages_from_db()
    assert len(remaining) == len(set(remaining))
