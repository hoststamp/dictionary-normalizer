from __future__ import annotations

from dictionary_normalizer.manifest import SourceConfig


def source_config(
    *,
    expected_sha256: str,
    source_id: str = "sample",
    title: str = "Sample",
    path: str = "words.txt",
    category: str = "sample",
    enabled: bool = True,
    download_url: str | None = None,
    refreshable: bool = True,
) -> SourceConfig:
    return SourceConfig(
        id=source_id,
        title=title,
        path=path,
        parser_kind="plain-lines",
        category=category,
        url="https://example.com",
        retrieved="2026-05-20",
        expected_sha256=expected_sha256,
        license="CC0-1.0",
        license_url="https://example.com/license",
        attribution="Example",
        changes="test fixture",
        notice_required=False,
        enabled=enabled,
        refreshable=refreshable,
        download_url=download_url,
    )
