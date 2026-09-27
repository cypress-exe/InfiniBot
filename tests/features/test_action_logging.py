"""
Tests for :mod:`features.action_logging` timeout reporting.

These are regressions from production incidents, so each one names the behavior
it protects rather than the function it calls.
"""

from __future__ import annotations

import datetime

import features.action_logging as action_logging
from unittest.mock import Mock

import nextcord

from tests.support.discord_mocks import make_guild, make_member, make_role, make_text_channel


def in_minutes(minutes: int) -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=minutes)


async def test_a_timeout_that_lapsed_mid_event_is_not_reported() -> None:
    """
    Regression for the prod TypeError (logfile 2026-07-22 22:05):
        'unsupported operand type(s) for -: NoneType and datetime.datetime'

    ``Member.communication_disabled_until`` returns None once the timeout instant
    has passed, so its value can flip from a datetime to None *between*
    log_member_update's ``before != after`` check and the read inside
    log_timeout_change — the intervening audit-log fetch is awaited. The
    "newly timed out" branch then dereferenced a None.
    """
    before = make_member(communication_disabled_until=None)
    after = make_member(mention="@LapsedUser", communication_disabled_until=None)
    log_channel = make_text_channel()

    # entry=None -> the actor resolves to "Someone"; this must not raise.
    await action_logging.log_timeout_change(before, after, entry=None, log_channel=log_channel)

    # Nothing meaningful to report for a timeout that lapsed before it was logged.
    log_channel.send.assert_not_awaited()


async def test_a_new_timeout_is_logged() -> None:
    before = make_member(communication_disabled_until=None)
    after = make_member(mention="@TimedOutUser", communication_disabled_until=in_minutes(10))
    log_channel = make_text_channel()

    await action_logging.log_timeout_change(before, after, entry=None, log_channel=log_channel)

    log_channel.send.assert_awaited_once()
    assert log_channel.send.await_args.kwargs["embed"].title == "Member Timed-Out"


async def test_a_revoked_timeout_is_logged() -> None:
    before = make_member(communication_disabled_until=in_minutes(5))
    after = make_member(mention="@RevokedUser", communication_disabled_until=None)
    log_channel = make_text_channel()

    await action_logging.log_timeout_change(before, after, entry=None, log_channel=log_channel)

    log_channel.send.assert_awaited_once()
    assert log_channel.send.await_args.kwargs["embed"].title == "Timeout Revoked"


async def test_delete_log_button_is_not_stored_per_message() -> None:
    """
    Regression for the prod view leak: every delete log used to send a fresh
    ShowMoreButton that nextcord stored forever, growing the view store
    unboundedly. The one instance registered at startup handles clicks on
    every log message, so sending one must not store another.
    """
    view = action_logging.ShowMoreButton()

    # nextcord stores a sent view only when prevent_update is set
    assert view.prevent_update is False
    # ...and it must still be registrable as the persistent startup instance
    assert view.is_persistent()


async def test_a_role_change_by_an_unresolvable_user_is_still_logged() -> None:
    """
    Regression for the prod AttributeError:
        'NoneType' object has no attribute 'mention'

    A fresh audit-log entry can have no resolvable user (e.g. a deleted account).
    The role-change log dereferenced entry.user.mention anyway and dropped the log.
    """
    everyone = make_role("@everyone", "@everyone")
    everyone.id = 1
    role = make_role("Member", "@Member")
    role.id = 4242
    before = make_member(mention="@Target")
    before.id = 77
    before.roles = [everyone]
    after = make_member(mention="@Target")
    after.id = 77
    after.roles = [everyone, role]
    guild = make_guild()
    guild.premium_subscriber_role = None
    entry = Mock(spec=nextcord.AuditLogEntry)
    entry.user = None
    entry.reason = None
    entry.created_at = in_minutes(0)
    log_channel = make_text_channel()

    await action_logging.log_role_change(before, after, entry, guild, log_channel)

    log_channel.send.assert_awaited_once()
    assert log_channel.send.await_args.kwargs["embed"].description == "Someone modified @Target's roles."
