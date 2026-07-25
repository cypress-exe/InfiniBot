"""
Mock nextcord objects.

Every mock is built with ``spec=`` so a typo in an attribute name fails the test
instead of silently returning a fresh ``Mock``. Only the attributes the code under
test actually reads are populated; add more here rather than hand-rolling a
one-off mock in a test module.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import nextcord


def make_role(name: str, mention: str | None = None) -> Mock:
    """A ``nextcord.Role`` carrying just a name and a mention."""
    role = Mock(spec=nextcord.Role)
    role.name = name
    role.mention = mention if mention is not None else f"<@&{abs(hash(name)) % 10**18}>"
    return role


def make_guild(
    roles: list[Mock] | None = None,
    *,
    guild_id: int = 1,
    name: str = "Test Guild",
    member_count: int = 10,
    owner_id: int = 999,
) -> Mock:
    """
    A ``nextcord.Guild`` with an ``@everyone`` default role plus ``roles``.

    Populates the fields the generic-replacement code reads (name, id,
    member_count, owner) with fixed values.
    """
    default_role = make_role("@everyone", "@everyone")

    guild = Mock(spec=nextcord.Guild)
    guild.id = guild_id
    guild.name = name
    guild.member_count = member_count
    guild.owner = Mock(display_name="GuildOwner")
    guild.owner_id = owner_id
    guild.default_role = default_role
    guild.roles = [default_role] + list(roles or [])
    guild.unavailable = False
    return guild


def make_guild_with_member_fetch(fetch_side_effect, *, guild_id: int = 111) -> Mock:
    """
    A guild whose member cache always misses, forcing ``fetch_member``.

    ``fetch_side_effect`` is handed to the ``AsyncMock`` backing
    ``fetch_member`` — pass an exception instance to simulate a failed fetch.
    """
    guild = make_guild(guild_id=guild_id)
    guild.get_member = Mock(return_value=None)  # cache miss -> forces a fetch
    guild.fetch_member = AsyncMock(side_effect=fetch_side_effect)
    return guild


def make_member(
    *,
    mention: str = "@TestUser",
    communication_disabled_until=None,
) -> Mock:
    """A ``nextcord.Member`` with the timeout-related fields action_logging reads."""
    member = Mock(spec=nextcord.Member)
    member.mention = mention
    member.communication_disabled_until = communication_disabled_until
    return member


def make_text_channel() -> Mock:
    """A ``nextcord.TextChannel`` with ``send`` as an ``AsyncMock``."""
    channel = Mock(spec=nextcord.TextChannel)
    channel.send = AsyncMock()
    return channel


def http_error(exception_type: type, status: int, reason: str, message: str) -> Exception:
    """
    Build a nextcord HTTP exception.

    These take ``(response, message)`` and read ``response.status`` /
    ``response.reason``, so a bare ``Mock`` response is enough.
    """
    response = Mock()
    response.status = status
    response.reason = reason
    return exception_type(response, message)


def discord_server_error(message: str = "upstream connect error") -> Exception:
    """A transient 503 from Discord."""
    return http_error(nextcord.DiscordServerError, 503, "Service Unavailable", message)


def not_found_error(message: str = "Unknown Member") -> Exception:
    """A genuine 404 from Discord."""
    return http_error(nextcord.NotFound, 404, "Not Found", message)
