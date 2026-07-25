"""
Builders for the domain objects tests need.

The ``db`` fixture gives each test its own database, so IDs only have to be
unique within a test rather than across the whole suite. ``next_id()`` therefore
hands out monotonic IDs rather than random ones: a random ID makes a failure
awkward to reproduce, and buys nothing once tests no longer share a database.
"""

from __future__ import annotations

import datetime
import itertools
import random
import string
from zoneinfo import ZoneInfo

from config.messages.stored_messages import MessageRecord

# Discord snowflakes are large; start high enough that IDs look realistic and
# never collide with the small literal IDs (1, 111, 123456789) used in tests.
_id_counter = itertools.count(start=1_000_000_000_000)


def next_id() -> int:
    """Return a unique ID. Monotonic within a process, so failures reproduce."""
    return next(_id_counter)


def random_content(length: int = 200) -> str:
    """Message body of the given length, drawn from letters, punctuation and
    spaces — the characters that stress quoting on the way into SQLite."""
    alphabet = string.ascii_lowercase + r"!@#$%^&*()_+-=[]{};:'<>,./? "
    return "".join(random.choice(alphabet) for _ in range(length))


def make_message(**overrides) -> MessageRecord:
    """
    Build a :class:`MessageRecord` with sensible unique defaults.

    Any field can be overridden by keyword::

        make_message(guild_id=guild_id, content="hello")
    """
    message = MessageRecord(
        message_id=next_id(),
        guild_id=next_id(),
        channel_id=next_id(),
        author_id=next_id(),
        content=random_content(),
        last_updated=datetime.datetime.now(ZoneInfo("UTC")),
    )

    for key, value in overrides.items():
        setattr(message, key, value)

    return message


def aged_message(days_old: float, **overrides) -> MessageRecord:
    """A message whose ``last_updated`` sits ``days_old`` days in the past."""
    overrides.setdefault(
        "last_updated",
        datetime.datetime.now(ZoneInfo("UTC")) - datetime.timedelta(days=days_old),
    )
    return make_message(**overrides)
