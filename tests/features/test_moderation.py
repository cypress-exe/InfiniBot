"""
Tests for :mod:`features.moderation` strike handling.

These are regressions from production incidents, so each one names the behavior
it protects rather than the function it calls.
"""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, Mock

import nextcord
import pytest

import features.moderation as moderation
from config.server import Server
from tests.support.factories import next_id


@pytest.fixture
def guild_id(db) -> int:
    server_id = next_id()
    server = Server(server_id)
    server.profanity_moderation_profile.strike_system_active = True
    server.profanity_moderation_profile.max_strikes = 3
    return server_id


@pytest.fixture
def bot(guild_id: int) -> Mock:
    """A bot whose guild lets InfiniBot time members out."""
    guild = Mock(spec=nextcord.Guild)
    guild.me.guild_permissions.moderate_members = True
    bot = Mock(spec=nextcord.Client)
    bot.get_guild = Mock(return_value=guild)
    return bot


@pytest.fixture
def member() -> Mock:
    member = Mock(spec=nextcord.Member)
    member.id = next_id()
    member.mention = "@Striker"
    # A stale snapshot, as message.author is: it never sees the timeout being applied
    member.communication_disabled_until = None
    return member


@pytest.fixture
def successful_timeout(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    timeout = AsyncMock(return_value="Success")
    monkeypatch.setattr(moderation.utils, "timeout", timeout)
    return timeout


async def test_a_strike_below_the_limit_is_not_reported_as_a_timeout(bot, guild_id, member, successful_timeout) -> None:
    result = await moderation.grant_and_punish_strike(bot, guild_id, member, 1)

    assert result == (True, False)
    assert Server(guild_id).moderation_strikes[member.id].strikes == 1
    successful_timeout.assert_not_awaited()


async def test_reaching_the_limit_reports_the_timeout(bot, guild_id, member, successful_timeout) -> None:
    """
    Regression for the prod KeyError:
        'Secondary key "..." not found in table.'

    The profanity DM decided "timed out vs. strike" from message.author's
    communication_disabled_until, which doesn't see the new timeout. It then looked
    up the strike row the timeout had just cleared. The strike call now reports the
    timeout itself.
    """
    Server(guild_id).moderation_strikes.add(member_id=member.id, strikes=2, last_strike=datetime.datetime.now(datetime.timezone.utc))

    result = await moderation.grant_and_punish_strike(bot, guild_id, member, 1)

    assert result == (True, True)
    assert member.id not in Server(guild_id).moderation_strikes
    successful_timeout.assert_awaited_once()


async def test_a_failed_timeout_is_not_reported_as_one(bot, guild_id, member, monkeypatch) -> None:
    monkeypatch.setattr(moderation.utils, "timeout", AsyncMock(return_value="Failure Forbidden"))
    monkeypatch.setattr(moderation.utils, "get_channel", AsyncMock(return_value=None))
    Server(guild_id).moderation_strikes.add(member_id=member.id, strikes=2, last_strike=datetime.datetime.now(datetime.timezone.utc))

    result = await moderation.grant_and_punish_strike(bot, guild_id, member, 1)

    assert result == (False, False)