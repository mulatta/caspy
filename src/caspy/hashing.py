"""Hash bytes, files, and canonical JSON into algorithm-tagged digests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from caspy.algorithms import new_hasher
from caspy.canonical import canonical_json
from caspy.digest import Digest

_CHUNK = 1 << 20  # 1 MiB streaming reads keep large files off the heap.


def hash_bytes(data: bytes, *, algorithm: str = "sha256") -> Digest:
    hasher = new_hasher(algorithm)
    hasher.update(data)
    return Digest(algorithm, hasher.hexdigest())


def hash_file(path: Path | str, *, algorithm: str = "sha256") -> Digest:
    """Hash a file's whole content, streamed in chunks."""
    hasher = new_hasher(algorithm)
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK), b""):
            hasher.update(chunk)
    return Digest(algorithm, hasher.hexdigest())


def hash_json(
    data: Any,
    *,
    algorithm: str = "sha256",
    default: Callable[[Any], Any] | None = None,
) -> Digest:
    """Hash the canonical (sorted, compact) JSON encoding of ``data``.

    ``default`` is forwarded to :func:`caspy.canonical.canonical_json` to encode
    values JSON cannot represent natively.
    """
    return hash_bytes(canonical_json(data, default=default), algorithm=algorithm)
