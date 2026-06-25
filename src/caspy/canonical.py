"""Canonical JSON serialization for deterministic hashing."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def canonical_json(data: Any, *, default: Callable[[Any], Any] | None = None) -> bytes:
    """Serialize ``data`` to deterministic UTF-8 JSON bytes.

    Sorted keys and compact separators make output stable regardless of dict
    insertion order, so hashing it yields a content identity. ``NaN``/``Infinity``
    are rejected — invalid JSON that would not round-trip.

    ``default`` is forwarded to :func:`json.dumps` for values JSON cannot encode
    (``Path``, numpy scalars, …) and must return a JSON-native replacement. It
    must be deterministic — equal inputs to equal replacements — or the
    stable-identity guarantee is lost.
    """
    text = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=default,
    )
    return text.encode("utf-8")
