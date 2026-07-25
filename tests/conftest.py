"""
Shared pytest fixtures for the InfiniBot suite.

Two things every test needs and neither should have to arrange itself:

* **A sandboxed filesystem.** ``config.file_manager`` and ``core.log_manager`` both
  read a module-level ``base_path`` that defaults into ``./generated/``. Left alone,
  tests would read and write the developer's real working tree. The session fixture
  below repoints both at a tmpdir and restores them afterwards.

* **An isolated database.** ``core.db_manager`` holds a single module-global
  ``database`` that every config object reaches through ``get_database()``. The
  ``db`` fixture rebuilds it against a fresh file per test, so tests can assert
  absolute row counts instead of working around whatever the previous test left
  behind.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import pytest

import core.db_manager as db_manager
import config.file_manager as file_manager
import core.log_manager as log_manager

# Repository root, resolved from this file rather than the working directory so
# `pytest` works from any cwd.
REPO_ROOT = Path(__file__).resolve().parent.parent

# Built by Database.__init__; the real schema the bot ships with.
DB_BUILD_FILE = REPO_ROOT / "resources" / "db_build.sql"

# A small fixture schema (3 tables exercising defaults, tags and composite keys)
# used by the tests that cover the generic Database machinery itself.
TEST_DB_BUILD_FILE = REPO_ROOT / "resources" / "test_db_build.sql"


@pytest.fixture(scope="session", autouse=True)
def sandboxed_paths(tmp_path_factory: pytest.TempPathFactory):
    """
    Redirect every module-global filesystem path into a session tmpdir.

    Autouse: no test should be able to touch the real ``./generated/`` tree by
    forgetting to ask for this.
    """
    root = tmp_path_factory.mktemp("infinibot")
    configure_dir = root / "configure"
    logs_dir = root / "logs"
    files_dir = root / "files"
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
    original_db_url = db_manager.database_url

    file_manager.update_base_path(f"{configure_dir}/")
    log_manager.update_base_path(f"{logs_dir}/")

    yield root

    file_manager.update_base_path(original_file_base)
    log_manager.update_base_path(original_log_base)
    db_manager.database_url = original_db_url


@pytest.fixture
def db(tmp_path: Path, sandboxed_paths):
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
    parsing, table indexing — which need a schema with known, stable shape rather
    than whatever the bot currently ships.
    """
    from modules.database import Database

    database = Database("sqlite://", str(TEST_DB_BUILD_FILE))
    try:
        yield database
    finally:
        database.cleanup()


@pytest.fixture(autouse=True)
def quiet_logging(caplog):
    """
    Keep the bot's own logging out of passing tests' output.

    ``caplog`` still captures records at WARNING and above, so tests that assert
    on log output continue to work; failures still show the captured log.
    """
    caplog.set_level(logging.WARNING)
