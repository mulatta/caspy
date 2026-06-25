# caspy

A light, general-purpose **content-addressable store** with the hashing,
atomic-IO, and memoization primitives that go with it.

- Algorithm-tagged digests (`sha256:…`, `blake3:…`); stdlib `sha256` core,
  `blake3` as an optional extra (`caspy[blake3]`).
- Filesystem-as-index (no database); lock-free concurrent put/get via atomic
  rename.
- A `KeyedCache` for memoizing a computation on a key derived from its inputs.

Usage docs follow once
the API has been exercised by a real consumer.
