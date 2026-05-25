from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import ManifestError


@dataclass(frozen=True)
class SourceConfig:
    id: str
    title: str
    path: str
    parser_kind: str
    category: str
    url: str
    retrieved: str
    expected_sha256: str
    license: str
    license_url: str
    attribution: str
    changes: str
    notice_required: bool
    enabled: bool = True
    refreshable: bool = True
    array: str | None = None
    download_url: str | None = None
    drop_words: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Manifest:
    sources: tuple[SourceConfig, ...]


def load_manifest(path: Path) -> Manifest:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ManifestError(f"{path}: invalid TOML: {exc}") from exc

    raw_sources = data.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ManifestError(f"{path}: expected at least one [[sources]] entry")

    sources = tuple(_source_from_toml(index, raw) for index, raw in enumerate(raw_sources, start=1))
    ids = [source.id for source in sources]
    duplicates = {source_id for source_id in ids if ids.count(source_id) > 1}
    if duplicates:
        raise ManifestError(f"{path}: duplicate source ids: {', '.join(sorted(duplicates))}")
    return Manifest(sources=sources)


def _source_from_toml(index: int, raw: Any) -> SourceConfig:
    if not isinstance(raw, dict):
        raise ManifestError(f"source #{index}: expected table")

    def require_str(key: str) -> str:
        value = raw.get(key)
        if not isinstance(value, str) or not value:
            raise ManifestError(f"source #{index}: {key} must be a non-empty string")
        return value

    notice_required = raw.get("notice_required")
    if not isinstance(notice_required, bool):
        raise ManifestError(f"source #{index}: notice_required must be boolean")

    enabled = raw.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ManifestError(f"source #{index}: enabled must be boolean")

    refreshable = raw.get("refreshable", True)
    if not isinstance(refreshable, bool):
        raise ManifestError(f"source #{index}: refreshable must be boolean")

    array = raw.get("array")
    if array is not None and not isinstance(array, str):
        raise ManifestError(f"source #{index}: array must be a string")

    download_url = raw.get("download_url")
    if download_url is not None and not isinstance(download_url, str):
        raise ManifestError(f"source #{index}: download_url must be a string")

    drop_words_raw = raw.get("drop_words", [])
    if not isinstance(drop_words_raw, list) or not all(
        isinstance(item, str) for item in drop_words_raw
    ):
        raise ManifestError(f"source #{index}: drop_words must be a list of strings")

    return SourceConfig(
        id=require_str("id"),
        title=require_str("title"),
        path=require_str("path"),
        parser_kind=require_str("parser_kind"),
        category=require_str("category"),
        url=require_str("url"),
        retrieved=require_str("retrieved"),
        expected_sha256=require_str("expected_sha256"),
        license=require_str("license"),
        license_url=require_str("license_url"),
        attribution=require_str("attribution"),
        changes=require_str("changes"),
        notice_required=notice_required,
        enabled=enabled,
        refreshable=refreshable,
        array=array,
        download_url=download_url,
        drop_words=tuple(word.lower() for word in drop_words_raw),
    )
