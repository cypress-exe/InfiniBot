"""
Tests for :mod:`core.api_connections_manager`: the bot list posting loops.

Both loops exist in place of the ones their libraries shipped, which shared a
failure mode — a raised exception ended posting for the lifetime of the process
with nothing logged. discordlist.gg is posted to directly rather than through
BotBlock, which relays list tokens without the ``Bearer`` prefix discordlist.gg
requires and reports the resulting 401 inside an HTTP 200 body.
"""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, Mock

import aiohttp
import nextcord
import pytest
from nextcord.ext import commands

import core.api_connections_manager as api_connections_manager

TOKEN = "test-token"
BOT_ID = 991832387015159911


class FakeResponse:
    """An ``aiohttp`` response that carries nothing but its own status."""

    def __init__(self, status: int = 200):
        self.status = status

    async def __aenter__(self) -> FakeResponse:
        return self

    async def __aexit__(self, *_) -> bool:
        return False

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise aiohttp.ClientResponseError(
                request_info=None, history=(), status=self.status
            )


class FakeSession:
    """Captures the single ``post`` call the discordlist.gg update makes."""

    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls: list[dict] = []

    async def __aenter__(self) -> FakeSession:
        return self

    async def __aexit__(self, *_) -> bool:
        return False

    def post(self, url, *, json=None, headers=None) -> FakeResponse:
        self.calls.append({"url": url, "json": json, "headers": headers})
        return self.response


@pytest.fixture
def fake_session(monkeypatch: pytest.MonkeyPatch) -> FakeSession:
    """Replace ``aiohttp.ClientSession`` with a recorder returning 200."""
    session = FakeSession(FakeResponse(200))
    monkeypatch.setattr(
        api_connections_manager.aiohttp, "ClientSession", lambda: session
    )
    return session


def make_bot(guild_count: int, *, shard_count: int | None) -> Mock:
    """An ``AutoShardedBot`` holding ``guild_count`` guilds."""
    bot = Mock(spec=commands.AutoShardedBot)
    bot.shard_count = shard_count
    bot.guilds = [Mock(spec=nextcord.Guild) for _ in range(guild_count)]
    bot.user = Mock(id=BOT_ID)
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


class TestPostDiscordlistsStats:
    @pytest.mark.asyncio
    async def test_posts_count_with_a_bearer_token(self, fake_session: FakeSession):
        """
        The ``Bearer`` prefix is the whole reason this bypasses BotBlock — the
        same request without it returns 401 from discordlist.gg.
        """
        bot = make_bot(3908, shard_count=8)

        await api_connections_manager.post_discordlists_stats(bot, TOKEN)

        assert fake_session.calls == [
            {
                "url": f"https://api.discordlist.gg/v0/bots/{BOT_ID}/guilds",
                "json": {"count": 3908},
                "headers": {"Authorization": f"Bearer {TOKEN}"},
            }
        ]

    @pytest.mark.asyncio
    async def test_logs_what_it_posted(self, fake_session: FakeSession, caplog):
        bot = make_bot(3908, shard_count=8)

        with caplog.at_level(logging.INFO):
            await api_connections_manager.post_discordlists_stats(bot, TOKEN)

        assert "Posted 3908 guilds to discordlist.gg." in caplog.text

    @pytest.mark.asyncio
    async def test_raises_on_error_status(self, monkeypatch: pytest.MonkeyPatch):
        session = FakeSession(FakeResponse(401))
        monkeypatch.setattr(
            api_connections_manager.aiohttp, "ClientSession", lambda: session
        )
        bot = make_bot(3908, shard_count=8)

        with pytest.raises(aiohttp.ClientResponseError):
            await api_connections_manager.post_discordlists_stats(bot, TOKEN)


class TestPostLoops:
    """
    Both libraries' own loops died permanently on the first failure. These pin
    the replacement behaviour: log it, and be back in 30 minutes.
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("loop_name", "post_name", "interval_name", "message"),
        [
            (
                "run_topgg_post_loop",
                "post_topgg_stats",
                "TOPGG_POST_INTERVAL_SECONDS",
                "Failed to post stats to Top.gg: 401 Unauthorized",
            ),
            (
                "run_discordlists_post_loop",
                "post_discordlists_stats",
                "DISCORDLISTS_POST_INTERVAL_SECONDS",
                "Failed to post stats to discordlist.gg: 401 Unauthorized",
            ),
        ],
    )
    async def test_logs_and_keeps_running_after_a_failed_post(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog,
        loop_name: str,
        post_name: str,
        interval_name: str,
        message: str,
    ):
        bot = make_bot(1, shard_count=1)
        post_stats = AsyncMock(side_effect=[RuntimeError("401 Unauthorized"), None])
        monkeypatch.setattr(api_connections_manager, post_name, post_stats)
        # Two posts, then close the bot so the loop terminates.
        bot.is_closed.side_effect = [False, False, True]

        sleep_calls = []

        async def fake_sleep(seconds):
            sleep_calls.append(seconds)

        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        loop = getattr(api_connections_manager, loop_name)
        args = (bot,) if loop_name == "run_topgg_post_loop" else (bot, TOKEN)

        with caplog.at_level(logging.ERROR):
            await loop(*args)

        assert post_stats.await_count == 2
        assert sleep_calls == [getattr(api_connections_manager, interval_name)] * 2
        assert message in caplog.text

    @pytest.mark.asyncio
    async def test_topgg_does_not_post_when_bot_is_already_closed(self):
        bot = make_bot(1, shard_count=1)
        bot.is_closed.return_value = True

        await api_connections_manager.run_topgg_post_loop(bot)

        bot.topggpy.post_guild_count.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_discordlists_does_not_post_when_bot_is_already_closed(
        self, fake_session: FakeSession
    ):
        bot = make_bot(1, shard_count=1)
        bot.is_closed.return_value = True

        await api_connections_manager.run_discordlists_post_loop(bot, TOKEN)

        assert fake_session.calls == []
