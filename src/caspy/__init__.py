"""caspy: a light, general-purpose content-addressable store.

Exposes content hashing (algorithm-tagged digests), atomic file writes, a
content-addressed blob store, a keyed cache for memoization, and versioned-JSON
loading.
"""

from __future__ import annotations

from caspy.algorithms import available, register
from caspy.atomic import write_atomic, write_json_atomic
from caspy.cache import KeyedCache
from caspy.digest import Digest
from caspy.hashing import hash_bytes, hash_file, hash_json
from caspy.store import Store, open_store
from caspy.versioned import SchemaVersionError, load_versioned_json

__all__ = [
    "Digest",
    "hash_bytes",
    "hash_file",
    "hash_json",
    "register",
    "available",
    "write_atomic",
    "write_json_atomic",
    "Store",
    "open_store",
    "KeyedCache",
    "load_versioned_json",
    "SchemaVersionError",
]
