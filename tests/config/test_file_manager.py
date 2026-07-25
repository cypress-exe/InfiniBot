"""
Tests for :mod:`config.file_manager`.

The old harness covered all of this in a single ``test_json_file`` that created,
read, mutated, re-read and deleted a file in one flow — so a failure anywhere in
it reported only "test_json_file failed". These split it by behavior.
"""

from __future__ import annotations

import os

import pytest

from config.file_manager import JSONFile


@pytest.fixture
def json_file() -> JSONFile:
    """An empty JSONFile in the sandboxed configure directory."""
    return JSONFile("test_file")


def test_file_name_gets_the_json_extension(json_file: JSONFile) -> None:
    assert json_file.file_name == "test_file.json"


def test_added_variables_read_back(json_file: JSONFile) -> None:
    json_file.add_variable("bool1", True)
    json_file.add_variable("bool2", False)

    assert json_file["bool1"] is True
    assert json_file["bool2"] is False


def test_dotted_keys_create_nested_structures(json_file: JSONFile) -> None:
    json_file.add_variable("parent.string1", "Hello World")

    assert json_file["parent.string1"] == "Hello World"
    assert json_file["parent"]["string1"] == "Hello World"


def test_len_counts_top_level_keys(json_file: JSONFile) -> None:
    json_file.add_variable("bool1", True)
    json_file.add_variable("bool2", False)
    json_file.add_variable("bool3", True)
    json_file.add_variable("parent.string1", "Hello World")

    # "parent" counts once, not once per child.
    assert len(json_file) == 4


def test_writes_persist_to_disk_for_a_new_instance(json_file: JSONFile) -> None:
    """The point of JSONFile: a second instance sees the first one's writes."""
    json_file.add_variable("bool1", True)
    json_file.add_variable("bool2", False)
    json_file.add_variable("parent.string1", "Hello World")

    json_file["bool2"] = True
    json_file["parent.string1"] = "Goodbye World"

    reopened = JSONFile("test_file")

    assert reopened["bool1"] is True
    assert reopened["bool2"] is True
    assert reopened["parent.string1"] == "Goodbye World"
    assert reopened["parent"]["string1"] == "Goodbye World"


def test_iteration_yields_top_level_keys(json_file: JSONFile) -> None:
    json_file.add_variable("bool1", True)
    json_file.add_variable("bool2", False)
    json_file.add_variable("parent.string1", "Hello World")

    assert sorted(json_file) == ["bool1", "bool2", "parent"]


def test_delete_file_removes_it_from_disk(json_file: JSONFile) -> None:
    json_file.add_variable("bool1", True)
    path = json_file.path
    assert os.path.exists(path)

    json_file.delete_file()

    assert not os.path.exists(path)
