"""
Tests for :mod:`config.messages.cached_messages` — the in-memory, per-channel
message cache that serves edit/delete logging without hitting the database.

The cache is a module global, so the autouse fixture below clears it between
tests. The old harness cleared it only once, before its seven steps ran.
"""

from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo

import pytest

from config.messages.cached_messages import (
    _MAX_CACHE_SIZE,
    cache_message,
    clear_all_cached_messages,
    get_all_cached_messages,
    get_cache_stats,
    get_cached_message,
    get_cached_messages_from_channel,
    remove_cached_message,
    remove_cached_messages_from_channel,
    remove_cached_messages_from_guild,
)
from tests.support.factories import make_message, next_id


@pytest.fixture(autouse=True)
def empty_cache():
    """The cache is process-global; start and finish every test with it empty."""
    clear_all_cached_messages()
    yield
    clear_all_cached_messages()


# --------------------------------------------------------------------------- #
# Caching and retrieval
# --------------------------------------------------------------------------- #


def test_a_cached_message_reads_back_intact() -> None:
    message = make_message()

    assert cache_message(message, override_checks=True) is True

    cached = get_cached_message(message.message_id, message.channel_id)
    assert cached is not None
    assert (cached.message_id, cached.channel_id, cached.guild_id, cached.author_id, cached.content) == (
        message.message_id,
        message.channel_id,
        message.guild_id,
        message.author_id,
        message.content,
    )


def test_an_uncached_message_reads_back_as_none() -> None:
    assert get_cached_message(next_id(), next_id()) is None


def test_recaching_a_message_updates_its_content() -> None:
    """Message edits re-cache the same ID; the new content must win."""
    message = make_message()
    cache_message(message, override_checks=True)

    message.content = "Updated content"
    message.last_updated = datetime.datetime.now(ZoneInfo("UTC"))
    assert cache_message(message, override_checks=True) is True

    cached = get_cached_message(message.message_id, message.channel_id)
    assert cached.content == "Updated content"


# --------------------------------------------------------------------------- #
# FIFO eviction
# --------------------------------------------------------------------------- #


def test_a_channel_never_holds_more_than_the_cache_limit() -> None:
    channel_id = next_id()
    for _ in range(_MAX_CACHE_SIZE + 5):
        cache_message(make_message(channel_id=channel_id), override_checks=True)

    assert len(get_cached_messages_from_channel(channel_id)) == _MAX_CACHE_SIZE


def test_eviction_keeps_the_newest_messages() -> None:
    channel_id = next_id()
    messages = [make_message(channel_id=channel_id) for _ in range(_MAX_CACHE_SIZE + 5)]
    for message in messages:
        cache_message(message, override_checks=True)

    cached_ids = {message.message_id for message in get_cached_messages_from_channel(channel_id)}
    assert cached_ids == {message.message_id for message in messages[-_MAX_CACHE_SIZE:]}


def test_eviction_drops_the_oldest_messages() -> None:
    channel_id = next_id()
    messages = [make_message(channel_id=channel_id) for _ in range(_MAX_CACHE_SIZE + 5)]
    for message in messages:
        cache_message(message, override_checks=True)

    for evicted in messages[:5]:
        assert get_cached_message(evicted.message_id, channel_id) is None


def test_eviction_is_per_channel_not_global() -> None:
    """A busy channel must not evict a quiet channel's messages."""
    busy_channel, quiet_channel = next_id(), next_id()
    quiet_message = make_message(channel_id=quiet_channel)
    cache_message(quiet_message, override_checks=True)

    for _ in range(_MAX_CACHE_SIZE + 5):
        cache_message(make_message(channel_id=busy_channel), override_checks=True)

    assert get_cached_message(quiet_message.message_id, quiet_channel) is not None


# --------------------------------------------------------------------------- #
# Removal
# --------------------------------------------------------------------------- #


def test_removing_a_cached_message_reports_success_and_evicts_it() -> None:
    message = make_message()
    cache_message(message, override_checks=True)

    assert remove_cached_message(message.message_id, message.channel_id) is True
    assert get_cached_message(message.message_id, message.channel_id) is None


def test_removing_an_absent_message_reports_failure() -> None:
    message = make_message()
    cache_message(message, override_checks=True)
    remove_cached_message(message.message_id, message.channel_id)

    assert remove_cached_message(message.message_id, message.channel_id) is False


def test_removing_a_channel_clears_all_of_its_messages() -> None:
    channel_id = next_id()
    for _ in range(5):
        cache_message(make_message(channel_id=channel_id), override_checks=True)

    assert remove_cached_messages_from_channel(channel_id) == 5
    assert get_cached_messages_from_channel(channel_id) == []


def test_removing_a_guild_clears_every_channel_it_owns() -> None:
    guild_id = next_id()
    for _ in range(3):
        channel_id = next_id()
        for _ in range(3):
            cache_message(
                make_message(guild_id=guild_id, channel_id=channel_id), override_checks=True
            )

    assert remove_cached_messages_from_guild(guild_id) == 9
    assert count_messages_for_guild(guild_id) == 0


def test_removing_a_guild_leaves_other_guilds_alone() -> None:
    departing_guild, staying_guild = next_id(), next_id()
    cache_message(make_message(guild_id=departing_guild), override_checks=True)
    cache_message(make_message(guild_id=staying_guild), override_checks=True)

    remove_cached_messages_from_guild(departing_guild)

    assert count_messages_for_guild(staying_guild) == 1


def count_messages_for_guild(guild_id: int) -> int:
    return sum(
        len([message for message in channel_messages if message.guild_id == guild_id])
        for channel_messages in get_all_cached_messages().values()
    )


# --------------------------------------------------------------------------- #
# Stats
# --------------------------------------------------------------------------- #


def test_stats_report_an_empty_cache() -> None:
    stats = get_cache_stats()

    assert stats["total_messages"] == 0
    assert stats["total_channels"] == 0


def test_stats_report_the_per_channel_cap() -> None:
    assert get_cache_stats()["max_cache_size_per_channel"] == _MAX_CACHE_SIZE


def test_stats_count_messages_and_channels() -> None:
    channel_1, channel_2 = next_id(), next_id()
    for _ in range(5):
        cache_message(make_message(channel_id=channel_1), override_checks=True)
        cache_message(make_message(channel_id=channel_2), override_checks=True)

    stats = get_cache_stats()

    assert stats["total_messages"] == 10
    assert stats["total_channels"] == 2


def test_stats_break_down_message_counts_by_channel() -> None:
    channel_1, channel_2 = next_id(), next_id()
    for _ in range(5):
        cache_message(make_message(channel_id=channel_1), override_checks=True)
        cache_message(make_message(channel_id=channel_2), override_checks=True)

    counts = get_cache_stats()["channel_message_counts"]

    assert counts[channel_1] == 5
    assert counts[channel_2] == 5
