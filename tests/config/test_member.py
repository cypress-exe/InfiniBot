"""
Tests for :class:`config.member.Member` — the per-user settings that follow a
member across every guild.

Same shape as ``test_server.py``: the property table drives pytest's parametrize
so each setting is its own test.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from config.member import Member
from tests.support.factories import next_id

pytestmark = pytest.mark.integration


@dataclass(frozen=True)
class Property:
    name: str
    default: Any
    valid_values: list

    @property
    def id(self) -> str:
        return self.name


MEMBER_PROPERTIES = [
    Property("level_up_card_enabled", False, [True, False]),
    Property("join_card_enabled", False, [True, False]),
    Property("level_up_card_embed[title]", "Yum... Levels", ["Title_Changed", None]),
    Property("level_up_card_embed[description]", "I am level [level]!", ["Description_Changed"]),
    Property("level_up_card_embed[color]", "Purple", ["Red", "Green", "White", None, 0x00FF00, 0x0000FF]),
    Property("join_card_embed[title]", "About Me", ["Title_Changed", None]),
    Property("join_card_embed[description]", "I am human", ["Description_Changed"]),
    Property("join_card_embed[color]", "Green", ["Red", "Purple", "White", None, 0x00FF00, 0x0000FF]),
    Property("direct_messages_enabled", True, [False, True]),
]

member_properties = pytest.mark.parametrize(
    "spec", MEMBER_PROPERTIES, ids=lambda spec: spec.id
)


def get_property(member: Member, spec: Property) -> Any:
    """Read ``spec`` off ``member``, handling the ``embed[title]`` item syntax."""
    name, _, item = spec.name.partition("[")
    return getattr(member, name)[item[:-1]] if item else getattr(member, name)


def set_property(member: Member, spec: Property, value: Any) -> None:
    """Write ``spec`` on ``member``, handling the ``embed[title]`` item syntax."""
    name, _, item = spec.name.partition("[")
    if item:
        # Itemized properties round-trip through the whole dict.
        container = getattr(member, name)
        container[item[:-1]] = value
        setattr(member, name, container)
    else:
        setattr(member, name, value)


@pytest.fixture
def member(db) -> Member:
    return Member(next_id())


def test_member_keeps_the_id_it_was_created_with(db) -> None:
    member_id = next_id()

    assert Member(member_id).member_id == member_id


@member_properties
def test_property_default(member: Member, spec: Property) -> None:
    assert get_property(member, spec) == spec.default


@member_properties
def test_property_round_trips_in_memory(member: Member, spec: Property) -> None:
    for value in spec.valid_values:
        set_property(member, spec, value)

        assert get_property(member, spec) == value


@member_properties
def test_property_persists_to_a_new_member_instance(member: Member, spec: Property) -> None:
    for value in spec.valid_values:
        set_property(member, spec, value)

        assert get_property(Member(member.member_id), spec) == value


def test_remove_all_data_restores_defaults(db) -> None:
    member = Member(next_id())
    member.level_up_card_enabled = True
    member.join_card_enabled = True
    member.direct_messages_enabled = False

    member.remove_all_data()

    reloaded = Member(member.member_id)
    assert reloaded.level_up_card_enabled is False
    assert reloaded.join_card_enabled is False
    assert reloaded.direct_messages_enabled is True


def test_remove_all_data_leaves_other_members_untouched(db) -> None:
    departing = Member(next_id())
    staying = Member(next_id())
    departing.level_up_card_enabled = True
    staying.level_up_card_enabled = True

    departing.remove_all_data()

    assert Member(staying.member_id).level_up_card_enabled is True
