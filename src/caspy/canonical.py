"""Canonical JSON serialization for deterministic hashing."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def canonical_json(data: Any, *, default: Callable[[Any], Any] | None = None) -> bytes:
    """Serialize ``data`` to deterministic UTF-8 JSON bytes.

    Sorted keys and compact separators make the output stable regardless of dict
    insertion order, so hashing it yields a content identity. ``NaN``/``Infinity``
    are rejected — they are not valid JSON and would not round-trip.

    ``default`` is forwarded to :func:`json.dumps`: it is called for values JSON
    cannot encode (``Path``, numpy scalars, dataclasses, …) and must return a
    JSON-native replacement, so callers can canonicalize their own types without
    reimplementing this function. It must be deterministic — returning equal
    replacements for equal inputs — or the stable-identity guarantee is lost.
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
