"""Versioned JSON loading and migration."""

from __future__ import annotations

import json

import pytest

from caspy import SchemaVersionError, load_versioned_json, write_json_atomic


def _write(path, obj):
    write_json_atomic(path, obj)
    return path


def test_loads_current_version_without_migration(tmp_path):
    path = _write(tmp_path / "r.json", {"schema_version": 2, "x": 1})
    assert load_versioned_json(path, current_version=2) == {
        "schema_version": 2,
        "x": 1,
    }


def test_migrates_through_a_chain(tmp_path):
    path = _write(tmp_path / "r.json", {"schema_version": 1, "name": "a"})

    def v1_to_v2(d):
        return {"schema_version": 2, "label": d["name"]}

    def v2_to_v3(d):
        return {"schema_version": 3, "label": d["label"].upper()}

    out = load_versioned_json(
        path, current_version=3, migrations={1: v1_to_v2, 2: v2_to_v3}
    )
    assert out == {"schema_version": 3, "label": "A"}


def test_missing_version_is_error(tmp_path):
    path = _write(tmp_path / "r.json", {"x": 1})
    with pytest.raises(SchemaVersionError, match="missing or non-integer"):
        load_versioned_json(path, current_version=1)


def test_no_migration_path_is_error(tmp_path):
    path = _write(tmp_path / "r.json", {"schema_version": 1})
    with pytest.raises(SchemaVersionError, match="no migration from version 1"):
        load_versioned_json(path, current_version=2)


def test_newer_than_supported_is_error(tmp_path):
    path = _write(tmp_path / "r.json", {"schema_version": 5})
    with pytest.raises(SchemaVersionError, match="newer than supported"):
        load_versioned_json(path, current_version=2)


def test_migration_must_advance_version(tmp_path):
    path = _write(tmp_path / "r.json", {"schema_version": 1})
    with pytest.raises(SchemaVersionError, match="did not advance"):
        load_versioned_json(path, current_version=2, migrations={1: lambda d: d})


def test_non_object_top_level_is_error(tmp_path):
    path = tmp_path / "r.json"
    path.write_text(json.dumps([1, 2, 3]))
    with pytest.raises(SchemaVersionError, match="must be an object"):
        load_versioned_json(path, current_version=1)
