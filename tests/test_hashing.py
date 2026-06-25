"""Content hashing: digests, algorithm tagging, files, and canonical JSON."""

from __future__ import annotations

import pytest

from caspy import Digest, hash_bytes, hash_file, hash_json
from caspy.algorithms import available, new_hasher

# sha256("") and sha256("abc"), the standard vectors.
_EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
_ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_digest_str_and_parse_roundtrip():
    d = Digest("sha256", _ABC)
    assert str(d) == f"sha256:{_ABC}"
    assert Digest.parse(str(d)) == d


@pytest.mark.parametrize("bad", ["sha256", "", "sha256:", "sha256:XYZ", "a:b:c"])
def test_digest_rejects_malformed(bad):
    with pytest.raises(ValueError):
        Digest.parse(bad)


def test_hash_bytes_known_vectors():
    assert hash_bytes(b"") == Digest("sha256", _EMPTY)
    assert str(hash_bytes(b"abc")) == f"sha256:{_ABC}"


def test_algorithm_is_tagged():
    assert hash_bytes(b"abc", algorithm="sha512").algorithm == "sha512"
    assert hash_bytes(b"abc", algorithm="sha256") != hash_bytes(
        b"abc", algorithm="sha512"
    )


def test_hash_file_matches_hash_bytes(tmp_path):
    payload = b"some bytes\nacross lines\n" * 100_000  # spans several read chunks
    path = tmp_path / "blob.bin"
    path.write_bytes(payload)
    assert hash_file(path) == hash_bytes(payload)


def test_hash_json_is_key_order_independent():
    assert hash_json({"a": 1, "b": 2}) == hash_json({"b": 2, "a": 1})
    assert hash_json({"a": 1}) != hash_json({"a": 2})


def test_unknown_algorithm_raises():
    with pytest.raises(ValueError, match="unknown hash algorithm"):
        new_hasher("not-a-real-algo")


def test_blake3_is_available_and_tagged():
    # blake3 is installed in the dev/check environment (optional extra).
    d = hash_bytes(b"abc", algorithm="blake3")
    assert d.algorithm == "blake3"
    assert "blake3" in available()
    assert d == hash_bytes(b"abc", algorithm="blake3")
    assert d != hash_bytes(b"abd", algorithm="blake3")
