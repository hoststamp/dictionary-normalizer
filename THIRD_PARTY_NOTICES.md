# Third-Party Notices

The dictionary-normalizer source code is licensed under the MIT License. The
input word sources and generated dictionary artifacts include normalized data
derived from third-party sources that retain their original licenses.

`sources.toml` is the authoritative machine-readable source manifest. It records
each source file, upstream URL, retrieval date, expected SHA-256, license,
attribution, and normalization notes.

## Sources Requiring Notice

### golang-petname

- License: Apache-2.0
- Attribution: Dustin Kirkland
- Upstream: https://github.com/dustinkirkland/golang-petname
- Local license text: `input/petname/LICENSE`
- Sources: `petname-adjectives`, `petname-adverbs`, `petname-animals`

### Docker/Moby Name Generator

- License: Apache-2.0
- Attribution: Docker, Inc. and Moby contributors
- Upstream: https://github.com/moby/moby/tree/v24.0.7/pkg/namesgenerator
- Local license text: `input/docker-moby/LICENSE`
- Local notice text: `input/docker-moby/NOTICE`
- Sources: `docker-moby-adjectives`, `docker-moby-scientists`

### haikunatorgo

- License: BSD-3-Clause
- Attribution: Atrox
- Upstream: https://github.com/Atrox/haikunatorgo
- Local license text: `input/haikunator/LICENSE`
- Sources: `haikunator-adjectives`, `haikunator-nouns`

### EFF Diceware Wordlists

- License: CC-BY-3.0-US
- Attribution: Joseph Bonneau
- Upstream: https://www.eff.org/dice
- Sources: `eff-large`, `eff-short-1`, `eff-short-2`

### Sqids Default Blocklist

- License: MIT
- Attribution: Sqids maintainers
- Upstream: https://github.com/sqids/sqids-rust/blob/v0.4.2/src/blocklist.json
- Source: `sqids-default-blocklist`

## Other Sources

The manifest also includes CC0-1.0, public-domain, and factual sources that do
not require the same notice handling, but they are still attributed in
`sources.toml` and in generated artifacts.
