from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import DictionaryNormalizerError

RELEASED_HASHES_FILENAME = "released-version-hashes.json"


def find_released_hashes_path(*anchors: Path) -> Path:
    for anchor in anchors:
        base = _anchor_base(anchor)
        for directory in (base, *base.parents):
            candidate = directory / RELEASED_HASHES_FILENAME
            if candidate.exists():
                return candidate
    searched = ", ".join(str(anchor) for anchor in anchors) or str(Path.cwd())
    raise DictionaryNormalizerError(
        f"{RELEASED_HASHES_FILENAME}: released hashes file not found near any anchor: {searched}"
    )


def load_released_hashes(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise DictionaryNormalizerError(f"{path}: released hashes file not found")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DictionaryNormalizerError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise DictionaryNormalizerError(f"{path}: released hashes must be a JSON object")
    return data


def _anchor_base(anchor: Path) -> Path:
    resolved = anchor.resolve()
    if resolved.exists() and resolved.is_dir():
        return resolved
    return resolved.parent
