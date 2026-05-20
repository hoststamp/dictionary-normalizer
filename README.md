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
`download_url`, and every download must match the pinned SHA-256. Offline runs
do not need network access.

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

`PROMPT.md` is the authoritative contract. `sources.toml` is the committed source manifest. It defines each input file,
parser kind, category mapping, expected SHA-256, license metadata, attribution,
and source-specific curation notes.

The generated JSON shape is the interchange contract documented in
`PROMPT.md`: `schema_version`, `meta.normalization`, `meta.sources[]`, and
string-keyed `categories` bucketed by word length. Normalized words are
lowercase ASCII alphabetic tokens only: `^[a-z]+$`.
