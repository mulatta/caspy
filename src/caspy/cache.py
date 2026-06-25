"""A keyed cache: memoize a computation on a key derived from its inputs.

Unlike the :class:`~caspy.store.Store` (which addresses content by hashing the
*output* — dedup), a ``KeyedCache`` maps a key — typically a digest of a
computation's *inputs* (argv, input file digests, config) — to the output stored
in a Store. The key→output pointers are small persisted state (file-as-truth, no
database); the outputs live in the Store and dedup as usual.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import IO

from caspy.atomic import write_atomic
from caspy.digest import Digest
from caspy.hashing import hash_bytes
from caspy.store import Store


class KeyedCache:
    def __init__(
        self,
        root: Path | str,
        *,
        store: Store | None = None,
        algorithm: str = "sha256",
    ) -> None:
        self.root = Path(root)
        self.store = (
            store
            if store is not None
            else Store(self.root / "blobs", algorithm=algorithm)
        )
        self._keys_dir = self.root / "keys"

    def _pointer_path(self, key: Digest | str) -> Path:
        # Hash the key to a safe, fixed-length, sharded filename.
        name = hash_bytes(
            str(key).encode("utf-8"), algorithm=self.store.algorithm
        ).hexdigest
        return self._keys_dir / name[:2] / name[2:4] / name

    def get(self, key: Digest | str) -> Digest | None:
        """The output digest recorded for ``key``, or None."""
        pointer = self._pointer_path(key)
        if not pointer.is_file():
            return None
        return Digest.parse(pointer.read_text(encoding="utf-8").strip())

    def _record(self, key: Digest | str, digest: Digest) -> Digest:
        write_atomic(self._pointer_path(key), str(digest))
        return digest

    def put(self, key: Digest | str, data: bytes) -> Digest:
        return self._record(key, self.store.put_bytes(data))

    def put_file(
        self, key: Digest | str, path: Path | str, *, move: bool = False
    ) -> Digest:
        return self._record(key, self.store.put_file(path, move=move))

    def get_bytes(self, key: Digest | str) -> bytes | None:
        digest = self.get(key)
        if digest is None:
            return None
        try:
            return self.store.get_bytes(digest)
        except KeyError:
            return None  # stale pointer (blob evicted) -> treat as a miss

    def open(self, key: Digest | str) -> IO[bytes] | None:
        digest = self.get(key)
        if digest is None:
            return None
        try:
            return self.store.open(digest)
        except KeyError:
            return None

    def get_or_compute(self, key: Digest | str, compute: Callable[[], bytes]) -> bytes:
        """Return the cached bytes for ``key``, else compute, store, and return them."""
        cached = self.get_bytes(key)
        if cached is not None:
            return cached
        data = compute()
        self.put(key, data)
        return data
