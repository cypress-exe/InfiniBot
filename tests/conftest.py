"""
Shared pytest fixtures for the InfiniBot suite.

InfiniBot reaches most of its state through module-level globals — base paths in
``config.file_manager`` and ``core.log_manager``, the database in
``core.db_manager``, a singleton cache in ``config.global_settings``, and a
class-level parse cache on ``JSONFile``. Left alone, tests would read and write
the developer's real ``./generated/`` tree and inherit each other's state.

The fixtures here reset all of it per test. That isolation is what lets tests
assert absolute values (row counts, file contents) instead of working around
whatever ran before them, and it is why the old harness's ``random.randint`` IDs
are no longer needed.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import pytest

import config.file_manager as file_manager
import config.global_settings as global_settings
import core.db_manager as db_manager
import core.log_manager as log_manager
from config.file_manager import JSONFile

# Repository root, resolved from this file rather than the working directory so
# pytest works from any cwd.
REPO_ROOT = Path(__file__).resolve().parent.parent

# The real schema the bot ships with.
DB_BUILD_FILE = REPO_ROOT / "resources" / "db_build.sql"

# A small fixture schema (3 tables exercising defaults, tags and composite keys)
# used by tests covering the generic Database machinery itself.
TEST_DB_BUILD_FILE = REPO_ROOT / "resources" / "test_db_build.sql"


@pytest.fixture(autouse=True)
def sandboxed_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    Give each test a private filesystem and a clean set of module caches.

    Autouse: no test should be able to touch the real ``./generated/`` tree by
    forgetting to ask for this. (The old harness wrote into the repo at
    ``./generated/test-files``, which is also how that directory ends up
    root-owned after a Docker run.)
    """
    configure_dir = tmp_path / "configure"
    logs_dir = tmp_path / "logs"
    files_dir = tmp_path / "files"
    for directory in (configure_dir, logs_dir, files_dir):
        directory.mkdir(parents=True, exist_ok=True)

    # The bot copies these out of defaults/ on first boot; several config code
    # paths assume they are present.
    shutil.copy(
        REPO_ROOT / "defaults" / "default_profane_words.txt",
        configure_dir / "default_profane_words.txt",
    )
    shutil.copy(REPO_ROOT / "defaults" / "default_jokes.json", files_dir / "jokes.json")

    original_file_base = file_manager.base_path
    original_log_base = log_manager.base_path

    file_manager.update_base_path(f"{configure_dir}/")
    log_manager.update_base_path(f"{logs_dir}/")

    # JSONFile caches parsed data by absolute path, and global_settings memoizes
    # its singletons. Both outlive a test unless cleared, so a settings change in
    # one test would be visible in the next.
    monkeypatch.setattr(JSONFile, "_cache", {})
    monkeypatch.setattr(global_settings, "_global_setting_singletons", {})

    yield tmp_path

    file_manager.update_base_path(original_file_base)
    log_manager.update_base_path(original_log_base)


@pytest.fixture
def db(tmp_path: Path, sandboxed_paths: Path):
    """
    Give the test a private, freshly built InfiniBot database.

    Rebuilding costs ~15ms, which buys full isolation: IDs can be reused freely
    across tests and row counts are absolute.

    Yields the ``DatabaseForInfiniBot`` instance, which is also reachable through
    ``db_manager.get_database()`` for code under test that looks it up globally.
    """
    previous_url = db_manager.database_url
    previous_database = db_manager.database

    db_manager.database_url = f"sqlite:///{tmp_path / 'test.db'}"
    db_manager.init_database()

    try:
        yield db_manager.get_database()
    finally:
        database = db_manager.get_database()
        if database is not None:
            database.cleanup()
        db_manager.database_url = previous_url
        db_manager.database = previous_database


@pytest.fixture
def fixture_db():
    """
    A standalone :class:`Database` built from the *fixture* schema
    (``resources/test_db_build.sql``), not InfiniBot's real one.

    For tests covering the generic database machinery — column defaults, tag
    parsing, table indexing — which need a schema of known, stable shape rather
    than whatever the bot currently ships.
    """
    from modules.database import Database

    database = Database("sqlite://", str(TEST_DB_BUILD_FILE))
    try:
        yield database
    finally:
        database.cleanup()


@pytest.fixture(autouse=True)
def quiet_logging(caplog: pytest.LogCaptureFixture) -> None:
    """
    Keep the bot's own logging out of passing tests' output.

    ``caplog`` still captures records at WARNING and above, so tests that assert
    on log output continue to work, and a failure still shows the captured log.
    """
    caplog.set_level(logging.WARNING)
