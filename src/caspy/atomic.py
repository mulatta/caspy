"""Crash-safe file writes: a reader never sees a half-written file."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def write_atomic(
    path: Path | str,
    data: bytes | str,
    *,
    encoding: str = "utf-8",
    mode: int | None = None,
) -> None:
    """Write ``data`` to ``path`` atomically (temp file in same dir + rename).

    The temp file is fsynced then ``os.replace``d, so a concurrent reader sees
    either the old file or the complete new one, never a partial write. Parent
    dirs are created. ``mode`` sets the final permission bits before the rename
    (e.g. ``0o444`` for read-only).
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = data.encode(encoding) if isinstance(data, str) else data
    fd, tmp = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(tmp, mode)
        os.replace(tmp, target)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def write_json_atomic(
    path: Path | str, data: Any, *, indent: int | None = 2, sort_keys: bool = False
) -> None:
    """Atomically write ``data`` as JSON (human-readable by default).

    For hashing use ``hash_json`` / ``canonical_json``; this is for writing
    records, not for content identity.
    """
    text = json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
    write_atomic(path, text)
