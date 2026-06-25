# caspy

A light, general-purpose **content-addressable store** with the hashing,
atomic-IO, and memoization primitives that go with it.

- **Algorithm-tagged digests** (`sha256:…`, `blake3:…`) — self-describing, so a
  store can hold mixed algorithms and migrate between them.
- **Zero-dependency core** (stdlib `sha256`); `blake3` for large blobs via the
  optional `caspy[blake3]` extra.
- **Filesystem is the index** — no database. Lock-free concurrent `put`/`get`
  via atomic rename.
- **`KeyedCache`** memoizes a computation on a key derived from its *inputs*.
- **Integrity** — blobs are written read-only and can be re-hashed individually
  (`verify`) or store-wide (`validate`).

## Install

```bash
pip install caspy            # stdlib core only
pip install "caspy[blake3]"  # + fast hashing for large files
```

Or as a Nix flake input (`packages.<system>.caspy`, dev shell included).

## Hashing

```python
from caspy import hash_bytes, hash_file, hash_json, Digest

hash_bytes(b"abc")                      # Digest("sha256", "ba78…")
str(hash_file("big.parquet"))           # "sha256:…"  (streamed)
hash_json({"b": 2, "a": 1})             # canonical: key-order independent
hash_file("big.parquet", algorithm="blake3")   # needs caspy[blake3]

Digest.parse("sha256:ba78…")            # round-trips with str(digest)
```

## Atomic writes

```python
from caspy import write_atomic, write_json_atomic

write_atomic("out.txt", "hello")        # temp + fsync + rename; parents created
write_json_atomic("meta.json", {"k": 1})
```

## Content-addressed store

```python
from caspy import Store

store = Store("/data/cas")              # or Store(root, algorithm="blake3")

d = store.put_bytes(b"hello")           # -> Digest; identical content dedups
d = store.put_file("embeddings.parquet")        # copy in
d = store.put_file("staging.bin", move=True)    # consume the source
d = store.put_json({"seed": 0})

store.get_bytes(d)                       # bytes
with store.open(d) as f: ...             # stream
store.exists(d); store.verify(d)         # membership / integrity re-hash
store.validate()                         # whole-store fsck -> corrupted digests
store.delete(d)
for digest in store: ...                 # iterate stored blobs
```

Blobs are written read-only (`0o444`) by default — immutable by contract; pass
`Store(root, read_only=False)` to opt out.

### Store vs. `KeyedCache` — which to use

Both persist bytes by digest, but they answer different questions:

- **`Store`** addresses content by hashing the **output** — identical content
  dedups to one blob. It's an immutable, verifiable record. Reach for it when the
  bytes must persist as a fact you can re-hash and audit later, independent of how
  (or whether) they could be reproduced.
- **`KeyedCache`** maps a key derived from a computation's **inputs** to its
  output. Reach for it to skip recomputation when the same inputs recur; an entry
  is a disposable shortcut — if its blob is gone, that's just a miss and you
  recompute.

In short: a `Store` entry is bytes worth keeping; a `KeyedCache` entry is bytes
worth not recomputing. (A `KeyedCache` is backed by a `Store`, so the two compose.)

## Keyed cache (memoization)

Key on a computation's **inputs**, store its **output**:

```python
from caspy import KeyedCache, hash_json, hash_file

cache = KeyedCache("/data/cache")

key = hash_json({
    "argv": ["embed", "--model", "esm2"],
    "inputs": [str(hash_file("candidates.fasta"))],
    "config": {"seed": 0, "dtype": "float32"},
})

# run the expensive step only on a miss:
result = cache.get_or_compute(key, lambda: run_embedding())   # bytes
```

A dangling pointer (its blob was evicted) is treated as a miss and recomputes.

## Versioned JSON

```python
from caspy import load_versioned_json, SchemaVersionError

data = load_versioned_json(
    "manifest.json",
    current_version=3,
    migrations={1: v1_to_v2, 2: v2_to_v3},   # each must advance schema_version
)
```
