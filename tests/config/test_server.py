"""
Tests for :class:`config.server.Server` — every per-guild setting the dashboard
can change.

``SCALAR_PROPERTIES`` tables every setting with its default, some values that
must round-trip and some that must be rejected; ``INTEGRATED_LISTS`` does the
same for the per-guild tables. Both are fed to ``parametrize``, so each property
is an independent test that names itself in the report:

    test_property_default[leveling_profile.max_points_per_message]

Adding a setting to ``Server`` means adding a row to the table — not writing a
test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from config.file_manager import read_txt_to_list
from config.messages.stored_messages import get_all_messages_from_db, store_message_in_db
from config.server import Server
from modules.custom_types import UNSET_VALUE
from tests.support.factories import make_message, next_id

pytestmark = pytest.mark.integration

# Shared invalid-value tables. Each entry is (expected_exception, value).
INVALID_INT = [(ValueError, -1), (TypeError, "abc"), (TypeError, None)]
INVALID_BOOL = [(TypeError, "abc"), (TypeError, None)]
INVALID_CHANNEL = [(TypeError, "abc")]
INVALID_CHANNEL_OR_NONE = INVALID_CHANNEL + [(TypeError, None)]

EMBED_COLORS = ["Red", "Orange", "Yellow", "Green", 0x00FF00, 0x0000FF]


class ProfaneWordsDefault:
    """
    Sentinel for ``filtered_words``, whose default is the contents of
    ``default_profane_words.txt``. That file lives in the per-test sandbox, so the
    value cannot be resolved at collection time — only inside a running test.
    """

    def resolve(self) -> list[str]:
        return read_txt_to_list("default_profane_words.txt")


PROFANE_WORDS = ProfaneWordsDefault()


@dataclass(frozen=True)
class Property:
    """One configurable setting and everything known about its contract."""

    profile: str
    name: str
    default: Any
    valid_values: list
    invalid_values: list = field(default_factory=list)

    @property
    def id(self) -> str:
        return f"{self.profile}.{self.name}"


SCALAR_PROPERTIES = [
    # --- profanity moderation ---------------------------------------------- #
    Property("profanity_moderation_profile", "active", False, [True, False], INVALID_BOOL),
    Property("profanity_moderation_profile", "channel", UNSET_VALUE, [1234567989, None, UNSET_VALUE], INVALID_CHANNEL),
    Property("profanity_moderation_profile", "strike_system_active", True, [False, True], INVALID_BOOL),
    Property("profanity_moderation_profile", "max_strikes", 3, [5, 0], INVALID_INT),
    Property("profanity_moderation_profile", "strike_expiring_active", True, [False, True], INVALID_BOOL),
    Property("profanity_moderation_profile", "strike_expire_days", 7, [10, 0], INVALID_INT),
    Property("profanity_moderation_profile", "timeout_seconds", 3600, [7200, 0], INVALID_INT),
    Property(
        "profanity_moderation_profile",
        "filtered_words",
        PROFANE_WORDS,
        [["hello", "world"], ["apple", "banana", "orange", "pineapple", "grape"], PROFANE_WORDS],
        [(ValueError, ["apple", "grape", "apple", "orange"])],  # no duplicates
    ),
    # --- spam moderation ---------------------------------------------------- #
    Property("spam_moderation_profile", "active", False, [True, False], INVALID_BOOL),
    Property("spam_moderation_profile", "score_threshold", 100, [12, 1500, 0], INVALID_INT),
    Property("spam_moderation_profile", "time_threshold_seconds", 60, [500, 0], INVALID_INT),
    Property("spam_moderation_profile", "timeout_seconds", 60, [140, 0], INVALID_INT),
    Property("spam_moderation_profile", "delete_invites", False, [True, False], INVALID_BOOL),
    # --- logging ------------------------------------------------------------ #
    Property("logging_profile", "active", False, [True, False], INVALID_BOOL),
    Property("logging_profile", "channel", UNSET_VALUE, [1234567989, UNSET_VALUE], INVALID_CHANNEL_OR_NONE),
    # --- leveling ----------------------------------------------------------- #
    Property("leveling_profile", "active", False, [True, False], INVALID_BOOL),
    Property("leveling_profile", "channel", UNSET_VALUE, [1234567989, UNSET_VALUE, 0, None], INVALID_CHANNEL),
    Property("leveling_profile", "level_up_embed[title]", "Congratulations, @displayname!", ["Title_Changed", None]),
    Property("leveling_profile", "level_up_embed[description]", "Congrats @mention! You reached level [level]!", ["Description_Changed"]),
    Property("leveling_profile", "level_up_embed[color]", "White", EMBED_COLORS),
    Property("leveling_profile", "points_lost_per_day", 0, [12, 0, 1], INVALID_INT),
    # None is allowed here (it means "no cap"), so it is dropped from the invalid table.
    Property("leveling_profile", "max_points_per_message", 40, [200, None, 0, 20, 500], [entry for entry in INVALID_INT if entry != (TypeError, None)]),
    Property("leveling_profile", "exempt_channels", [], [[1234567989, 256468532], [1234567989, 256468532, 494621612]], [(ValueError, [1234, 9876, 1234])]),
    Property("leveling_profile", "allow_leveling_cards", True, [False, True], INVALID_BOOL),
    # --- join / leave messages ---------------------------------------------- #
    Property("join_message_profile", "active", False, [True, False], INVALID_BOOL),
    Property("join_message_profile", "channel", UNSET_VALUE, [1234567989, UNSET_VALUE], INVALID_CHANNEL_OR_NONE),
    Property("join_message_profile", "embed[title]", "@displayname just joined the server!", ["Title_Changed", None]),
    Property("join_message_profile", "embed[description]", "Welcome to the server, @mention!", ["Description_Changed"]),
    Property("join_message_profile", "embed[color]", "Blurple", EMBED_COLORS),
    Property("join_message_profile", "allow_join_cards", True, [False, True], INVALID_BOOL),
    Property("leave_message_profile", "active", False, [True, False], INVALID_BOOL),
    Property("leave_message_profile", "channel", UNSET_VALUE, [1234567989, UNSET_VALUE], INVALID_CHANNEL_OR_NONE),
    Property("leave_message_profile", "embed[title]", "@displayname just left the server.", ["Title_Changed", None]),
    Property("leave_message_profile", "embed[description]", "@mention left.", ["Description_Changed"]),
    Property("leave_message_profile", "embed[color]", "Blurple", EMBED_COLORS),
    # --- birthdays ---------------------------------------------------------- #
    Property("birthdays_profile", "channel", UNSET_VALUE, [1234567989, None, UNSET_VALUE], INVALID_CHANNEL),
    Property("birthdays_profile", "embed[title]", "Happy Birthday, [realname]!", ["Title_Changed", None]),
    Property("birthdays_profile", "embed[description]", "@mention just turned [age]!", ["Description_Changed"]),
    Property("birthdays_profile", "embed[color]", "Gold", EMBED_COLORS),
    Property("birthdays_profile", "runtime", UNSET_VALUE, ["12:00 MDT", "8:00 PDT", "18:00 UTC", "0:00 EST", UNSET_VALUE], [(TypeError, None)]),
    # --- InfiniBot settings -------------------------------------------------- #
    Property("infinibot_settings_profile", "get_updates", True, [False, True], INVALID_BOOL),
    Property("infinibot_settings_profile", "timezone", UNSET_VALUE, [ZoneInfo("America/Los_Angeles").key, ZoneInfo("America/New_York").key, UNSET_VALUE], [(TypeError, None)]),
    # --- simple lists -------------------------------------------------------- #
    Property("join_to_create_vcs", "channels", [], [[1234567989, 256468532], [1234567989, 256468532, 494621612]], [(ValueError, [1234567989, 256468532, 1234567989])]),
    Property("default_roles", "default_roles", [], [[1234567989, 256468532], [1234567989, 256468532, 494621612]], [(ValueError, [1234567989, 256468532, 1234567989])]),
]


def resolve(value: Any) -> Any:
    """Expand a lazy default (see :class:`ProfaneWordsDefault`) at test time."""
    return value.resolve() if isinstance(value, ProfaneWordsDefault) else value


def get_property(server: Server, spec: Property) -> Any:
    """Read ``spec`` off ``server``, handling the ``embed[title]`` item syntax."""
    name, _, item = spec.name.partition("[")
    profile = getattr(server, spec.profile)
    return getattr(profile, name)[item[:-1]] if item else getattr(profile, name)


def set_property(server: Server, spec: Property, value: Any) -> None:
    """Write ``spec`` on ``server``, handling the ``embed[title]`` item syntax."""
    name, _, item = spec.name.partition("[")
    profile = getattr(server, spec.profile)
    if item:
        # Itemized properties round-trip through the whole dict.
        container = getattr(profile, name)
        container[item[:-1]] = value
        setattr(profile, name, container)
    else:
        setattr(profile, name, value)


@pytest.fixture
def server(db) -> Server:
    return Server(next_id())


# --------------------------------------------------------------------------- #
# Scalar properties
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("spec", SCALAR_PROPERTIES, ids=lambda spec: spec.id)
def test_property_default(server: Server, spec: Property) -> None:
    assert get_property(server, spec) == resolve(spec.default)


@pytest.mark.parametrize("spec", SCALAR_PROPERTIES, ids=lambda spec: spec.id)
def test_property_round_trips_in_memory(server: Server, spec: Property) -> None:
    for value in spec.valid_values:
        expected = resolve(value)
        set_property(server, spec, expected)

        assert get_property(server, spec) == expected


@pytest.mark.parametrize("spec", SCALAR_PROPERTIES, ids=lambda spec: spec.id)
def test_property_persists_to_a_new_server_instance(server: Server, spec: Property) -> None:
    """A setting is only useful if it survives the object that set it."""
    for value in spec.valid_values:
        expected = resolve(value)
        set_property(server, spec, expected)

        assert get_property(Server(server.server_id), spec) == expected


@pytest.mark.parametrize(
    ("spec", "expected_exception", "invalid_value"),
    [
        pytest.param(spec, exception, value, id=f"{spec.id}-{value!r}")
        for spec in SCALAR_PROPERTIES
        for exception, value in spec.invalid_values
    ],
)
def test_property_rejects_an_invalid_value(
    server: Server, spec: Property, expected_exception: type, invalid_value: Any
) -> None:
    """
    Validation lives in the setter, so a bad value written by a dashboard bug
    must raise rather than land in the database.
    """
    with pytest.raises(expected_exception):
        set_property(server, spec, invalid_value)


# --------------------------------------------------------------------------- #
# Integrated lists
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ListSpec:
    """An integrated-list table: its name, its secondary key, and sample rows."""

    name: str
    key: str
    rows: list[dict]

    @property
    def id(self) -> str:
        return self.name

    def edited(self, row: dict, marker: int) -> dict:
        """A copy of ``row`` with every non-key field changed."""
        changed = dict(row)
        for column, value in row.items():
            if column == self.key:
                continue
            changed[column] = (
                value + marker if isinstance(value, int) else f"{value}-edited-{marker}"
            )
        return changed


INTEGRATED_LISTS = [
    ListSpec(
        "moderation_strikes",
        "member_id",
        [
            {"member_id": 101, "strikes": 1, "last_strike": "2026-01-01"},
            {"member_id": 102, "strikes": 2, "last_strike": "2026-02-02"},
            {"member_id": 103, "strikes": 2, "last_strike": "2026-03-03"},
        ],
    ),
    ListSpec(
        "member_levels",
        "member_id",
        [
            {"member_id": 201, "points": 10},
            {"member_id": 202, "points": 20},
            {"member_id": 203, "points": 20},
        ],
    ),
    ListSpec(
        "level_rewards",
        "role_id",
        [
            {"role_id": 301, "level": 5},
            {"role_id": 302, "level": 10},
            {"role_id": 303, "level": 10},
        ],
    ),
    ListSpec(
        "birthdays",
        "member_id",
        [
            {"member_id": 401, "birth_date": "2000-01-01", "real_name": "Ada"},
            {"member_id": 402, "birth_date": "2001-02-02", "real_name": "Grace"},
            {"member_id": 403, "birth_date": "2002-03-03", "real_name": "Grace"},
        ],
    ),
    ListSpec(
        "join_to_create_active_vcs",
        "channel_id",
        [{"channel_id": 501}, {"channel_id": 502}, {"channel_id": 503}],
    ),
    ListSpec(
        "autobans",
        "member_id",
        [
            {"member_id": 601, "member_name": "spammer_one"},
            {"member_id": 602, "member_name": "spammer_two"},
            {"member_id": 603, "member_name": "spammer_two"},
        ],
    ),
    ListSpec(
        "managed_messages",
        "message_id",
        [
            {"message_id": 701, "channel_id": 71, "author_id": 81, "message_type": "embed", "json_data": "{}"},
            {"message_id": 702, "channel_id": 72, "author_id": 82, "message_type": "role", "json_data": "{}"},
            {"message_id": 703, "channel_id": 73, "author_id": 83, "message_type": "role", "json_data": "{}"},
        ],
    ),
]

list_specs = pytest.mark.parametrize("spec", INTEGRATED_LISTS, ids=lambda spec: spec.id)


def populate(server: Server, spec: ListSpec):
    table = getattr(server, spec.name)
    for row in spec.rows:
        table.add(**row)
    return table


def assert_rows_match(table, spec: ListSpec, rows: list[dict]) -> None:
    """Every row in ``rows`` is present in ``table`` with all its fields intact."""
    for row in rows:
        entry = table[row[spec.key]]
        for column, value in row.items():
            assert getattr(entry, column) == value, f"{spec.name}.{column} for key {row[spec.key]}"


@list_specs
def test_integrated_list_starts_empty(server: Server, spec: ListSpec) -> None:
    assert len(getattr(server, spec.name)) == 0


@list_specs
def test_added_rows_read_back(server: Server, spec: ListSpec) -> None:
    table = populate(server, spec)

    assert len(table) == len(spec.rows)
    assert_rows_match(table, spec, spec.rows)


@list_specs
def test_added_rows_persist_to_a_new_server_instance(server: Server, spec: ListSpec) -> None:
    populate(server, spec)

    assert_rows_match(getattr(Server(server.server_id), spec.name), spec, spec.rows)


@list_specs
def test_edited_rows_persist_to_a_new_server_instance(server: Server, spec: ListSpec) -> None:
    table = populate(server, spec)
    edited = [spec.edited(row, marker=7) for row in spec.rows]

    for row in edited:
        table.edit(row[spec.key], **row)

    assert_rows_match(getattr(Server(server.server_id), spec.name), spec, edited)


@list_specs
def test_get_matching_selects_rows_sharing_a_non_key_value(
    server: Server, spec: ListSpec
) -> None:
    """The last two sample rows share every non-key value, so a shared field
    selects exactly those two — and not the first row."""
    table = populate(server, spec)
    shared_columns = [
        column
        for column in spec.rows[0]
        if column != spec.key and spec.rows[1][column] == spec.rows[2][column]
    ]
    if not shared_columns:
        # join_to_create_active_vcs is (server_id, channel_id) plus an
        # auto-populated timestamp: no payload field exists to match on.
        # test_get_matching_selects_a_single_row_by_key covers it instead.
        pytest.skip(f"{spec.name} has no non-key column to match on")
    column = shared_columns[0]
    value = spec.rows[1][column]

    matches = table.get_matching(**{column: value})

    assert len(matches) == 2
    assert all(getattr(match, column) == value for match in matches)


@list_specs
def test_get_matching_selects_a_single_row_by_key(server: Server, spec: ListSpec) -> None:
    """Matching on the secondary key narrows to exactly that row."""
    table = populate(server, spec)
    key_value = spec.rows[1][spec.key]

    matches = table.get_matching(**{spec.key: key_value})

    assert len(matches) == 1
    assert getattr(matches[0], spec.key) == key_value


@list_specs
def test_delete_removes_a_single_row(server: Server, spec: ListSpec) -> None:
    table = populate(server, spec)

    table.delete(spec.rows[0][spec.key])

    remaining = getattr(Server(server.server_id), spec.name)
    assert len(remaining) == len(spec.rows) - 1
    assert_rows_match(remaining, spec, spec.rows[1:])


@list_specs
def test_delete_all_matching_removes_only_matching_rows(server: Server, spec: ListSpec) -> None:
    table = populate(server, spec)
    key_value = spec.rows[0][spec.key]

    table.delete_all_matching(**{spec.key: key_value})

    remaining = getattr(Server(server.server_id), spec.name)
    assert len(remaining) == len(spec.rows) - 1


@list_specs
def test_delete_all_empties_the_table(server: Server, spec: ListSpec) -> None:
    table = populate(server, spec)

    table.delete_all()

    assert len(getattr(Server(server.server_id), spec.name)) == 0


# --------------------------------------------------------------------------- #
# Server lifecycle
# --------------------------------------------------------------------------- #


def test_server_keeps_the_id_it_was_created_with(db) -> None:
    server_id = next_id()

    assert Server(server_id).server_id == server_id


@pytest.mark.parametrize("invalid_id", [None, 0, "", False, True])
def test_server_rejects_an_unusable_id(db, invalid_id) -> None:
    with pytest.raises(ValueError):
        Server(invalid_id)


def test_remove_all_data_resets_configured_settings(db) -> None:
    server = Server(next_id())
    server.profanity_moderation_profile.active = True
    server.profanity_moderation_profile.channel = 123456789
    server.spam_moderation_profile.active = True
    server.leveling_profile.active = True
    server.join_message_profile.active = True

    server.remove_all_data()

    reloaded = Server(server.server_id)
    assert reloaded.profanity_moderation_profile.active is False
    assert reloaded.profanity_moderation_profile.channel == UNSET_VALUE
    assert reloaded.spam_moderation_profile.active is False
    assert reloaded.leveling_profile.active is False
    assert reloaded.join_message_profile.active is False


def test_remove_all_data_restores_embed_defaults(db) -> None:
    server = Server(next_id())
    embed = server.leveling_profile.level_up_embed
    embed["title"] = "Changed Title"
    embed["description"] = "Changed Description"
    embed["color"] = 0x00FF00
    server.leveling_profile.level_up_embed = embed

    server.remove_all_data()

    embed = Server(server.server_id).leveling_profile.level_up_embed
    assert embed["title"] == "Congratulations, @displayname!"
    assert embed["description"] == "Congrats @mention! You reached level [level]!"
    assert embed["color"] == "White"


def test_remove_all_data_clears_integrated_lists(db) -> None:
    server = Server(next_id())
    server.birthdays.add(member_id="123456789", birth_date="2023-01-01", real_name=None)
    server.birthdays.add(member_id="987654321", birth_date="2023-01-02", real_name="John Doe")
    server.default_roles.default_roles = [123456789]

    server.remove_all_data()

    reloaded = Server(server.server_id)
    assert len(reloaded.birthdays) == 0
    assert len(reloaded.default_roles.default_roles) == 0


def test_remove_all_data_deletes_the_guilds_stored_messages(db) -> None:
    server = Server(next_id())
    for _ in range(5):
        store_message_in_db(make_message(guild_id=server.server_id), override_checks=True)

    server.remove_all_data()

    assert get_all_messages_from_db(guild_id=server.server_id) == []


def test_remove_all_data_leaves_other_guilds_untouched(db) -> None:
    departing = Server(next_id())
    staying = Server(next_id())
    staying.profanity_moderation_profile.active = True
    store_message_in_db(make_message(guild_id=staying.server_id), override_checks=True)
    departing.profanity_moderation_profile.active = True

    departing.remove_all_data()

    assert Server(staying.server_id).profanity_moderation_profile.active is True
    assert len(get_all_messages_from_db(guild_id=staying.server_id)) == 1
