# Coverage baseline — July 2026

Reproduce with `uv run pytest --cov`.

**13.6% of 11,445 statements** (9,889 untested).

> The number is only meaningful with `include_namespace_packages = true` in
> `[tool.coverage.report]`. `src/` has no `__init__.py` files, so without it
> coverage walks only the modules the tests happened to import and reports 51% —
> counting untested files as absent rather than as 0%.

## Where the gap is

Almost all of it is `src/features/`. The config and database layers are in
reasonable shape; the bot's actual behavior is not covered at all.

Ranked by untested statements, which is where a test buys the most:

| Module | Stmts | Untested | Cover |
|---|---:|---:|---:|
| `src/features/dashboard.py` | 3000 | 3000 | 0% |
| `src/features/admin_commands.py` | 529 | 529 | 0% |
| `src/features/moderation.py` | 513 | 513 | 0% |
| `src/features/role_messages.py` | 444 | 444 | 0% |
| `src/components/utils.py` | 584 | 436 | 25% |
| `src/features/profile.py` | 403 | 403 | 0% |
| `src/core/bot.py` | 390 | 390 | 0% |
| `src/features/action_logging.py` | 442 | 383 | 13% |
| `src/features/options_menu/editing/role_messages.py` | 373 | 373 | 0% |
| `src/features/jokes.py` | 287 | 287 | 0% |
| `src/features/reaction_roles.py` | 283 | 283 | 0% |
| `src/features/leveling.py` | 281 | 281 | 0% |
| `src/features/options_menu/editing/reaction_roles.py` | 246 | 246 | 0% |
| `src/features/onboarding.py` | 224 | 224 | 0% |
| `src/components/ui_components.py` | 252 | 202 | 20% |
| `src/core/db_manager.py` | 537 | 201 | 63% |
| `src/features/purging.py` | 146 | 146 | 0% |
| `src/core/scheduling.py` | 120 | 120 | 0% |
| `src/features/birthdays.py` | 104 | 104 | 0% |
| `src/core/log_manager.py` | 121 | 100 | 17% |

Everything below `log_manager` is under 100 untested statements each.

## Reasonably covered already

| Module | Cover |
|---|---:|
| `src/config/server.py` | 92% |
| `src/config/messages/stored_messages.py` | 89% |
| `src/modules/database.py` | 89% |
| `src/config/global_settings.py` | 85% |
| `src/modules/custom_types.py` | 82% |
| `src/config/member.py` | 78% |
| `src/config/file_manager.py` | 75% |
| `src/config/messages/cached_messages.py` | 70% |

## Suggested order for closing the gap

Ranked by untested lines alone would say "start with `dashboard.py`". That is
the wrong first move: it is 5,141 lines of interactive UI, the hardest thing
here to test and the least likely to break silently.

Better order, by (likelihood of a silent regression × testability):

1. **`features/moderation.py`** (513) — profanity/spam scoring is pure logic over
   a message and a server config. Easy to test, and a regression here is a
   user-visible false positive on a real server.
2. **`components/utils.py`** (436 untested of 584) — shared helpers called from
   everywhere; already 25% covered, so the fixtures exist.
3. **`features/leveling.py`** (281) — point arithmetic and the anti-spam
   cooldown. Same shape as moderation.
4. **`features/birthdays.py`** (104) and **`core/scheduling.py`** (120) —
   timezone and scheduling arithmetic, which is exactly the sort of thing that
   breaks quietly at a DST boundary.
5. **`features/action_logging.py`** (383 untested) — already has three
   regressions covered; the surrounding embed builders are straightforward.
6. **`features/role_messages.py`** / **`reaction_roles.py`** — split the state
   handling from the UI and test the state handling.
7. `dashboard.py` last, and only the non-UI helpers.

`core/bot.py` (390) and `core/shard_manager.py` (67) are gateway wiring; they
are better served by `src/event_harness.py` than by unit tests.

## Raising the floor

`fail_under` in `[tool.coverage.report]` starts at **13**. Raise it in the same
PR that adds the tests, never in a PR of its own — a floor that fails on
unrelated work gets disabled.
