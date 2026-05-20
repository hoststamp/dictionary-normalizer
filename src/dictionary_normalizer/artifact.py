from __future__ import annotations

import hashlib
import json
import urllib.request
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__
from .errors import DictionaryNormalizerError
from .manifest import Manifest, SourceConfig
from .normalizer import DEFAULT_SETTINGS, bucket_by_length, load_blocklist, normalize_words
from .parsers import parse_source
from .validator import validate_artifact

SCHEMA_VERSION = 1


def build_artifact(input_dir: Path, manifest: Manifest, *, refresh: bool = False) -> dict[str, Any]:
    if refresh:
        refresh_sources(input_dir, manifest)

    blocklist = load_blocklist()
    category_words: dict[str, set[str]] = defaultdict(set)
    category_source_ids: dict[str, list[str]] = defaultdict(list)
    source_records: list[dict[str, Any]] = []

    for source in manifest.sources:
        if not source.enabled:
            continue

        source_path = input_dir / source.path
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
            blocklist=blocklist,
            drop_words=set(source.drop_words),
        )

        if words:
            category_words[source.category].update(words)
            category_source_ids[source.category].append(source.id)

        source_records.append(source_record(source, raw_sha256))

    categories = {
        category: {
            "source_ids": sorted(set(category_source_ids[category])),
            "lengths": bucket_by_length(sorted(words)),
        }
        for category, words in sorted(category_words.items())
        if words
    }

    generated = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    artifact: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "meta": {
            "generated": generated,
            "generator": f"dictionary-normalizer {__version__}",
            "normalization": DEFAULT_SETTINGS.as_json(),
            "sources": source_records,
        },
        "categories": categories,
    }
    validate_artifact(artifact)
    return artifact


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
    missing = [source.id for source in enabled_sources if source.download_url is None]
    if missing:
        raise DictionaryNormalizerError(
            "--refresh requires download_url for every enabled source; missing: "
            + ", ".join(missing)
        )

    for source in enabled_sources:
        assert source.download_url is not None
        target = input_dir / source.path
        target.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(source.download_url, timeout=30) as response:
            payload = response.read()
        digest = hashlib.sha256(payload).hexdigest()
        if digest != source.expected_sha256:
            raise DictionaryNormalizerError(
                f"{source.id}: downloaded sha256 mismatch: "
                f"expected {source.expected_sha256}, got {digest}"
            )
        target.write_bytes(payload)


def source_record(source: SourceConfig, sha256: str) -> dict[str, Any]:
    return {
        "id": source.id,
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
