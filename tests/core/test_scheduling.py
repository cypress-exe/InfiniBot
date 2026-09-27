"""
Tests for :mod:`core.scheduling`: starting the scheduler.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import core.scheduling as scheduling


@pytest.fixture
async def fresh_scheduler(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncIOScheduler]:
    """Swap in an unstarted scheduler so tests never share the module singleton."""
    new_scheduler = AsyncIOScheduler()
    monkeypatch.setattr(scheduling, "scheduler", new_scheduler)
    yield new_scheduler
    if new_scheduler.running:
        # The shutdown is deferred to the loop, so give it a tick before the loop closes
        new_scheduler.shutdown(wait=False)
        await asyncio.sleep(0)


async def test_start_scheduler_starts_one_job(fresh_scheduler: AsyncIOScheduler) -> None:
    scheduling.start_scheduler()
    await asyncio.sleep(0)

    assert fresh_scheduler.running
    assert len(fresh_scheduler.get_jobs()) == 1


async def test_repeated_start_keeps_scheduler_running(fresh_scheduler: AsyncIOScheduler) -> None:
    # on_ready fires again on every shard re-identify. Each call used to shut the
    # scheduler down (deferred) and raise, leaving it dead until the next on_ready.
    for _ in range(4):
        scheduling.start_scheduler()
        # Let any deferred call_soon_threadsafe work (e.g. a shutdown) run
        await asyncio.sleep(0.05)

        assert fresh_scheduler.running
        assert len(fresh_scheduler.get_jobs()) == 1
