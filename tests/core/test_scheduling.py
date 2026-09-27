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


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def fake_cpu(monkeypatch: pytest.MonkeyPatch) -> tuple[FakeClock, list[float]]:
    """A controllable monotonic clock and a queue of psutil readings (last one repeats)."""
    clock = FakeClock()
    readings: list[float] = [0.0]
    monkeypatch.setattr(scheduling.time, "monotonic", clock)
    monkeypatch.setattr(scheduling.psutil, "cpu_percent", lambda: readings.pop(0) if len(readings) > 1 else readings[0])
    return clock, readings


def test_cpu_sampler_skips_readings_inside_the_window(fake_cpu) -> None:
    """
    Regression for the prod throttle noise: readings taken milliseconds apart were
    always 100.0% and triggered 10.5k throttles.
    """
    clock, readings = fake_cpu
    sampler = scheduling.CpuSampler(min_window_seconds=1.0)
    readings[:] = [100.0, 30.0]

    clock.now += 0.01
    assert sampler.sample() is None
    assert readings == [100.0, 30.0]  # psutil was not consulted (its baseline is intact)


def test_cpu_sampler_reads_once_the_window_has_elapsed(fake_cpu) -> None:
    clock, readings = fake_cpu
    sampler = scheduling.CpuSampler(min_window_seconds=1.0)
    readings[:] = [42.0, 42.0]

    clock.now += 1.5
    assert sampler.sample() == 42.0
    assert sampler.last_reading == 42.0

    clock.now += 0.2  # A new window starts at each reading
    assert sampler.sample() is None
