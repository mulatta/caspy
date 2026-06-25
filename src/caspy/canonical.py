"""Canonical JSON serialization for deterministic hashing."""

from __future__ import annotations

import json
from typing import Any


def canonical_json(data: Any) -> bytes:
    """Serialize ``data`` to deterministic UTF-8 JSON bytes.

    Sorted keys and compact separators make the output stable regardless of dict
    insertion order, so hashing it yields a content identity. ``NaN``/``Infinity``
    are rejected — they are not valid JSON and would not round-trip.
    """
    text = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return text.encode("utf-8")
