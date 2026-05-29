from __future__ import annotations

import hashlib
import json
import logging
import tempfile
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from . import __version__
from .errors import DictionaryNormalizerError
from .manifest import Manifest, SourceConfig
from .normalizer import DEFAULT_SETTINGS, load_blocklist, normalize_words
from .parsers import parse_source
from .validator import (
    blocklist_version_hash,
    dictionary_version_hash,
    encode_blocked_token,
    validate_artifact,
)

SCHEMA_VERSION = 1
DEFAULT_DICTIONARY_VERSION = 1
DEFAULT_BLOCKLIST_VERSION = 1
DEFAULT_DICTIONARY_LABEL = "hoststamp-dictionary-v1"
DEFAULT_BLOCKLIST_LABEL = "server-name-safety-v1"
SERVER_BLOCKLIST_SOURCE_ID = "hoststamp-server-name-blocklist"
SQIDS_BLOCKLIST_SOURCE_ID = "sqids-default-blocklist"
SQIDS_BLOCKLIST_RESOURCE = "sqids-default-blocklist-0.4.2.txt"
ALLOWED_DOWNLOAD_SCHEMES = {"https", "file"}
MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024
logger = logging.getLogger(__name__)
BlocklistSources = dict[str, list[str]]


def build_artifact(
    input_dir: Path,
    manifest: Manifest,
    *,
    refresh: bool = False,
    released_hashes: dict[str, Any] | None = None,
    generated: str | None = None,
) -> dict[str, Any]:
    if refresh:
        refresh_sources(input_dir, manifest)

    blocklist_version_sources: dict[int, BlocklistSources] = {
        DEFAULT_BLOCKLIST_VERSION: {
            SERVER_BLOCKLIST_SOURCE_ID: normalize_words(
                sorted(load_blocklist()), settings=DEFAULT_SETTINGS
            ),
            SQIDS_BLOCKLIST_SOURCE_ID: load_sqids_blocklist(),
        }
    }
    blocked_tokens = blocked_word_table(blocklist_version_sources)
    blocked_token_ids = {token: index for index, token in enumerate(blocked_tokens)}
    dictionary_v1_excluded_words = alpha_tokens(
        blocklist_version_sources[DEFAULT_BLOCKLIST_VERSION]
    )
    category_words: dict[str, set[str]] = defaultdict(set)
    category_source_ids: dict[str, list[str]] = defaultdict(list)
    source_records: dict[str, dict[str, Any]] = blocklist_source_records()

    for source in manifest.sources:
        if not source.enabled:
            continue

        source_path = source_path_under(input_dir, source)
        if not source_path.exists():
            raise DictionaryNormalizerError(f"{source.id}: input file not found: {source_path}")

        raw_sha256 = sha256_file(source_path)
        if source.expected_sha256 and raw_sha256 != source.expected_sha256:
            raise DictionaryNormalizerError(
                f"{source.id}: sha256 mismatch for {source.path}: "
                f"expected {source.expected_sha256}, got {raw_sha256}"
            )

        raw_words = parse_source(source_path, source.parser_kind, array=source.array)
        words = normalize_words(
            raw_words,
            settings=DEFAULT_SETTINGS,
            drop_words=set(source.drop_words),
        )

        if words:
            category_words[source.category].update(
                word for word in words if word not in dictionary_v1_excluded_words
            )
            category_source_ids[source.category].append(source.id)

        source_records[source.id] = source_record(source, raw_sha256)

    allowed_words = sorted(set().union(*category_words.values()))
    allowed_word_ids = {word: index for index, word in enumerate(allowed_words)}
    categories = {
        category: [allowed_word_ids[word] for word in sorted(words)]
        for category, words in sorted(category_words.items())
        if words
    }
    dictionary_sources = sorted(
        {
            source_id
            for source_ids in category_source_ids.values()
            for source_id in source_ids
            if source_id in source_records
        }
    )
    dictionary_version = {
        "label": DEFAULT_DICTIONARY_LABEL,
        "sources": dictionary_sources,
        "categories": categories,
    }
    dictionary_version["hash"] = dictionary_version_hash(
        DEFAULT_DICTIONARY_VERSION,
        DEFAULT_DICTIONARY_LABEL,
        dictionary_sources,
        {category: sorted(words) for category, words in sorted(category_words.items()) if words},
    )

    blocklist_sources = blocklist_source_ids(
        blocklist_version_sources[DEFAULT_BLOCKLIST_VERSION],
        blocked_token_ids,
    )
    blocklist_version = {
        "label": DEFAULT_BLOCKLIST_LABEL,
        "sources": blocklist_sources,
    }
    blocklist_version["hash"] = blocklist_version_hash(
        DEFAULT_BLOCKLIST_VERSION,
        DEFAULT_BLOCKLIST_LABEL,
        {
            source_id: [blocked_tokens[token_id] for token_id in token_ids]
            for source_id, token_ids in blocklist_sources.items()
        },
    )

    if generated is None:
        generated = generated_timestamp()
    artifact: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated": generated,
        "generator": f"dictionary-normalizer {__version__}",
        "normalization": DEFAULT_SETTINGS.as_json(),
        "default_dictionary_version": DEFAULT_DICTIONARY_VERSION,
        "default_blocklist_version": DEFAULT_BLOCKLIST_VERSION,
        "words": {
            "allowed": allowed_words,
            "blocked": [encode_blocked_token(token) for token in blocked_tokens],
        },
        "dictionary_versions": {
            str(DEFAULT_DICTIONARY_VERSION): dictionary_version,
        },
        "blocklist_versions": {
            str(DEFAULT_BLOCKLIST_VERSION): blocklist_version,
        },
        "sources": dict(sorted(source_records.items())),
    }
    validate_artifact(artifact, released_hashes=released_hashes)
    return artifact


def generated_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_artifact(path: Path, artifact: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_artifact(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise DictionaryNormalizerError(f"{path}: artifact must be a JSON object")
    return data


def refresh_sources(input_dir: Path, manifest: Manifest) -> None:
    enabled_sources = [source for source in manifest.sources if source.enabled]
    missing = [
        source.id
        for source in enabled_sources
        if source.refreshable and source.download_url is None
    ]
    if missing:
        raise DictionaryNormalizerError(
            "--refresh requires download_url for every refreshable source; missing: "
            + ", ".join(missing)
        )

    for source in enabled_sources:
        if not source.refreshable:
            logger.info("skipping non-refreshable source %s", source.id)
            continue
        if source.download_url is None:
            raise DictionaryNormalizerError(f"{source.id}: missing download_url")
        validate_download_url(source)
        target = source_path_under(input_dir, source)
        target.parent.mkdir(parents=True, exist_ok=True)
        download_to_tempfile(source, target)


def source_record(source: SourceConfig, sha256: str) -> dict[str, Any]:
    return {
        "title": source.title,
        "url": source.url,
        "retrieved": source.retrieved,
        "sha256": sha256,
        "license": source.license,
        "license_url": source.license_url,
        "attribution": source.attribution,
        "changes": source.changes,
        "notice_required": source.notice_required,
    }


def blocklist_source_records() -> dict[str, dict[str, Any]]:
    return {
        SERVER_BLOCKLIST_SOURCE_ID: {
            "title": "Hoststamp server-name safety blocklist",
            "url": "https://github.com/hoststamp/hoststamp",
            "retrieved": "2026-05-24",
            "sha256": sha256_resource("blocked-server-words.txt"),
            "license": "MIT",
            "license_url": "https://opensource.org/license/mit",
            "attribution": "hoststamp contributors",
            "changes": "normalized as lowercase base36 tokens; base64url-encoded in artifact",
            "notice_required": False,
        },
        SQIDS_BLOCKLIST_SOURCE_ID: {
            "title": "Sqids default blocklist",
            "url": "https://github.com/sqids/sqids-rust/blob/v0.4.2/src/blocklist.json",
            "retrieved": "2026-05-24",
            "sha256": sha256_resource(SQIDS_BLOCKLIST_RESOURCE),
            "license": "MIT",
            "license_url": "https://opensource.org/license/mit",
            "attribution": "Sqids maintainers",
            "changes": (
                "extracted from pinned sqids 0.4.2 blocklist.json; base64url-encoded in artifact"
            ),
            "notice_required": True,
        },
    }


def load_sqids_blocklist() -> list[str]:
    data = resources.files("dictionary_normalizer").joinpath(f"data/{SQIDS_BLOCKLIST_RESOURCE}")
    tokens = [
        line.strip().lower()
        for line in data.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    return sorted(set(tokens))


def blocked_word_table(blocklist_versions: dict[int, BlocklistSources]) -> list[str]:
    return sorted(
        {
            token
            for sources in blocklist_versions.values()
            for tokens in sources.values()
            for token in tokens
        }
    )


def alpha_tokens(blocklist_sources: BlocklistSources) -> set[str]:
    return {token for tokens in blocklist_sources.values() for token in tokens if token.isalpha()}


def blocklist_source_ids(
    blocklist_sources: BlocklistSources, blocked_token_ids: dict[str, int]
) -> dict[str, list[int]]:
    return {
        source_id: [blocked_token_ids[token] for token in tokens if token in blocked_token_ids]
        for source_id, tokens in blocklist_sources.items()
    }


def sha256_resource(name: str) -> str:
    data = resources.files("dictionary_normalizer").joinpath(f"data/{name}")
    return hashlib.sha256(data.read_bytes()).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_path_under(input_dir: Path, source: SourceConfig) -> Path:
    input_root = input_dir.resolve()
    source_path = (input_root / source.path).resolve()
    if not source_path.is_relative_to(input_root):
        raise DictionaryNormalizerError(f"{source.id}: path escapes input directory: {source.path}")
    return source_path


def validate_download_url(source: SourceConfig) -> None:
    download_url = source.download_url
    if download_url is None:
        raise DictionaryNormalizerError(f"{source.id}: missing download_url")
    scheme = urlsplit(download_url).scheme.lower()
    if scheme not in ALLOWED_DOWNLOAD_SCHEMES:
        raise DictionaryNormalizerError(
            f"{source.id}: unsupported download_url scheme: {scheme or '<none>'}"
        )


def download_to_tempfile(source: SourceConfig, target: Path) -> str:
    download_url = source.download_url
    if download_url is None:
        raise DictionaryNormalizerError(f"{source.id}: missing download_url")
    digest = hashlib.sha256()
    total = 0
    temp_path: Path | None = None
    try:
        # file:// is intentionally allowed for deterministic local refresh tests.
        with urllib.request.urlopen(download_url, timeout=30) as response:
            final_scheme = urlsplit(response.geturl()).scheme.lower()
            if final_scheme not in ALLOWED_DOWNLOAD_SCHEMES:
                raise DictionaryNormalizerError(
                    f"{source.id}: unsupported redirected download_url scheme: "
                    f"{final_scheme or '<none>'}"
                )
            with tempfile.NamedTemporaryFile("wb", delete=False, dir=target.parent) as temp:
                temp_path = Path(temp.name)
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        raise DictionaryNormalizerError(
                            f"{source.id}: download exceeds {MAX_DOWNLOAD_BYTES} bytes"
                        )
                    digest.update(chunk)
                    temp.write(chunk)
    except DictionaryNormalizerError:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise DictionaryNormalizerError(f"{source.id}: download failed: {exc}") from exc

    if temp_path is None:
        raise DictionaryNormalizerError(f"{source.id}: download did not produce a file")
    actual_sha256 = digest.hexdigest()
    if actual_sha256 != source.expected_sha256:
        temp_path.unlink(missing_ok=True)
        raise DictionaryNormalizerError(
            f"{source.id}: downloaded sha256 mismatch: "
            f"expected {source.expected_sha256}, got {actual_sha256}"
        )
    temp_path.replace(target)
    return actual_sha256
