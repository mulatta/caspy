"""The content-addressed blob store."""

from __future__ import annotations

import os

import pytest

from caspy import Digest, hash_bytes, open_store
from caspy.store import Store


def test_put_get_roundtrip_and_dedup(tmp_path):
    store = Store(tmp_path)
    d1 = store.put_bytes(b"hello world")
    d2 = store.put_bytes(b"hello world")
    assert d1 == d2 == hash_bytes(b"hello world")
    assert store.get_bytes(d1) == b"hello world"
    assert len(store) == 1  # identical content stored once


def test_path_layout_is_sharded_and_algorithm_scoped(tmp_path):
    store = Store(tmp_path)
    d = store.put_bytes(b"abc")
    h = d.hexdigest
    assert store.path_for(d) == tmp_path / "sha256" / h[:2] / h[2:4] / h


def test_exists_contains_and_open(tmp_path):
    store = Store(tmp_path)
    d = store.put_bytes(b"data")
    assert store.exists(d) and d in store
    with store.open(d) as handle:
        assert handle.read() == b"data"


def test_missing_blob_raises_keyerror(tmp_path):
    store = Store(tmp_path)
    with pytest.raises(KeyError):
        store.get_bytes(Digest("sha256", "00" * 32))


def test_put_json_is_canonical(tmp_path):
    store = Store(tmp_path)
    assert store.put_json({"a": 1, "b": 2}) == store.put_json({"b": 2, "a": 1})


def test_put_file_copy_and_move(tmp_path):
    store = Store(tmp_path)
    src = tmp_path / "src.bin"
    src.write_bytes(b"payload")

    d = store.put_file(src)  # copy: source preserved
    assert src.exists()
    assert store.get_bytes(d) == b"payload"

    moved = tmp_path / "moved.bin"
    moved.write_bytes(b"payload")
    d2 = store.put_file(moved, move=True)  # move: source consumed
    assert d2 == d
    assert not moved.exists()


def test_put_file_fsyncs_copied_data(tmp_path, monkeypatch):
    # The copy path must fsync the blob before the rename, like write_atomic does;
    # otherwise a crash could expose a renamed-but-not-durable blob.
    synced = []
    real_fsync = os.fsync
    monkeypatch.setattr(os, "fsync", lambda fd: synced.append(fd) or real_fsync(fd))
    store = Store(tmp_path)
    src = tmp_path / "src.bin"
    src.write_bytes(b"durable")
    store.put_file(src)
    assert synced


def test_blobs_are_read_only_by_default(tmp_path):
    store = Store(tmp_path)
    blob = store.path_for(store.put_bytes(b"immutable"))
    assert blob.stat().st_mode & 0o777 == 0o444
    with pytest.raises(PermissionError):
        blob.write_bytes(b"tamper")  # the read-only bit blocks accidental writes


def test_read_only_false_leaves_blobs_writable(tmp_path):
    store = Store(tmp_path, read_only=False)
    blob = store.path_for(store.put_bytes(b"mutable"))
    assert blob.stat().st_mode & 0o200  # owner-writable


def test_delete_works_on_read_only_blobs(tmp_path):
    store = Store(tmp_path)
    d = store.put_bytes(b"x")
    assert store.delete(d) is True  # unlink needs the dir's write bit, not the file's


def test_verify_detects_corruption(tmp_path):
    store = Store(tmp_path)
    d = store.put_bytes(b"trustworthy")
    assert store.verify(d) is True
    blob = store.path_for(d)
    blob.chmod(0o644)  # simulate external corruption (bit-rot / privileged write)
    blob.write_bytes(b"tampered")
    assert store.verify(d) is False


def test_validate_reports_only_corrupted_blobs(tmp_path):
    store = Store(tmp_path)
    good = store.put_bytes(b"healthy")
    bad = store.put_bytes(b"original")
    assert store.validate() == []  # intact store

    blob = store.path_for(bad)
    blob.chmod(0o644)
    blob.write_bytes(b"corrupted")  # external corruption
    assert store.validate() == [bad]
    assert store.verify(good) is True


def test_delete_and_iterate(tmp_path):
    store = Store(tmp_path)
    a = store.put_bytes(b"one")
    b = store.put_bytes(b"two")
    assert set(store) == {a, b}
    assert store.delete(a) is True
    assert store.delete(a) is False
    assert set(store) == {b}


def test_mixed_algorithms_coexist(tmp_path):
    sha = Store(tmp_path, algorithm="sha256")
    blake = Store(tmp_path, algorithm="blake3")
    ds = sha.put_bytes(b"abc")
    db = blake.put_bytes(b"abc")
    assert ds.algorithm == "sha256" and db.algorithm == "blake3"
    assert sha.get_bytes(ds) == blake.get_bytes(db) == b"abc"


def test_open_store_helper(tmp_path):
    store = open_store(tmp_path, algorithm="blake3")
    assert store.algorithm == "blake3"
    assert store.put_bytes(b"x").algorithm == "blake3"
