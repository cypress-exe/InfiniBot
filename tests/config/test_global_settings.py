"""
Tests for :mod:`config.global_settings`.

The kill-status file is how features get disabled fleet-wide without a deploy,
so both halves matter: a known key must round-trip, and an unknown key must be
rejected loudly rather than silently accepted (a typo'd kill switch that appears
to work is worse than one that errors).
"""

from __future__ import annotations

import pytest

from config.global_settings import get_global_kill_status

# Profanity moderation stands in for "any real feature key".
FEATURE_KEY = "moderation__profanity"


def test_features_are_not_killed_by_default() -> None:
    assert get_global_kill_status()[FEATURE_KEY] is False


def test_setting_a_kill_switch_round_trips() -> None:
    get_global_kill_status()[FEATURE_KEY] = True

    assert get_global_kill_status()[FEATURE_KEY] is True


def test_reset_clears_a_set_kill_switch() -> None:
    get_global_kill_status()[FEATURE_KEY] = True

    get_global_kill_status().reset()

    assert get_global_kill_status()[FEATURE_KEY] is False


def test_reading_an_unknown_key_raises() -> None:
    with pytest.raises(AttributeError):
        get_global_kill_status()["fake_item"]


def test_writing_an_unknown_key_raises() -> None:
    with pytest.raises(AttributeError):
        get_global_kill_status()["fake_item"] = True


def test_kill_status_does_not_leak_between_tests() -> None:
    """
    Guards the conftest isolation: if the singleton cache or JSONFile cache
    survived a test, this would see the True written above.
    """
    assert get_global_kill_status()[FEATURE_KEY] is False
