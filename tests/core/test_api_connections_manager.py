"""
Tests for :mod:`core.api_connections_manager`: the Top.gg stats posting loop.

The loop exists in place of topggpy's built-in autopost, which dispatched
failures to an ``on_autopost_error`` event nothing listened for and killed its
own task outright on an unauthorized response — leaving the listing frozen with
no trace in the logs. These tests pin the logging and the recovery.
"""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, Mock

import nextcord
import pytest
from nextcord.ext import commands

import core.api_connections_manager as api_connections_manager


def make_bot(guild_count: int, *, shard_count: int | None) -> Mock:
    """An ``AutoShardedBot`` holding ``guild_count`` guilds."""
    bot = Mock(spec=commands.AutoShardedBot)
    bot.shard_count = shard_count
    bot.guilds = [Mock(spec=nextcord.Guild) for _ in range(guild_count)]
    bot.topggpy = Mock()
    bot.topggpy.post_guild_count = AsyncMock()
    return bot


class TestPostTopggStats:
    @pytest.mark.asyncio
    async def test_posts_guild_and_shard_counts(self):
        bot = make_bot(3908, shard_count=8)

        await api_connections_manager.post_topgg_stats(bot)

        bot.topggpy.post_guild_count.assert_awaited_once_with(
            guild_count=3908,
            shard_count=8,
        )

    @pytest.mark.asyncio
    async def test_logs_what_it_posted(self, caplog):
        """
        The counts posted have to be visible somewhere: Top.gg exposes no read
        endpoint for shards, so the log is the only record of what was sent.
        """
        bot = make_bot(3908, shard_count=8)

        with caplog.at_level(logging.INFO):
            await api_connections_manager.post_topgg_stats(bot)

        assert "Posted 3908 guilds across 8 shards to Top.gg." in caplog.text

    @pytest.mark.asyncio
    async def test_posts_when_unsharded(self):
        """topggpy drops a falsy shard count from the payload on its own."""
        bot = make_bot(12, shard_count=None)

        await api_connections_manager.post_topgg_stats(bot)

        bot.topggpy.post_guild_count.assert_awaited_once_with(
            guild_count=12,
            shard_count=None,
        )


class TestRunTopggPostLoop:
    @pytest.mark.asyncio
    async def test_logs_and_keeps_running_after_a_failed_post(
        self, monkeypatch: pytest.MonkeyPatch, caplog
    ):
        """
        topggpy's autopost re-raised on an unauthorized response, killing the
        loop for the process's lifetime. A rejected token must instead recover
        on the next cycle.
        """
        bot = make_bot(1, shard_count=1)
        bot.topggpy.post_guild_count.side_effect = [
            RuntimeError("401 Unauthorized"),
            None,
        ]
        # Two posts, then close the bot so the loop terminates.
        bot.is_closed.side_effect = [False, False, True]

        sleep_calls = []

        async def fake_sleep(seconds):
            sleep_calls.append(seconds)

        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        with caplog.at_level(logging.ERROR):
            await api_connections_manager.run_topgg_post_loop(bot)

        assert bot.topggpy.post_guild_count.await_count == 2
        assert sleep_calls == [api_connections_manager.TOPGG_POST_INTERVAL_SECONDS] * 2
        assert "Failed to post stats to Top.gg: 401 Unauthorized" in caplog.text

    @pytest.mark.asyncio
    async def test_does_not_post_when_bot_is_already_closed(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        bot = make_bot(1, shard_count=1)
        bot.is_closed.return_value = True

        await api_connections_manager.run_topgg_post_loop(bot)

        bot.topggpy.post_guild_count.assert_not_awaited()
