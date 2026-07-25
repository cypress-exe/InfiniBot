"""
Tests for :mod:`components.utils`.

Three unrelated areas live here because they share a module: the feature
kill-switch check, the required-permissions table, and the ``@mention``
replacement grammar used when rendering configurable embeds.
"""

from __future__ import annotations

import nextcord
import pytest

import components.utils as utils
from components.utils import apply_generic_replacements, feature_is_active
from config.global_settings import get_global_kill_status, required_permissions
from config.server import Server
from modules.custom_types import ExpiringSet
from tests.support.discord_mocks import (
    discord_server_error,
    make_guild,
    make_guild_with_member_fetch,
    make_role,
    not_found_error,
)
from tests.support.factories import next_id

FEATURE = "moderation__profanity"


# --------------------------------------------------------------------------- #
# feature_is_active
# --------------------------------------------------------------------------- #


def test_feature_is_inactive_when_the_server_has_not_enabled_it(db) -> None:
    assert feature_is_active(server_id=next_id(), feature=FEATURE) is False


def test_feature_is_active_when_the_server_enables_it(db) -> None:
    server = Server(next_id())
    server.profanity_moderation_profile.active = True

    assert feature_is_active(server=server, feature=FEATURE) is True


def test_global_kill_overrides_a_server_that_enabled_the_feature(db) -> None:
    """The kill switch is the whole point: it must win over server config."""
    server = Server(next_id())
    server.profanity_moderation_profile.active = True
    get_global_kill_status()[FEATURE] = True

    assert feature_is_active(server=server, feature=FEATURE) is False


def test_global_kill_applies_to_a_server_looked_up_by_id(db) -> None:
    get_global_kill_status()[FEATURE] = True

    assert feature_is_active(server_id=next_id(), feature=FEATURE) is False


# --------------------------------------------------------------------------- #
# required_permissions
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "backend_permission",
    sorted(
        {
            backend_permission
            for permissions in required_permissions.values()
            for dependencies in permissions.values()
            for backend_permission in dependencies
        }
    ),
)
def test_required_permission_exists_in_nextcord(backend_permission: str) -> None:
    """
    Every permission the bot declares a dependency on must be a real
    ``nextcord.Permissions`` flag — a typo here would silently never be checked.

    Parametrized so a bad entry names itself in the failure.
    """
    assert hasattr(nextcord.Permissions, backend_permission)


# --------------------------------------------------------------------------- #
# apply_generic_replacements — role mentions
# --------------------------------------------------------------------------- #


def replace_in(guild, text: str) -> str:
    """Run the replacement over a description-only embed and return the result."""
    embed = nextcord.Embed(description=text)
    return apply_generic_replacements(
        embed, None, guild, skip_channel_replacement=True
    ).description


def test_bare_role_name_becomes_a_mention() -> None:
    guild = make_guild([make_role("Moderator", "<@&111>")])

    assert replace_in(guild, "Hello @Moderator!") == "Hello <@&111>!"


def test_unmatched_name_is_left_literal() -> None:
    guild = make_guild([make_role("Moderator", "<@&111>")])

    assert replace_in(guild, "Hello @NoSuchRole!") == "Hello @NoSuchRole!"


def test_everyone_is_never_matched_by_name() -> None:
    """
    Turning ``@everyone`` into a real mention is against stipulated rules.
    
    Even though a mention in a message never sends a ping, it was stipulated
    as a rule for this method to NOT convert ``@everyone`` into a real mention.
    """

    guild = make_guild([])

    assert replace_in(guild, "Welcome @everyone!") == "Welcome @everyone!"


def test_reserved_placeholder_beats_a_role_of_the_same_name() -> None:
    guild = make_guild([make_role("server", "<@&222>")])

    assert replace_in(guild, "Welcome to @server!") == "Welcome to Test Guild!"


def test_explicit_role_syntax_reaches_a_shadowed_role() -> None:
    guild = make_guild([make_role("server", "<@&222>")])

    assert replace_in(guild, "Welcome to @role:server!") == "Welcome to <@&222>!"


def test_longer_role_names_match_before_shorter_prefixes() -> None:
    """"Mod" must not eat the front of "Moderator"."""
    guild = make_guild(
        [make_role("Mod", "<@&111>"), make_role("Moderator", "<@&222>")]
    )

    result = replace_in(guild, "Ping @Moderator now, not @Mod.")

    assert result == "Ping <@&222> now, not <@&111>."


# --------------------------------------------------------------------------- #
# get_member — resilience to Discord HTTP errors
# --------------------------------------------------------------------------- #


@pytest.fixture(autouse=True)
def clean_failed_member_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    ``utils.failed_member_fetches`` is a module-global ExpiringSet with a 15-minute
    TTL, so an entry written by one test would otherwise be visible to the next
    for the rest of the session.
    """
    monkeypatch.setattr(utils, "failed_member_fetches", ExpiringSet(60 * 15))


async def test_get_member_returns_none_on_a_transient_server_error() -> None:
    """
    Regression for the prod ERROR (logfile 2026-07-22 20:09 / 22:56): a transient
    503 while fetching a member propagated out of ``get_member`` (which caught
    only Forbidden/NotFound) and surfaced as a feature error. It should absorb
    HTTP errors and return None, mirroring its sibling ``get_message``.
    """
    member_id = 987654321
    guild = make_guild_with_member_fetch(discord_server_error())

    assert await utils.get_member(guild, member_id) is None


async def test_a_transient_server_error_is_not_cached() -> None:
    """A 503 is temporary — caching it would suppress fetches that would now succeed."""
    member_id = 987654321
    guild = make_guild_with_member_fetch(discord_server_error())

    await utils.get_member(guild, member_id)

    assert (guild.id, member_id) not in utils.failed_member_fetches


async def test_get_member_returns_none_when_the_member_does_not_exist() -> None:
    guild = make_guild_with_member_fetch(not_found_error())

    assert await utils.get_member(guild, 987654322) is None


async def test_a_genuine_not_found_is_cached_to_suppress_repeat_fetches() -> None:
    member_id = 987654322
    guild = make_guild_with_member_fetch(not_found_error())

    await utils.get_member(guild, member_id)

    assert (guild.id, member_id) in utils.failed_member_fetches


async def test_a_cached_not_found_short_circuits_the_fetch() -> None:
    """The cache exists to stop repeat calls, so the second lookup must not refetch."""
    member_id = 987654323
    guild = make_guild_with_member_fetch(not_found_error())

    await utils.get_member(guild, member_id)
    guild.fetch_member.reset_mock()
    await utils.get_member(guild, member_id)

    guild.fetch_member.assert_not_awaited()
