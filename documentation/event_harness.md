# InfiniBot Synthetic Event Harness

`src/event_harness.py` fires fabricated Discord events directly through InfiniBot's real
event handlers (no gateway connection) to measure hot-path throughput and asyncio
event-loop lag.  Use it to establish a baseline and validate performance fixes with
before/after numbers.

---

## How to run

### Prerequisites

The harness is run from the **repo root** with the project's virtual environment:

```bash
# Local (no Docker)
.venv/bin/python src/event_harness.py [OPTIONS]

# Docker (mirrors run_tests.bash style)
./run_harness.bash [OPTIONS]
```

### Quick sanity check

```bash
.venv/bin/python src/event_harness.py --smoke
```

Fires 200 events across 10 synthetic guilds.  Should complete in under 10 seconds with 0
errors.

### Standard benchmark

```bash
.venv/bin/python src/event_harness.py --events 5000 --guilds 200
```

---

## CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--events N` | 5000 | Total events to dispatch. |
| `--guilds N` | 200 | Number of synthetic guilds. |
| `--seed INT` | 42 | RNG seed for reproducible runs. |
| `--smoke` | off | Shorthand for `--events 200 --guilds 10`. |
| `--enable-features FRACTION` | 0.25 | Fraction of guilds that have logging/leveling/moderation enabled via `Server` setters before the run.  Drives the expensive DB-read code paths. |
| `--db-path PATH` | (none) | Point the harness at an existing SQLite file (e.g. a prod snapshot) instead of a fresh ephemeral DB.  **Seeding is skipped.**  A loud WARNING is printed because message-log rows will be inserted — always run against a *copy*. |
| `--log-level LEVEL` | WARNING | Python logging verbosity: DEBUG / INFO / WARNING / ERROR. |

---

## Environment isolation

By default the harness creates a fully self-contained environment under
`./generated/harness-files/` (wiped and re-created on every run):

```
generated/harness-files/
  files/        ← harness.db (SQLite)
  backups/
  configure/    ← default_profane_words.txt
  logs/
```

Config-file paths and the database URL are remapped **before** importing `core.bot`, so
the harness never touches `./generated/files/prod.db` or your real config.

---

## What is measured

### Per-event-type latency

`time.perf_counter()` is wrapped around every `await handler(...)` call.  Four handler
types are driven with weighted random selection:

| Event type | Default weight |
|------------|---------------|
| `on_message` | 80 % |
| `on_raw_message_edit` | 10 % |
| `on_raw_message_delete` | 5 % |
| `on_member_join` | 5 % |

Statistics reported: **count, mean, p50, p95, max**.

### Event-loop lag watchdog

A concurrent `asyncio` task sleeps 50 ms in a loop and records
`actual_elapsed − 0.050` on each tick.  This is the headline number: in production,
large spikes here stall heartbeats and trigger gateway disconnects.

Statistics reported: **tick count, mean lag, p95 lag, max lag**.

### Throughput and RSS

Overall events/sec, RSS at start and end (via `psutil`).

---

## What is NOT measured / known caveats

- **Library command processing is excluded.**  `bot.process_commands` is patched with an
  `AsyncMock` so slash-command dispatch overhead is not in the numbers.
- `on_raw_message_edit` early-exits after the channel lookup because `channel.fetch_message`
  raises `nextcord.NotFound` (the mock channel has no real messages).  It still exercises
  the `feature_is_active` and DB-lookup path before returning.
- `action_logging.log_raw_message_delete` contains an intentional `asyncio.sleep(1)` for
  audit-log timing.  On guilds where logging is enabled this appears as ~1 s outliers in
  the `on_raw_message_delete` p95/max columns — this is **real application behaviour**, not
  a harness artefact.
- The harness seeds the DB synchronously in `main()` before `asyncio.run()`.  Seeding
  writes `Server` profile rows into the ephemeral SQLite so `feature_is_active()` returns
  `True` for the configured fraction of guilds.
- Mock objects use `spec=nextcord.X` so `isinstance` checks pass.  Every attribute the
  handlers read is explicitly configured; bare Mock attributes that could silently swallow
  errors were identified by tracing each handler's code path.

---

## How to interpret the output

```
======================================================================
  INFINIBOT SYNTHETIC EVENT HARNESS — RESULTS
======================================================================
  Events requested  : 5,000
  Events succeeded  : 5,000
  Events errored    : 0
  Wall time         : 167.569 s
  Throughput        : 29.8 events/sec
  Guilds            : 200
  Active-features % : 25%
  RSS start         : 261.4 MiB
  RSS end          : 320.4 MiB

  --- Per-event-type latency (handler wall time) ---
  Event                               N       mean        p50        p95        max
  ------------------------------  ------  ---------  ---------  ---------  ---------
  on_message                       4027    25.5 ms    17.8 ms    52.7 ms   442.5 ms
  on_raw_message_edit               510     4.5 ms     4.3 ms     5.5 ms    11.7 ms
  on_raw_message_delete             217   282.8 ms     4.3 ms  1012.6 ms  1014.8 ms
  on_member_join                    246     4.5 ms     4.5 ms     5.2 ms     7.3 ms

  --- Event-loop lag watchdog (asyncio sleep(0.05) drift) ---
  Ticks sampled     : 1,200
  Lag mean          : 87.7 ms
  Lag p95           : 1.4 ms
  Lag max           : 6250.8 ms
======================================================================
```

**Throughput** — lower than expected here because `on_message` is synchronous-IO heavy
(per-property SQL SELECTs, JSON config reads on every `feature_is_active()` call).

**Event-loop lag mean >> p95** — the mean is pulled up by a few large spikes (SQLite
serialised writes, the `asyncio.sleep(1)` in delete-log logic).  p95 at 1.4 ms shows that
the *typical* tick is fast.

**`on_raw_message_delete` p95 ≈ 1 s** — expected: `action_logging.log_raw_message_delete`
deliberately sleeps 1 s for audit-log timing, and ~25% of delete events hit guilds with
logging enabled.

**Error count** — should be 0 for a healthy run.  Any errors are caught, counted per event
type, and the first 3 unique tracebacks are printed.  A run with >10% errors exits with
code 1.

---

## Example output (smoke run)

```
-- smoke mode: events=200, guilds=10 --

======================================================================
  INFINIBOT SYNTHETIC EVENT HARNESS — RESULTS
======================================================================
  Events requested  : 200
  Events succeeded  : 200
  Events errored    : 0
  Wall time         : 5.795 s
  Throughput        : 34.5 events/sec
  Guilds            : 10
  Active-features % : 25%
  RSS start         : 100.5 MiB
  RSS end          : 101.9 MiB

  --- Per-event-type latency (handler wall time) ---
  Event                               N       mean        p50        p95        max
  ------------------------------  ------  ---------  ---------  ---------  ---------
  on_message                        162    22.3 ms    17.7 ms    44.5 ms    62.7 ms
  on_raw_message_edit                21     4.2 ms     4.1 ms     5.1 ms     5.3 ms
  on_raw_message_delete               7   292.0 ms     4.1 ms  1011.6 ms  1011.6 ms
  on_member_join                     10     4.5 ms     4.4 ms     4.8 ms     4.9 ms

  --- Event-loop lag watchdog (asyncio sleep(0.05) drift) ---
  Ticks sampled     : 40
  Lag mean          : 34.8 ms
  Lag p95           : 21.7 ms
  Lag max           : 956.4 ms
======================================================================
```

---

## Example output (full run — 5000 events, 200 guilds)

```
======================================================================
  INFINIBOT SYNTHETIC EVENT HARNESS — RESULTS
======================================================================
  Events requested  : 5,000
  Events succeeded  : 5,000
  Events errored    : 0
  Wall time         : 167.569 s
  Throughput        : 29.8 events/sec
  Guilds            : 200
  Active-features % : 25%
  RSS start         : 261.4 MiB
  RSS end          : 320.4 MiB

  --- Per-event-type latency (handler wall time) ---
  Event                               N       mean        p50        p95        max
  ------------------------------  ------  ---------  ---------  ---------  ---------
  on_message                       4027    25.5 ms    17.8 ms    52.7 ms   442.5 ms
  on_raw_message_edit               510     4.5 ms     4.3 ms     5.5 ms    11.7 ms
  on_raw_message_delete             217   282.8 ms     4.3 ms  1012.6 ms  1014.8 ms
  on_member_join                    246     4.5 ms     4.5 ms     5.2 ms     7.3 ms

  --- Event-loop lag watchdog (asyncio sleep(0.05) drift) ---
  Ticks sampled     : 1,200
  Lag mean          : 87.7 ms
  Lag p95           : 1.4 ms
  Lag max           : 6250.8 ms
======================================================================
```
