"""
Tests for :mod:`modules.custom_types`.

``ExpiringSet`` reads the wall clock via ``time.time()`` and nothing else, so the
``clock`` fixture swaps the module's ``time`` reference for a fake one. Advancing
that clock exercises expiry deterministically and instantly; sleeping for real
would make these tests slow, and flaky on a loaded machine.
"""

from __future__ import annotations

import pytest

import modules.custom_types as custom_types
from modules.custom_types import ExpiringSet


class FakeClock:
    """Stands in for the ``time`` module: exposes ``time()`` and can be advanced."""

    def __init__(self, start: float = 1_000_000.0):
        self._now = start

    def time(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    fake = FakeClock()
    monkeypatch.setattr(custom_types, "time", fake)
    return fake


def test_items_are_present_immediately_after_add(clock: FakeClock) -> None:
    expiring_set = ExpiringSet(expiration_time=1)

    for i in range(100):
        expiring_set.add(f"item_{i}")

    assert all(f"item_{i}" in expiring_set for i in range(100))


def test_items_expire_once_the_expiration_time_has_passed(clock: FakeClock) -> None:
    expiring_set = ExpiringSet(expiration_time=1)
    for i in range(100):
        expiring_set.add(f"item_{i}")

    clock.advance(1.5)

    assert not any(f"item_{i}" in expiring_set for i in range(100))


def test_items_survive_right_up_to_the_expiration_boundary(clock: FakeClock) -> None:
    """Expiry is ``now > expiry``, so an item is still present *at* its deadline."""
    expiring_set = ExpiringSet(expiration_time=10)
    expiring_set.add("item")

    clock.advance(10)

    assert "item" in expiring_set


def test_re_adding_an_item_renews_its_expiration(clock: FakeClock) -> None:
    expiring_set = ExpiringSet(expiration_time=2)
    expiring_set.add("renewable_item")

    clock.advance(1)
    expiring_set.add("renewable_item")

    # 2.5s since the first add, but only 1.5s since the renewal.
    clock.advance(1.5)
    assert "renewable_item" in expiring_set

    # Now past 2s from the renewal.
    clock.advance(1)
    assert "renewable_item" not in expiring_set


def test_remove_drops_an_item(clock: FakeClock) -> None:
    expiring_set = ExpiringSet(expiration_time=10)
    expiring_set.add("item")

    expiring_set.remove("item")

    assert "item" not in expiring_set


def test_removing_an_absent_item_is_a_no_op(clock: FakeClock) -> None:
    expiring_set = ExpiringSet(expiration_time=10)

    expiring_set.remove("never_added")  # must not raise

    assert list(expiring_set) == []


def test_iteration_yields_live_items_and_purges_expired_ones(clock: FakeClock) -> None:
    expiring_set = ExpiringSet(expiration_time=1)
    for i in range(5):
        expiring_set.add(f"item_{i}")

    assert len(list(expiring_set)) == 5

    clock.advance(1.5)

    assert list(expiring_set) == []


def test_repr_shows_live_items_and_hides_expired_ones(clock: FakeClock) -> None:
    expiring_set = ExpiringSet(expiration_time=1)
    expiring_set.add("item_1")
    expiring_set.add("item_2")

    assert "item_1" in repr(expiring_set)
    assert "item_2" in repr(expiring_set)

    clock.advance(1.5)

    assert "item_1" not in repr(expiring_set)
    assert "item_2" not in repr(expiring_set)


def test_add_purges_expired_entries_so_a_write_only_set_does_not_grow(clock: FakeClock) -> None:
    """
    Regression guard for the unbounded-growth fix: a set that is only ever
    written to (never read) must still shed expired entries on ``add``.
    """
    expiring_set = ExpiringSet(expiration_time=1)
    for i in range(50):
        expiring_set.add(f"old_{i}")

    clock.advance(1.5)
    expiring_set.add("new")

    # Reach into the store directly — going through __contains__/__iter__ would
    # purge on its own and mask a broken add().
    assert list(expiring_set.store.keys()) == ["new"]
