"""The keyed cache (memoization)."""

from __future__ import annotations

from caspy import KeyedCache, hash_json
from caspy.store import Store


def test_put_get_roundtrip(tmp_path):
    cache = KeyedCache(tmp_path)
    key = hash_json({"argv": ["embed"], "seed": 0})
    digest = cache.put(key, b"result")
    assert cache.get(key) == digest
    assert cache.get_bytes(key) == b"result"


def test_get_miss_is_none(tmp_path):
    cache = KeyedCache(tmp_path)
    assert cache.get("never-stored") is None
    assert cache.get_bytes("never-stored") is None
    assert cache.open("never-stored") is None


def test_get_or_compute_runs_once(tmp_path):
    cache = KeyedCache(tmp_path)
    calls = []

    def compute() -> bytes:
        calls.append(1)
        return b"expensive"

    assert cache.get_or_compute("k", compute) == b"expensive"
    assert cache.get_or_compute("k", compute) == b"expensive"
    assert len(calls) == 1  # second call hit the cache


def test_string_and_digest_keys_both_work(tmp_path):
    cache = KeyedCache(tmp_path)
    cache.put("plain-string", b"a")
    cache.put(hash_json({"x": 1}), b"b")
    assert cache.get_bytes("plain-string") == b"a"
    assert cache.get_bytes(hash_json({"x": 1})) == b"b"


def test_put_file(tmp_path):
    cache = KeyedCache(tmp_path)
    src = tmp_path / "out.bin"
    src.write_bytes(b"payload")
    cache.put_file("k", src)
    assert cache.get_bytes("k") == b"payload"


def test_stale_pointer_is_a_miss_and_recomputes(tmp_path):
    cache = KeyedCache(tmp_path)
    digest = cache.put("k", b"v1")
    cache.store.delete(digest)  # evict the blob, pointer now dangles
    assert cache.get_bytes("k") is None
    assert cache.get_or_compute("k", lambda: b"v2") == b"v2"


def test_shares_an_explicit_store(tmp_path):
    store = Store(tmp_path / "cas")
    cache = KeyedCache(tmp_path / "memo", store=store)
    cache.put("k", b"shared")
    assert len(store) == 1
