"""Atomic file writes."""

from __future__ import annotations

import json

from caspy import write_atomic, write_json_atomic


def test_write_atomic_str_and_bytes(tmp_path):
    write_atomic(tmp_path / "a.txt", "hello")
    assert (tmp_path / "a.txt").read_text() == "hello"
    write_atomic(tmp_path / "b.bin", b"\x00\x01\x02")
    assert (tmp_path / "b.bin").read_bytes() == b"\x00\x01\x02"


def test_write_atomic_creates_parents(tmp_path):
    target = tmp_path / "deep" / "nested" / "x.txt"
    write_atomic(target, "ok")
    assert target.read_text() == "ok"


def test_write_atomic_overwrites_and_leaves_no_temp(tmp_path):
    target = tmp_path / "x.txt"
    write_atomic(target, "first")
    write_atomic(target, "second")
    assert target.read_text() == "second"
    assert [p.name for p in tmp_path.iterdir() if p.suffix == ".tmp"] == []


def test_write_json_atomic_roundtrips(tmp_path):
    write_json_atomic(tmp_path / "m.json", {"b": 2, "a": [1, 2, 3]})
    assert json.loads((tmp_path / "m.json").read_text()) == {"a": [1, 2, 3], "b": 2}
