# dictionary-normalizer

Standalone Python CLI that normalizes third-party word sources into a single
validated JSON dictionary artifact consumed by `hoststamp`.

## Usage

After installing the package, build an artifact from the checked-in offline
fixtures:

```sh
python3 -m dictionary_normalizer --input input --output output/artifact.json
```

Validate an existing artifact:

```sh
python3 -m dictionary_normalizer --validate output/artifact.json
```

If the released hash lock is not near the artifact or manifest path, pass it
explicitly:

```sh
python3 -m dictionary_normalizer --validate output/artifact.json --released-hashes released-version-hashes.json
```

When installed, the console script is also available:

```sh
dictionary-normalizer
dictionary-normalizer --validate output/artifact.json
```

By default the artifact is written to `output/artifact.json`. That canonical
handoff artifact is committed; other generated contents under `output/` are
ignored.

Refresh sources from upstream:

```sh
dictionary-normalizer --refresh
```

`--refresh` requires every enabled source in `sources.toml` to have a
`download_url`, unless the source is marked `refreshable = false`. Every
download must match the pinned SHA-256. Curated local fixtures such as the
extracted corpora lists and NATO phonetic list are skipped during refresh.
Offline runs do not need network access.

## Development

The runtime package uses only the Python standard library. Optional dev tools
are pinned in `requirements-dev.txt`.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy src
coverage run -m pytest tests
coverage report
```

Coverage is enforced at 95% for the package under `src/`.

## Data Model

This README documents the artifact contract. `sources.toml` is the committed
source manifest. It defines each input file, parser kind, category mapping,
expected SHA-256, license metadata, attribution, and source-specific curation
notes.

The generated JSON shape contains separate `words.allowed` and encoded
`words.blocked` tables, complete `dictionary_versions`, complete
`blocklist_versions`, default version numbers, normalization metadata, and a
source attribution map. Allowed words are lowercase ASCII alphabetic tokens
only: `^[a-z]+$`. Blocked tokens decode to lowercase base36 and are
base64url-encoded without padding in the artifact. The global word tables are
interning tables for version indexes, so future blocklist versions may contain
tokens that also remain in `words.allowed` for older dictionary versions.

Dictionary and blocklist version hashes are deterministic hashes of logical
content, not JSON formatting. Released hashes are pinned in
`released-version-hashes.json`; validation fails if a pinned version changes.
To deliberately inspect the NSFW blocked token list, run
`scripts/decode-blocked-words.py output/artifact.json`.

## Hoststamp Migration Note

Hoststamp should keep this artifact as build-time input. `build.rs` reads and
validates the normalized artifact, then emits generated Rust constants for the
allowed word table, blocked token table, dictionary version indexes, blocklist
version indexes, source attribution metadata, and version hashes.

Profile config should store `dictionary_version`, `blocklist_version`,
category/length settings, and resolved word-pool hashes. Generation resolves
candidate pools by dictionary version, category, and length. It should use the
selected blocklist version's decoded tokens for suffix/Sqids filtering and for
removing blocked candidates from the resolved pool. Old profiles fail closed
only when their selected dictionary/blocklist version hash or resolved pool
hash no longer matches; unrelated new versions do not invalidate them.
