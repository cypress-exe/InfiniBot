"""
Tests for :mod:`core.api_connections_manager`: the bot list posting loops.
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
from core.api_connections_manager import (
    BotListConnection,
    DiscordListConnection,
    TopGGConnection,
)

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
    """Captures the requests a connection makes."""

    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls: list[dict] = []

    async def __aenter__(self) -> FakeSession:
        return self

    async def __aexit__(self, *_) -> bool:
        return False

    def request(self, method, url, *, json=None, headers=None) -> FakeResponse:
        self.calls.append(
            {"method": method, "url": url, "json": json, "headers": headers}
        )
        return self.response


@pytest.fixture
def fake_session(monkeypatch: pytest.MonkeyPatch) -> FakeSession:
    """Replace ``aiohttp.ClientSession`` with a recorder returning 200."""
    session = FakeSession(FakeResponse(200))
    monkeypatch.setattr(
        api_connections_manager.aiohttp, "ClientSession", lambda: session
    )
    return session


def make_bot(guild_count: int, *, shard_count: int | None = 8) -> Mock:
    """
    An ``AutoShardedBot`` holding ``guild_count`` guilds.

    ``loop`` is attached by hand: nextcord sets it at runtime rather than on the
    class, so ``spec=`` alone would reject it. Scheduled coroutines are closed
    instead of run, keeping "never awaited" warnings out of the suite.
    """
    bot = Mock(spec=commands.AutoShardedBot)
    bot.shard_count = shard_count
    bot.guilds = [Mock(spec=nextcord.Guild) for _ in range(guild_count)]
    bot.user = Mock(id=BOT_ID)

    task = Mock(name="task")

    def create_task(coro):
        coro.close()
        return task

    bot.loop = Mock()
    bot.loop.create_task = Mock(side_effect=create_task)
    bot.loop.task_sentinel = task
    return bot


class StubConnection(BotListConnection):
    """A connection whose request is inert, for exercising the base class."""

    name = "Stub List"
    post_interval_seconds = 60

    def build_request(self):
        return "POST", "https://example.invalid/stats", {"count": self.server_count}, {}


class TestConnectionSetup:
    def test_rejects_an_empty_token(self):
        with pytest.raises(ValueError, match="Stub List"):
            StubConnection(make_bot(1), "")

    def test_start_holds_a_reference_to_its_task(self):
        """
        asyncio keeps only a weak reference to a running task, so a loop whose
        task is dropped can be garbage collected mid-flight.
        """
        bot = make_bot(1)
        connection = StubConnection(bot, TOKEN)

        connection.start()

        bot.loop.create_task.assert_called_once()
        assert connection.task is bot.loop.task_sentinel


class TestTopGGConnection:
    def test_posts_server_and_shard_counts_to_v1(self):
        """
        v1 rather than v0: v0 discards the shard count, reading back as null.
        """
        connection = TopGGConnection(make_bot(3908, shard_count=8), TOKEN)

        method, url, payload, headers = connection.build_request()

        assert method == "PATCH"
        assert url == "https://top.gg/api/v1/projects/@me/metrics"
        assert payload == {"server_count": 3908, "shard_count": 8}
        assert headers == {"Authorization": f"Bearer {TOKEN}"}

    def test_omits_shard_count_when_unsharded(self):
        """Top.gg validates the payload, so a null is not the same as absent."""
        connection = TopGGConnection(make_bot(12, shard_count=None), TOKEN)

        _, _, payload, _ = connection.build_request()

        assert payload == {"server_count": 12}

    @pytest.mark.asyncio
    async def test_logs_both_counts(self, fake_session: FakeSession, caplog):
        connection = TopGGConnection(make_bot(3908, shard_count=8), TOKEN)

        with caplog.at_level(logging.INFO):
            await connection.post_stats()

        assert "Posted 3908 guilds across 8 shards to Top.gg." in caplog.text


class TestDiscordListConnection:
    def test_posts_count_with_a_bearer_token(self):
        """
        The ``Bearer`` prefix is why this no longer goes through BotBlock — the
        same request without it returns 401 from discordlist.gg.
        """
        connection = DiscordListConnection(make_bot(3908), TOKEN)

        method, url, payload, headers = connection.build_request()

        assert method == "POST"
        assert url == f"https://api.discordlist.gg/v0/bots/{BOT_ID}/guilds"
        assert payload == {"count": 3908}
        assert headers == {"Authorization": f"Bearer {TOKEN}"}

    @pytest.mark.asyncio
    async def test_logs_the_count(self, fake_session: FakeSession, caplog):
        connection = DiscordListConnection(make_bot(3908), TOKEN)

        with caplog.at_level(logging.INFO):
            await connection.post_stats()

        assert "Posted 3908 guilds to discordlist.gg." in caplog.text


class TestPostStats:
    @pytest.mark.asyncio
    async def test_sends_the_request_the_subclass_describes(
        self, fake_session: FakeSession
    ):
        connection = StubConnection(make_bot(7), TOKEN)

        await connection.post_stats()

        assert fake_session.calls == [
            {
                "method": "POST",
                "url": "https://example.invalid/stats",
                "json": {"count": 7},
                "headers": {},
            }
        ]

    @pytest.mark.asyncio
    async def test_raises_on_error_status(self, monkeypatch: pytest.MonkeyPatch):
        session = FakeSession(FakeResponse(401))
        monkeypatch.setattr(
            api_connections_manager.aiohttp, "ClientSession", lambda: session
        )
        connection = StubConnection(make_bot(1), TOKEN)

        with pytest.raises(aiohttp.ClientResponseError):
            await connection.post_stats()


class TestRunPostLoop:
    @pytest.mark.asyncio
    async def test_logs_and_keeps_running_after_a_failed_post(
        self, monkeypatch: pytest.MonkeyPatch, caplog
    ):
        """
        Both replaced libraries stopped posting for the lifetime of the process
        after one failure. A rejected token must recover on the next cycle.
        """
        bot = make_bot(1)
        connection = StubConnection(bot, TOKEN)
        monkeypatch.setattr(
            connection,
            "post_stats",
            AsyncMock(side_effect=[RuntimeError("401 Unauthorized"), None]),
        )
        # Two posts, then close the bot so the loop terminates.
        bot.is_closed.side_effect = [False, False, True]

        sleep_calls = []

        async def fake_sleep(seconds):
            sleep_calls.append(seconds)

        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        with caplog.at_level(logging.ERROR):
            await connection.run_post_loop()

        assert connection.post_stats.await_count == 2
        assert sleep_calls == [StubConnection.post_interval_seconds] * 2
        assert "Failed to post stats to Stub List: 401 Unauthorized" in caplog.text

    @pytest.mark.asyncio
    async def test_does_not_post_when_bot_is_already_closed(
        self, fake_session: FakeSession
    ):
        bot = make_bot(1)
        bot.is_closed.return_value = True

        await StubConnection(bot, TOKEN).run_post_loop()

        assert fake_session.calls == []


class TestStartAllApiConnections:
    @pytest.fixture(autouse=True)
    def stub_bot(self, monkeypatch: pytest.MonkeyPatch) -> Mock:
        """Stand in for the module-level bot ``start_all_api_connections`` imports."""
        bot = make_bot(3908)
        bot_module = Mock()
        bot_module.get_bot.return_value = bot
        monkeypatch.setitem(__import__("sys").modules, "core.bot", bot_module)
        return bot

    def test_starts_a_connection_per_configured_token(
        self, monkeypatch: pytest.MonkeyPatch, stub_bot: Mock
    ):
        monkeypatch.setenv("TOPGG_AUTH_TOKEN", TOKEN)
        monkeypatch.setenv("DISCORDLISTS_AUTH_TOKEN", TOKEN)

        api_connections_manager.start_all_api_connections()

        started = [type(c) for c in stub_bot.bot_list_connections]
        assert started == [TopGGConnection, DiscordListConnection]

    @pytest.mark.parametrize("value", ["", "NONE", "missing"])
    def test_skips_placeholder_tokens(
        self, monkeypatch: pytest.MonkeyPatch, stub_bot: Mock, caplog, value: str
    ):
        """
        The shipped env template sets both tokens to "NONE", so a placeholder has
        to be treated as absent rather than posted with.
        """
        monkeypatch.setenv("TOPGG_AUTH_TOKEN", value)
        monkeypatch.setenv("DISCORDLISTS_AUTH_TOKEN", value)

        with caplog.at_level(logging.WARNING):
            api_connections_manager.start_all_api_connections()

        assert stub_bot.bot_list_connections == []
        assert "TOPGG_AUTH_TOKEN is not set or is invalid" in caplog.text
        assert "DISCORDLISTS_AUTH_TOKEN is not set or is invalid" in caplog.text
