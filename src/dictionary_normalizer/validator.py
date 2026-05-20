from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from .errors import ValidationError
from .normalizer import WORD_RE, is_rfc1123_label

REQUIRED_SOURCE_FIELDS = {
    "id",
    "title",
    "url",
    "retrieved",
    "sha256",
    "license",
    "license_url",
    "attribution",
    "changes",
    "notice_required",
}

ARTIFACT_FIELDS = {"schema_version", "meta", "categories"}
META_FIELDS = {"generated", "generator", "normalization", "sources"}
NORMALIZATION_FIELDS = {"ascii_fold", "charset", "length_min", "length_max", "rfc1123_label"}
CATEGORY_FIELDS = {"source_ids", "lengths"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def validate_artifact(artifact: dict[str, Any]) -> None:
    _reject_unknown_fields(artifact, ARTIFACT_FIELDS, "artifact")
    if artifact.get("schema_version") != 1:
        raise ValidationError("schema_version must be 1")
    meta = _require_dict(artifact, "meta", "artifact")
    _reject_unknown_fields(meta, META_FIELDS, "meta")
    categories = _require_dict(artifact, "categories", "artifact")
    if not categories:
        raise ValidationError("categories must not be empty")

    normalization = _require_dict(meta, "normalization", "meta")
    _reject_unknown_fields(normalization, NORMALIZATION_FIELDS, "meta.normalization")
    length_min = _require_int(normalization, "length_min", "meta.normalization")
    length_max = _require_int(normalization, "length_max", "meta.normalization")
    if length_min < 1 or length_max < length_min:
        raise ValidationError("meta.normalization length bounds are invalid")
    if normalization.get("ascii_fold") is not True:
        raise ValidationError("meta.normalization.ascii_fold must be true")
    if normalization.get("charset") != "^[a-z]+$":
        raise ValidationError("meta.normalization.charset must be ^[a-z]+$")
    if normalization.get("rfc1123_label") is not True:
        raise ValidationError("meta.normalization.rfc1123_label must be true")

    generated = _require_str(meta, "generated", "meta")
    _validate_generated(generated)
    _require_str(meta, "generator", "meta")

    source_ids = _validate_sources(meta)
    _validate_categories(categories, source_ids, length_min, length_max)


def _validate_sources(meta: dict[str, Any]) -> set[str]:
    sources = meta.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValidationError("meta.sources must be a non-empty list")

    ids: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValidationError(f"meta.sources[{index}] must be an object")
        _reject_unknown_fields(source, REQUIRED_SOURCE_FIELDS, f"meta.sources[{index}]")
        missing = REQUIRED_SOURCE_FIELDS - set(source)
        if missing:
            raise ValidationError(
                f"meta.sources[{index}] missing fields: {', '.join(sorted(missing))}"
            )
        source_id = _require_str(source, "id", f"meta.sources[{index}]")
        if source_id in ids:
            raise ValidationError(f"duplicate source id: {source_id}")
        ids.add(source_id)
        for key in REQUIRED_SOURCE_FIELDS - {"notice_required"}:
            _require_str(source, key, f"meta.sources[{index}]")
        if not SHA256_RE.fullmatch(source["sha256"]):
            raise ValidationError(f"meta.sources[{index}].sha256 must be lowercase sha256")
        if not isinstance(source["notice_required"], bool):
            raise ValidationError(f"meta.sources[{index}].notice_required must be boolean")
    return ids


def _validate_categories(
    categories: dict[str, Any],
    source_ids: set[str],
    length_min: int,
    length_max: int,
) -> None:
    for category, body in categories.items():
        if not isinstance(category, str) or not category:
            raise ValidationError("category names must be non-empty strings")
        if not isinstance(body, dict):
            raise ValidationError(f"categories.{category} must be an object")
        _reject_unknown_fields(body, CATEGORY_FIELDS, f"categories.{category}")
        refs = body.get("source_ids")
        if not isinstance(refs, list) or not refs:
            raise ValidationError(f"categories.{category}.source_ids must be non-empty")
        if refs != sorted(set(refs)):
            raise ValidationError(f"categories.{category}.source_ids must be sorted and unique")
        unknown = [source_id for source_id in refs if source_id not in source_ids]
        if unknown:
            raise ValidationError(
                f"categories.{category}.source_ids contains unknown ids: {', '.join(unknown)}"
            )

        lengths = body.get("lengths")
        if not isinstance(lengths, dict) or not lengths:
            raise ValidationError(f"categories.{category}.lengths must be non-empty")
        for length_key, words in lengths.items():
            if not isinstance(length_key, str) or not length_key.isdecimal():
                raise ValidationError(f"categories.{category}.lengths keys must be numeric strings")
            length = int(length_key)
            if not length_min <= length <= length_max:
                raise ValidationError(
                    f"categories.{category}.lengths.{length_key} is outside configured bounds"
                )
            if not isinstance(words, list) or not words:
                raise ValidationError(f"categories.{category}.lengths.{length_key} is empty")
            if words != sorted(set(words)):
                raise ValidationError(
                    f"categories.{category}.lengths.{length_key} must be sorted and unique"
                )
            for word in words:
                _validate_word(category, length_key, word, length)


def _validate_word(category: str, length_key: str, word: Any, length: int) -> None:
    if not isinstance(word, str):
        raise ValidationError(f"categories.{category}.lengths.{length_key} contains non-string")
    if len(word) != length:
        raise ValidationError(
            f"categories.{category}.lengths.{length_key} contains wrong length word: {word}"
        )
    if not WORD_RE.fullmatch(word):
        raise ValidationError(f"invalid word charset: {word}")
    if not is_rfc1123_label(word):
        raise ValidationError(f"word is not RFC-1123 label safe: {word}")


def _require_dict(parent: dict[str, Any], key: str, context: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValidationError(f"{context}.{key} must be an object")
    return value


def _require_str(parent: dict[str, Any], key: str, context: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{context}.{key} must be a non-empty string")
    return value


def _require_int(parent: dict[str, Any], key: str, context: str) -> int:
    value = parent.get(key)
    if not isinstance(value, int):
        raise ValidationError(f"{context}.{key} must be an integer")
    return value


def _reject_unknown_fields(parent: dict[str, Any], allowed: set[str], context: str) -> None:
    unknown = set(parent) - allowed
    if unknown:
        raise ValidationError(f"{context} has unknown fields: {', '.join(sorted(unknown))}")


def _validate_generated(value: str) -> None:
    if not value.endswith("Z"):
        raise ValidationError("meta.generated must be UTC RFC3339 ending in Z")
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise ValidationError("meta.generated must be RFC3339") from exc
