# Production Log Analysis — 2026-07-22 → 2026-07-23

**Analyzed by:** Claude (Opus 4.8), 2026-07-22
**Logs:** `logfile-2026-07-22-05-52-42.log` (1.1 MB) + `logfile-2026-07-23-00-00-00.log` (360 KB)
**Coverage:** continuous, `2026-07-22 05:52:42` → `2026-07-23 05:48:55` (~24 h), single process, ~3909 guilds, 8 shards.

## Method

Log format is `TIMESTAMP - LEVEL - function - message`. Levels were parsed from the
real level field (position 3), **not** substring matches — the raw counts of lowercase
"error"/"critical" are message content ("error 404", "critical throttling"), not log
levels. Entries were grouped by *signature* (function + normalized message template,
with snowflake IDs / UUIDs / durations collapsed), then each distinct signature was
traced into the source tree. Two of the code-level defects were reproduced with
standalone scripts against the actual installed `nextcord`.

## Level summary (both files combined)

| Level | Count | Notes |
|---|---:|---|
| WARNING | 5,450 | 99.9% is just two signatures (HTTP 404 flood + CPU throttle) |
| INFO | 3,954 | normal operation |
| ERROR | 3 | two 503s + one TypeError (below) |
| CRITICAL | 0 | — |

There are **3 stack traces**, all in the older file. Everything else is single-line.

## Issue inventory (deduplicated)

| # | Signature | Count | First → Last seen | Severity | Root-cause type |
|---|---|---:|---|---|---|
| 1 | `TypeError: None - datetime` in `log_timeout_change` | 1 | 07-22 22:05 | **Medium** | Race condition (time-dependent property) |
| 2 | `DiscordServerError 503` uncaught in `get_member` | 2 | 07-22 20:09 → 22:56 | **Medium** | Missing exception handling + external outage |
| 3 | `CPU 100% > 75%, critical throttling` | 2,040 | entire 24 h, ~85/h | **Medium-High** | Architecture / scale (+ metric artifact + log noise) |
| 4 | `... resulted in error 404` (member/msg/channel fetch) | 3,402 | entire 24 h | **Low-Medium** | Handled-but-noisy + cache TTL too short |
| 5 | `403` on `remove_roles` / channel GET | 3 | — | **Low** | Missing guild permission (handled) |
| 6 | `add_roles_for_new_member`: role not found | 1 | 07-22 12:40 | **Low** | Stale config (deleted role) |
| 7 | join-to-create: `400 Target user is not connected to voice` | 1 | 07-22 23:34 | **Low** | Race (member left VC) |
| 8 | `ack`: shard 1 websocket 10.1s behind | 2 | 07-22 14:25 | **Low** | Gateway lag (likely CPU-correlated) |
| 9 | PyNaCl not installed | 1 | boot | **Info** | Intentional (voice unused) |

The 404 breakdown (Issue 4): **2,556** `GET /guilds/{}/members/{}` · **693** `GET /channels/{}/messages/{}` · **153** `GET /channels/{}`.

---

## Issue 1 — `TypeError: unsupported operand type(s) for -: 'NoneType' and 'datetime.datetime'`

**Signature:** `ERROR - __exit__ - Error occurred in feature: action_logging.log_member_update ...`
`src/features/action_logging.py:779`, reached via `on_member_update` → `log_member_update` → `log_timeout_change`.
**Frequency:** 1 in 24 h. **Severity:** Medium (crashes only the timeout-logging feature for one event; caught by `LogIfFailure`, no process impact — but it silently drops a moderation-audit log line).

### Root cause (confirmed)
`nextcord.Member.communication_disabled_until` is **time-dependent**. Its implementation (`nextcord/member.py:659`):

```python
if self._timeout is None or self._timeout < utils.utcnow():
    return None
return self._timeout
```

i.e. it returns `None` the moment the stored timeout expires, and the property is
re-evaluated on *every* access against the current wall clock.

`log_member_update` reads it multiple times across `await` boundaries and assumes the
value is stable:

- `log_member_update:920` — `await asyncio.sleep(1)`
- `log_member_update:946` — read #1: `before.cdu != after.cdu` → True, enter timeout branch
- `log_member_update:947` — `await find_audit_entry(...)` (a REST call, variable latency)
- `log_timeout_change:777` — `before.cdu is None` → take "newly timed out" branch
- `log_timeout_change:779` — read #2: `after.cdu - now()` → **`after.cdu` has since flipped to `None`**

For a member timed out with an expiry that lapses inside the window between read #1 and
read #2 (i.e. a very short timeout, roughly ≤ the 1 s sleep + audit-log fetch latency),
read #1 sees a `datetime` (branch entered) and read #2 sees `None` → `None - datetime`.
Its rarity (1×/24 h) matches the narrow timing window.

### Repro — **PASS**
Standalone script mirroring the real property semantics and call sequence reproduced the
exact prod message:
```
RESULT: reproduced -> TypeError - unsupported operand type(s) for -: 'NoneType' and 'datetime.datetime'
```

### Suggested fix
Snapshot each member's timeout **once** at the top of `log_timeout_change` and branch on
the locals, so the value can't change mid-function:
```python
before_cdu = before.communication_disabled_until
after_cdu  = after.communication_disabled_until
if before_cdu is None and after_cdu is not None:
    timeout_time = after_cdu - datetime.datetime.now(datetime.timezone.utc)
    ...
elif after_cdu is None:   # revoked or expired-in-flight
    ... "Timeout Revoked" ...
else:                     # both set → duration changed
    ...
```
Add an explicit `else` so a snapshot where both are non-`None` (duration edit / lapsed
race) is handled instead of falling through. Consider snapshotting in `log_member_update`
too and passing the values down, so the `!=` gate and the formatter agree.

---

## Issue 2 — `DiscordServerError: 503 Service Unavailable` uncaught in `get_member`

**Signature:** `ERROR - __exit__ - Error occurred in feature: utils.get_member (message edit profanity check) ...: 503 Service Unavailable ... upstream connect error`
`src/components/utils.py:865`, via `on_raw_message_edit` (`bot.py:576`).
**Frequency:** 2 (20:09 and 22:56), both during a brief Discord upstream disturbance.
**Severity:** Medium (feature-level; each occurrence aborts the profanity check on that edited message).

### Root cause (confirmed)
`get_member` only catches the "expected miss" exceptions:
```python
try:
    return await guild.fetch_member(user_id)
except (nextcord.Forbidden, nextcord.NotFound):   # utils.py:866
    ...
```
`DiscordServerError` (503/502/504) is **not** a subclass of `Forbidden`/`NotFound`, so a
transient Discord outage propagates out to the `LogIfFailure` handler and is logged as an
ERROR. Its sibling `get_message` (`utils.py:824`) already catches `nextcord.HTTPException`
(the base class of `DiscordServerError`) — so this is an inconsistency/oversight, not an
intentional difference.

### Repro — **PASS**
Against the installed nextcord: `issubclass(DiscordServerError, (Forbidden, NotFound))` is
`False`; a `DiscordServerError` raised inside `get_member`'s `except (Forbidden, NotFound)`
propagates, while `get_message`'s `except (..., HTTPException)` catches it.

### Suggested fix
Make `get_member` resilient like `get_message` — add `nextcord.HTTPException` to the
`except`. Note the caching semantics differ: a `NotFound` means "really gone" (cache it in
`failed_member_fetches`), whereas a 503 is transient and should **not** be cached (so a
retry is possible once Discord recovers):
```python
except (nextcord.Forbidden, nextcord.NotFound):
    failed_member_fetches.add((guild.id, user_id))
    return None
except nextcord.HTTPException as e:          # 5xx / rate-limit exhaustion — transient
    logging.debug(f"Transient error fetching member {user_id} in {guild.id}: {e}")
    return None                               # do NOT cache
```

---

## Issue 3 — CPU pegged: `CPU 100.0% > 75%, critical throttling` (2,040×)

**Signature:** `WARNING - run_scheduled_tasks - CPU {n}% > 75%, critical throttling for {d}s`
`src/core/scheduling.py:76`.
**Frequency:** ~85/hour, **flat across all 24 hours** (min 70/h, max 99/h). 2,027 of 2,040
report exactly `100.0%`. **Severity:** Medium-High (operational; also the single largest
source of log noise and a real symptom of the known scale ceiling).

### Root cause (three layers, all confirmed)
1. **Genuine CPU-bound scheduler work.** `run_scheduled_tasks` runs every
   `INTERVAL_MINUTES = 15` and walks **all ~3909 guilds synchronously**, constructing a
   `Server(guild.id)` object (DB reads) and running birthday/maintenance checks per guild
   (`scheduling.py:66-114`). CPU is sampled every `MONITORING_INTERVAL = 25` guilds
   (~156 samples/run × 4 runs/h ≈ 625 samples/h); ~13% land above 75%. This matches the
   memory note that the 4k-guild breakdown is **architectural, not a Python limitation**
   ([[infinibot-scale-assessment]]).
2. **Metric artifact inflates the number.** `psutil.cpu_percent(interval=None)`
   (`scheduling.py:70`) is non-blocking and measures utilization *since the previous call*.
   In this tight loop the window between samples is very short and dominated by the bot's
   own synchronous burst, so a busy stretch reads as a full `100.0%` even though the
   sustained average is lower. (Verified: first call returns `0.0`; it is a
   since-last-call delta, not an instantaneous system load.) The reported "100%" is real
   busy-ness *in that sub-window*, but overstates sustained load.
3. **Logged at WARNING every cycle** → 2,040 lines of noise that bury the 3 real ERRORs.

### Repro — **NOT ATTEMPTED** (requires prod-scale state)
Reproducing the sustained readings needs ~3900 real guilds + populated DB; can't be
faithfully reproduced locally. Layers 2 and 3 were verified by reading `psutil` behavior
and the code path.

### Suggested next steps
- **Noise:** drop the critical-throttle line to `DEBUG` (or log once per run with a
  count + peak), matching the normal-throttle line already at DEBUG (`scheduling.py:79`).
- **Metric accuracy:** sample with a real interval on a cheaper cadence, or use
  `psutil.getloadavg()` / per-process `Process().cpu_percent()`, so throttling reacts to
  sustained load rather than sub-window spikes.
- **Architecture (the actual fix):** the per-guild synchronous `Server(...)` construction
  every 15 min is the cost driver. Batch the DB reads (one query for all guilds' settings
  per cycle) and/or offload to a worker, and only touch guilds with due birthday/
  maintenance work instead of all of them. Tracked under the scale assessment.

---

## Issue 4 — HTTP 404 WARNING flood (3,402×)

**Signature:** `WARNING - _handle_http_response_errors - Path (...) resulted in error 404, check your path?`
Emitted by **nextcord's own HTTP layer** *before* it raises `NotFound`, which InfiniBot
then catches. So these are **handled** failures — the WARNING is library-level noise, not
an unhandled error.
**Severity:** Low-Medium (no functional impact, but 3,402 lines/day obscure real issues).

### Root cause (confirmed)
- **member (2,556):** `get_member` → `guild.fetch_member` for authors of edited messages
  who aren't cached members (left the guild, webhook/app authors, uncached users). The
  fetch 404s, `get_member` catches `NotFound` and caches it. Working as designed — just
  loud.
- **message (693):** `get_message` → `fetch_message` for messages deleted between the
  raw event and the fetch. Caught (`utils.py:824`).
- **channel (153):** channel fetches for deleted/invisible channels. Caught.
- **Cache TTL too short:** `failed_member_fetches = ExpiringSet(60*1)` — **1 minute**
  (`utils.py:828`). One member ID (`1297653417329692682`) 404'd **735 times** in 24 h
  because any edit >60 s after the last one re-fetches and re-404s. 150 distinct member
  IDs produced the 2,556 member-404s; the cache is doing little for chronic repeaters.

### Repro — **NOT ATTEMPTED** (behavioral / not a defect)
No failing behavior to reproduce; this is handled control flow plus a tuning opportunity.

### Suggested next steps
- These 404 WARNINGs originate in `nextcord`, so raise its logger threshold, e.g.
  `logging.getLogger("nextcord.http").setLevel(logging.ERROR)`, to silence handled misses
  while keeping genuine errors. (Confirm the logger name in this nextcord build first.)
- Raise `failed_member_fetches` TTL (e.g. 15–60 min) to actually suppress repeat fetches
  for known-absent members; the memory cost is trivial and it cuts REST traffic.

---

## Issue 5 — `403` on role removal / channel fetch (3×)

`403` on `DELETE /guilds/{}/members/{}/roles/{}` (2×, `leveling.py:480` level-reward role
removal) and `GET /channels/{}` (1×). **Root cause:** InfiniBot lacks *Manage Roles* / the
role is above its highest role, or it can't view the channel. These are handled (logged as
WARNING by the HTTP layer). **Severity:** Low. **Next step:** confirm the level-reward path
surfaces a "missing permissions" notice to the server owner (the reaction-roles path
already has `MISSING_PERMISSIONS_MESSAGE`); no code defect.

## Issue 6 — `add_roles_for_new_member`: role not found (1×)

`Role 1461046582769352932 was not found in guild Caracal Chaos 2.0 ... Skipping`.
**Root cause:** a configured default/auto-role was deleted from the guild but not from
InfiniBot's config. Already handled gracefully (skips). **Severity:** Low. **Next step:**
optional — prune deleted roles from the guild's default-role config on `on_guild_role_delete`
so the warning stops recurring.

## Issue 7 — join-to-create: `400 Target user is not connected to voice` (1×)

`run_join_to_create_vc_member_update` tried to move a member who had already left voice.
**Root cause:** classic TOCTOU race between the voice-state event and the move call.
**Severity:** Low (single occurrence, handled). **Next step:** treat error code `40032` as
a benign no-op rather than surfacing it.

## Issue 8 — `ack`: shard 1 websocket 10.1s behind (2×)

Two consecutive heartbeat-lag warnings at 14:25. **Root cause:** event-loop stall — most
likely the same CPU saturation as Issue 3 blocking the loop long enough to delay heartbeat
acks. **Severity:** Low (transient, recovered). Resolving Issue 3's synchronous work would
also relieve this.

## Issue 9 — PyNaCl not installed (boot, 1×)

`WARNING - __init__ - PyNaCl is not installed, voice will NOT be supported`. **Intentional**
— InfiniBot doesn't use voice audio. Informational only.

---

## Recommended priority order

1. **Issue 1** — fix the `communication_disabled_until` race (snapshot once). Small, safe,
   prevents dropped moderation-audit logs. Repro passes.
2. **Issue 2** — add `HTTPException` handling to `get_member` to match `get_message`. Small,
   safe, one-line. Repro passes.
3. **Issue 3 (noise)** — demote the critical-throttle log to DEBUG / summarize per run;
   immediately makes the logs readable.
4. **Issue 4 (noise + tuning)** — quiet nextcord's handled-404 WARNINGs and lengthen the
   failed-member-fetch TTL.
5. **Issue 3 (architecture)** — batch the scheduler's per-guild DB work; ties into the
   existing scale-assessment effort.
6. Issues 5–9 — optional hardening; none are process-affecting.
