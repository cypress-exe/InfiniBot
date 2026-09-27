"""
Tests for :func:`core.bot.on_raw_message_edit`'s REST usage.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import nextcord
import pytest

import core.bot as bot_module
from config.server import Server
from tests.support.factories import next_id


# Regressions for the prod 404 flood: every edit in every guild fetched the
# edited message, and its author when that wasn't a cached Member — >16k
# message 404s and >26k member 404s, mostly webhook authors.

@pytest.fixture
def handlers(monkeypatch: pytest.MonkeyPatch) -> dict[str, Mock]:
    """Stub every collaborator so only the handler's own decisions are exercised."""
    mocks = {
        "get_channel": AsyncMock(),
        "get_message": AsyncMock(),
        "get_member": AsyncMock(return_value=None),
        "profanity": AsyncMock(),
        "edit_log": AsyncMock(),
    }
    monkeypatch.setattr(bot_module.utils, "get_channel", mocks["get_channel"])
    monkeypatch.setattr(bot_module.utils, "get_message", mocks["get_message"])
    monkeypatch.setattr(bot_module.utils, "get_member", mocks["get_member"])
    monkeypatch.setattr(bot_module.moderation, "check_and_trigger_profanity_moderation_for_message", mocks["profanity"])
    monkeypatch.setattr(bot_module.action_logging, "log_raw_message_edit", mocks["edit_log"])
    monkeypatch.setattr(bot_module.cached_messages, "cache_message", Mock())
    monkeypatch.setattr(bot_module.stored_messages, "get_message_from_db", Mock(return_value=None))
    monkeypatch.setattr(bot_module.stored_messages, "store_message_in_db", Mock())
    return mocks


def edit_payload(guild_id: int) -> Mock:
    payload = Mock(spec=nextcord.RawMessageUpdateEvent)
    payload.guild_id = guild_id
    payload.channel_id = next_id()
    payload.message_id = next_id()
    payload.cached_message = None
    return payload


async def test_edits_in_guilds_without_edit_features_make_no_rest_calls(db, handlers) -> None:
    guild_id = next_id()
    Server(guild_id)  # All features off by default

    await bot_module.on_raw_message_edit(edit_payload(guild_id))

    handlers["get_channel"].assert_not_awaited()
    handlers["get_message"].assert_not_awaited()
    handlers["get_member"].assert_not_awaited()


@pytest.mark.parametrize("profile", ["logging_profile", "profanity_moderation_profile", "spam_moderation_profile", "leveling_profile"])
async def test_edits_are_still_processed_when_any_edit_feature_is_on(db, handlers, profile) -> None:
    guild_id = next_id()
    getattr(Server(guild_id), profile).active = True
    handlers["get_channel"].return_value = None  # Stop right after the gate

    await bot_module.on_raw_message_edit(edit_payload(guild_id))

    handlers["get_channel"].assert_awaited_once()


async def test_webhook_authors_are_not_fetched_as_members(db, handlers) -> None:
    guild_id = next_id()
    Server(guild_id).logging_profile.active = True
    channel = Mock(spec=nextcord.TextChannel)
    channel.guild = Mock(spec=nextcord.Guild)
    channel.guild.id = guild_id
    handlers["get_channel"].return_value = channel
    message = Mock(spec=nextcord.Message)
    message.author = Mock(spec=nextcord.User)
    message.author.id = next_id()
    message.webhook_id = message.author.id
    handlers["get_message"].return_value = message

    await bot_module.on_raw_message_edit(edit_payload(guild_id))

    handlers["get_member"].assert_not_awaited()
    handlers["edit_log"].assert_awaited_once()


async def test_uncached_member_authors_are_still_resolved(db, handlers) -> None:
    guild_id = next_id()
    Server(guild_id).logging_profile.active = True
    channel = Mock(spec=nextcord.TextChannel)
    channel.guild = Mock(spec=nextcord.Guild)
    channel.guild.id = guild_id
    handlers["get_channel"].return_value = channel
    message = Mock(spec=nextcord.Message)
    message.author = Mock(spec=nextcord.User)
    message.author.id = next_id()
    message.webhook_id = None
    handlers["get_message"].return_value = message

    await bot_module.on_raw_message_edit(edit_payload(guild_id))

    handlers["get_member"].assert_awaited_once_with(channel.guild, message.author.id)
