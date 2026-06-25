"""The hash-algorithm registry.

The core algorithms come from the stdlib (``hashlib``), so caspy has no required
dependencies. Non-stdlib algorithms (``blake3``) register themselves lazily when
first requested, and are only importable if their optional extra is installed.
A hasher is anything ``hashlib``-shaped: ``.update(bytes)`` + ``.hexdigest()``.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from functools import partial
from typing import Protocol


class Hasher(Protocol):
    def update(self, data: bytes, /) -> object: ...

    def hexdigest(self) -> str: ...


_REGISTRY: dict[str, Callable[[], Hasher]] = {}


def register(name: str, factory: Callable[[], Hasher]) -> None:
    """Register a hasher factory under ``name`` (e.g. for a custom algorithm)."""
    _REGISTRY[name] = factory


def available() -> set[str]:
    """Algorithm names currently registered (stdlib built-ins plus any loaded)."""
    return set(_REGISTRY)


def new_hasher(algorithm: str) -> Hasher:
    """A fresh hasher for ``algorithm``; raises if it is unknown/unavailable."""
    if algorithm not in _REGISTRY:
        _try_autoload(algorithm)
    factory = _REGISTRY.get(algorithm)
    if factory is None:
        raise _unavailable(algorithm)
    return factory()


# stdlib built-ins — zero dependency.
for _name in ("sha256", "sha512", "sha3_256", "blake2b", "blake2s"):
    register(_name, partial(hashlib.new, _name))


def _try_autoload(algorithm: str) -> None:
    if algorithm == "blake3":
        try:
            import blake3
        except ModuleNotFoundError:
            return
        register("blake3", blake3.blake3)


def _unavailable(algorithm: str) -> Exception:
    if algorithm == "blake3":
        return ModuleNotFoundError(
            "the 'blake3' algorithm needs its optional dependency; "
            "install caspy[blake3]"
        )
    return ValueError(
        f"unknown hash algorithm {algorithm!r}; available: "
        f"{', '.join(sorted(available()))}"
    )
