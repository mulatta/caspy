"""The ``Digest`` value object: an algorithm-tagged content hash."""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEX = re.compile(r"^[0-9a-f]+$")


@dataclass(frozen=True)
class Digest:
    """A content hash plus the algorithm that produced it.

    Rendered as ``"<algorithm>:<hexdigest>"`` (e.g. ``"sha256:9f86d0…"``) so a
    digest is self-describing: the store can hold mixed algorithms unambiguously.
    """

    algorithm: str
    hexdigest: str

    def __post_init__(self) -> None:
        if not self.algorithm or ":" in self.algorithm:
            raise ValueError(f"invalid algorithm: {self.algorithm!r}")
        if not _HEX.match(self.hexdigest):
            raise ValueError(f"hexdigest must be lowercase hex: {self.hexdigest!r}")

    def __str__(self) -> str:
        return f"{self.algorithm}:{self.hexdigest}"

    @classmethod
    def parse(cls, text: str) -> Digest:
        algorithm, sep, hexdigest = text.partition(":")
        if not sep:
            raise ValueError(f"not a digest: {text!r} (expected 'algorithm:hexdigest')")
        return cls(algorithm, hexdigest)
