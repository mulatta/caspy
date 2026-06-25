"""A content-addressed blob store.

Blobs are immutable and named by their content digest, which maps deterministically
to a sharded path (``root/<algorithm>/<ab>/<cd>/<hexdigest>``) — so the filesystem
is the index (no database) and identical content deduplicates. Writes go through a
temp file + atomic rename, so concurrent ``put``/``get`` need no locks.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import IO, Any

from caspy.atomic import write_atomic
from caspy.canonical import canonical_json
from caspy.digest import Digest
from caspy.hashing import hash_bytes, hash_file


class Store:
    def __init__(
        self,
        root: Path | str,
        *,
        algorithm: str = "sha256",
        fanout: int = 2,
        depth: int = 2,
    ) -> None:
        self.root = Path(root)
        self.algorithm = algorithm
        self._fanout = fanout
        self._depth = depth

    # --- locating ---------------------------------------------------------

    def path_for(self, digest: Digest) -> Path:
        """The on-disk path a blob with ``digest`` has (or would have)."""
        hexdigest = digest.hexdigest
        shards = [
            hexdigest[i * self._fanout : (i + 1) * self._fanout]
            for i in range(self._depth)
        ]
        return self.root.joinpath(digest.algorithm, *shards, hexdigest)

    def exists(self, digest: Digest) -> bool:
        return self.path_for(digest).is_file()

    __contains__ = exists

    # --- writing ----------------------------------------------------------

    def put_bytes(self, data: bytes) -> Digest:
        digest = hash_bytes(data, algorithm=self.algorithm)
        target = self.path_for(digest)
        if not target.is_file():  # immutable + content-addressed -> skip rewrite
            write_atomic(target, data)
        return digest

    def put_json(self, data: Any) -> Digest:
        return self.put_bytes(canonical_json(data))

    def put_file(self, path: Path | str, *, move: bool = False) -> Digest:
        """Store a file's content. ``move=True`` consumes the source."""
        source = Path(path)
        digest = hash_file(source, algorithm=self.algorithm)
        target = self.path_for(digest)
        if target.is_file():
            if move:
                source.unlink()
            return digest
        target.parent.mkdir(parents=True, exist_ok=True)
        if move:
            try:
                os.replace(source, target)  # atomic rename, same filesystem
                return digest
            except OSError:
                pass  # cross-device; fall back to copy
        fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".put.", suffix=".tmp")
        os.close(fd)
        try:
            shutil.copyfile(source, tmp)
            os.replace(tmp, target)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        if move:
            source.unlink()
        return digest

    # --- reading ----------------------------------------------------------

    def get_bytes(self, digest: Digest) -> bytes:
        try:
            return self.path_for(digest).read_bytes()
        except FileNotFoundError:
            raise KeyError(str(digest)) from None

    def open(self, digest: Digest) -> IO[bytes]:
        try:
            return open(self.path_for(digest), "rb")
        except FileNotFoundError:
            raise KeyError(str(digest)) from None

    def verify(self, digest: Digest) -> bool:
        """Re-hash the stored blob and check it matches its digest."""
        path = self.path_for(digest)
        if not path.is_file():
            return False
        return hash_file(path, algorithm=digest.algorithm) == digest

    # --- removing & listing ----------------------------------------------

    def delete(self, digest: Digest) -> bool:
        path = self.path_for(digest)
        if not path.is_file():
            return False
        path.unlink()
        return True

    def __iter__(self) -> Iterator[Digest]:
        if not self.root.is_dir():
            return
        for algorithm_dir in self.root.iterdir():
            if not algorithm_dir.is_dir():
                continue
            for blob in algorithm_dir.rglob("*"):
                if blob.is_file() and not blob.name.endswith(".tmp"):
                    yield Digest(algorithm_dir.name, blob.name)

    def __len__(self) -> int:
        return sum(1 for _ in self)


def open_store(root: Path | str, **kwargs: Any) -> Store:
    """Convenience constructor: ``open_store(path, algorithm="blake3")``."""
    return Store(root, **kwargs)
