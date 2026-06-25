"""Load JSON records whose schema evolves, migrating old versions forward."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


class SchemaVersionError(ValueError):
    """A JSON record's ``schema_version`` could not be brought to the current one."""


def load_versioned_json(
    path: Path | str,
    *,
    current_version: int,
    migrations: Mapping[int, Callable[[dict], dict]] | None = None,
    version_key: str = "schema_version",
) -> dict[str, Any]:
    """Read a JSON object and migrate it up to ``current_version``.

    ``migrations[v]`` upgrades a version-``v`` record to ``v+n`` (it must advance
    ``version_key``). A record newer than ``current_version`` is an error — the
    reader cannot understand the future.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SchemaVersionError(f"{path}: top-level JSON must be an object")

    version = data.get(version_key)
    if not isinstance(version, int):
        raise SchemaVersionError(f"{path}: missing or non-integer {version_key!r}")

    migrations = migrations or {}
    while version < current_version:
        migrate = migrations.get(version)
        if migrate is None:
            raise SchemaVersionError(f"{path}: no migration from version {version}")
        data = migrate(data)
        advanced = data.get(version_key)
        if not isinstance(advanced, int) or advanced <= version:
            raise SchemaVersionError(
                f"{path}: migration from {version} did not advance {version_key}"
            )
        version = advanced

    if version != current_version:
        raise SchemaVersionError(
            f"{path}: version {version} is newer than supported {current_version}"
        )
    return data
