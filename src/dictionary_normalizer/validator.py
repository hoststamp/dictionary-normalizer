from __future__ import annotations

import hashlib
import json
import re
from base64 import urlsafe_b64decode, urlsafe_b64encode
from binascii import Error as BinasciiError
from datetime import datetime
from typing import Any

from .errors import ValidationError
from .normalizer import WORD_RE, is_rfc1123_label

SOURCE_FIELDS = {
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

ARTIFACT_FIELDS = {
    "schema_version",
    "generated",
    "generator",
    "normalization",
    "default_dictionary_version",
    "default_blocklist_version",
    "words",
    "dictionary_versions",
    "blocklist_versions",
    "sources",
}
NORMALIZATION_FIELDS = {"ascii_fold", "charset", "length_min", "length_max", "rfc1123_label"}
WORDS_FIELDS = {"allowed", "blocked"}
DICTIONARY_VERSION_FIELDS = {"label", "sources", "categories", "hash"}
BLOCKLIST_VERSION_FIELDS = {"label", "sources", "hash"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
BASE36_RE = re.compile(r"^[a-z0-9]+$")
BASE64URL_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def validate_artifact(
    artifact: dict[str, Any],
    *,
    released_hashes: dict[str, Any] | None = None,
) -> None:
    _reject_unknown_fields(artifact, ARTIFACT_FIELDS, "artifact")
    if artifact.get("schema_version") != 1:
        raise ValidationError("schema_version must be 1")

    generated = _require_str(artifact, "generated", "artifact")
    _validate_generated(generated)
    _require_str(artifact, "generator", "artifact")
    _validate_normalization(_require_dict(artifact, "normalization", "artifact"))

    allowed_words, blocked_words = _validate_words(artifact.get("words"))
    source_ids = _validate_sources(_require_dict(artifact, "sources", "artifact"))

    dictionary_versions = _require_dict(artifact, "dictionary_versions", "artifact")
    blocklist_versions = _require_dict(artifact, "blocklist_versions", "artifact")
    if not dictionary_versions:
        raise ValidationError("dictionary_versions must not be empty")
    if not blocklist_versions:
        raise ValidationError("blocklist_versions must not be empty")

    dictionary_hashes = _validate_dictionary_versions(
        dictionary_versions, allowed_words, source_ids
    )
    blocklist_hashes = _validate_blocklist_versions(blocklist_versions, blocked_words, source_ids)

    default_dictionary_version = _require_int(artifact, "default_dictionary_version", "artifact")
    default_blocklist_version = _require_int(artifact, "default_blocklist_version", "artifact")
    if str(default_dictionary_version) not in dictionary_versions:
        raise ValidationError("default_dictionary_version is missing from dictionary_versions")
    if str(default_blocklist_version) not in blocklist_versions:
        raise ValidationError("default_blocklist_version is missing from blocklist_versions")

    if released_hashes is not None:
        _validate_released_hashes(dictionary_hashes, blocklist_hashes, released_hashes)


def dictionary_version_hash(
    version: int,
    label: str,
    sources: list[str],
    categories: dict[str, list[str]],
) -> str:
    return _logical_hash(
        {
            "kind": "dictionary",
            "version": version,
            "label": label,
            "sources": sources,
            "categories": categories,
        }
    )


def blocklist_version_hash(version: int, label: str, sources: dict[str, list[str]]) -> str:
    return _logical_hash(
        {"kind": "blocklist", "version": version, "label": label, "sources": sources}
    )


def encode_blocked_token(token: str) -> str:
    return urlsafe_b64encode(token.encode("utf-8")).decode("ascii").rstrip("=")


def decode_blocked_token(encoded: str) -> str:
    padding = "=" * (-len(encoded) % 4)
    try:
        decoded = urlsafe_b64decode((encoded + padding).encode("ascii")).decode("utf-8")
    except (BinasciiError, UnicodeDecodeError, ValueError) as exc:
        raise ValidationError(f"invalid blocked token encoding: {encoded}") from exc
    if encode_blocked_token(decoded) != encoded:
        raise ValidationError(f"blocked token is not canonical base64url: {encoded}")
    return decoded


def _logical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_normalization(normalization: dict[str, Any]) -> None:
    _reject_unknown_fields(normalization, NORMALIZATION_FIELDS, "artifact.normalization")
    length_min = _require_int(normalization, "length_min", "artifact.normalization")
    length_max = _require_int(normalization, "length_max", "artifact.normalization")
    if length_min < 1 or length_max < length_min:
        raise ValidationError("artifact.normalization length bounds are invalid")
    if normalization.get("ascii_fold") is not True:
        raise ValidationError("artifact.normalization.ascii_fold must be true")
    if normalization.get("charset") != "^[a-z]+$":
        raise ValidationError("artifact.normalization.charset must be ^[a-z]+$")
    if normalization.get("rfc1123_label") is not True:
        raise ValidationError("artifact.normalization.rfc1123_label must be true")


def _validate_words(value: Any) -> tuple[list[str], list[str]]:
    if not isinstance(value, dict):
        raise ValidationError("words must be an object")
    _reject_unknown_fields(value, WORDS_FIELDS, "words")
    allowed = _validate_allowed_words(value.get("allowed"))
    blocked = _validate_blocked_words(value.get("blocked"))
    return allowed, blocked


def _validate_allowed_words(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValidationError("words.allowed must be a non-empty list")
    if value != sorted(set(value)):
        raise ValidationError("words.allowed must be sorted and unique")
    for index, word in enumerate(value):
        if not isinstance(word, str):
            raise ValidationError(f"words.allowed[{index}] must be a string")
        _validate_word(f"words.allowed[{index}]", word)
    return value


def _validate_blocked_words(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValidationError("words.blocked must be a non-empty list")
    decoded: list[str] = []
    for index, encoded in enumerate(value):
        if not isinstance(encoded, str) or not BASE64URL_RE.fullmatch(encoded):
            raise ValidationError(f"words.blocked[{index}] must be base64url")
        token = decode_blocked_token(encoded)
        if not BASE36_RE.fullmatch(token):
            raise ValidationError(f"words.blocked[{index}] decodes to invalid token: {token}")
        decoded.append(token)
    if decoded != sorted(set(decoded)):
        raise ValidationError("words.blocked must decode to sorted unique tokens")
    return decoded


def _validate_sources(sources: dict[str, Any]) -> set[str]:
    if not sources:
        raise ValidationError("sources must not be empty")

    ids: set[str] = set()
    for source_id, source in sources.items():
        if not isinstance(source_id, str) or not source_id:
            raise ValidationError("source ids must be non-empty strings")
        if source_id in ids:
            raise ValidationError(f"duplicate source id: {source_id}")
        ids.add(source_id)
        if not isinstance(source, dict):
            raise ValidationError(f"sources.{source_id} must be an object")
        _reject_unknown_fields(source, SOURCE_FIELDS, f"sources.{source_id}")
        missing = SOURCE_FIELDS - set(source)
        if missing:
            raise ValidationError(
                f"sources.{source_id} missing fields: {', '.join(sorted(missing))}"
            )
        for key in SOURCE_FIELDS - {"notice_required"}:
            _require_str(source, key, f"sources.{source_id}")
        if not SHA256_RE.fullmatch(source["sha256"]):
            raise ValidationError(f"sources.{source_id}.sha256 must be lowercase sha256")
        if not isinstance(source["notice_required"], bool):
            raise ValidationError(f"sources.{source_id}.notice_required must be boolean")
    return ids


def _validate_dictionary_versions(
    versions: dict[str, Any],
    words: list[str],
    source_ids: set[str],
) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for version_key, body in versions.items():
        version = _validate_version_key(version_key, "dictionary_versions")
        if not isinstance(body, dict):
            raise ValidationError(f"dictionary_versions.{version_key} must be an object")
        _reject_unknown_fields(
            body, DICTIONARY_VERSION_FIELDS, f"dictionary_versions.{version_key}"
        )
        label = _require_str(body, "label", f"dictionary_versions.{version_key}")
        refs = body.get("sources")
        if not isinstance(refs, list) or not refs:
            raise ValidationError(f"dictionary_versions.{version_key}.sources must be non-empty")
        if refs != sorted(set(refs)):
            raise ValidationError(
                f"dictionary_versions.{version_key}.sources must be sorted and unique"
            )
        unknown = [source_id for source_id in refs if source_id not in source_ids]
        if unknown:
            raise ValidationError(
                f"dictionary_versions.{version_key}.sources contains unknown ids: "
                + ", ".join(unknown)
            )

        categories = _require_dict(body, "categories", f"dictionary_versions.{version_key}")
        if not categories:
            raise ValidationError(f"dictionary_versions.{version_key}.categories must not be empty")
        logical_categories: dict[str, list[str]] = {}
        for category, word_ids in categories.items():
            if not isinstance(category, str) or not category:
                raise ValidationError("category names must be non-empty strings")
            logical_categories[category] = _validate_word_ids(
                word_ids, words, f"dictionary_versions.{version_key}.categories.{category}"
            )

        expected_hash = dictionary_version_hash(version, label, refs, logical_categories)
        actual_hash = _require_hash(body, "hash", f"dictionary_versions.{version_key}")
        if actual_hash != expected_hash:
            raise ValidationError(
                f"dictionary_versions.{version_key}.hash mismatch: "
                f"expected {expected_hash}, got {actual_hash}"
            )
        hashes[version_key] = actual_hash
    return hashes


def _validate_blocklist_versions(
    versions: dict[str, Any],
    blocked_words: list[str],
    source_ids: set[str],
) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for version_key, body in versions.items():
        version = _validate_version_key(version_key, "blocklist_versions")
        if not isinstance(body, dict):
            raise ValidationError(f"blocklist_versions.{version_key} must be an object")
        _reject_unknown_fields(body, BLOCKLIST_VERSION_FIELDS, f"blocklist_versions.{version_key}")
        label = _require_str(body, "label", f"blocklist_versions.{version_key}")
        refs = _require_dict(body, "sources", f"blocklist_versions.{version_key}")
        if not refs:
            raise ValidationError(f"blocklist_versions.{version_key}.sources must not be empty")
        logical_sources: dict[str, list[str]] = {}
        for source_id, ids in refs.items():
            if source_id not in source_ids:
                raise ValidationError(
                    f"blocklist_versions.{version_key}.sources contains unknown id: {source_id}"
                )
            logical_sources[source_id] = _validate_word_ids(
                ids, blocked_words, f"blocklist_versions.{version_key}.sources.{source_id}"
            )
        expected_hash = blocklist_version_hash(version, label, logical_sources)
        actual_hash = _require_hash(body, "hash", f"blocklist_versions.{version_key}")
        if actual_hash != expected_hash:
            raise ValidationError(
                f"blocklist_versions.{version_key}.hash mismatch: "
                f"expected {expected_hash}, got {actual_hash}"
            )
        hashes[version_key] = actual_hash
    return hashes


def _validate_word_ids(ids: Any, words: list[str], context: str) -> list[str]:
    if not isinstance(ids, list) or not ids:
        raise ValidationError(f"{context} must be a non-empty list")
    if ids != sorted(set(ids)):
        raise ValidationError(f"{context} must be sorted and unique")
    resolved: list[str] = []
    for word_id in ids:
        if not isinstance(word_id, int):
            raise ValidationError(f"{context} contains non-integer id")
        if word_id < 0 or word_id >= len(words):
            raise ValidationError(f"{context} contains out-of-range id: {word_id}")
        resolved.append(words[word_id])
    return resolved


def _validate_version_key(version_key: Any, context: str) -> int:
    if not isinstance(version_key, str) or not version_key.isdecimal():
        raise ValidationError(f"{context} keys must be numeric strings")
    version = int(version_key)
    if version < 1:
        raise ValidationError(f"{context} version numbers must be positive")
    return version


def _validate_released_hashes(
    dictionary_hashes: dict[str, str],
    blocklist_hashes: dict[str, str],
    released_hashes: dict[str, Any],
) -> None:
    expected_sections = {"dictionary_versions", "blocklist_versions"}
    _reject_unknown_fields(released_hashes, expected_sections, "released_hashes")
    for section, actual_hashes in (
        ("dictionary_versions", dictionary_hashes),
        ("blocklist_versions", blocklist_hashes),
    ):
        expected_hashes = released_hashes.get(section, {})
        if not isinstance(expected_hashes, dict):
            raise ValidationError(f"released_hashes.{section} must be an object")
        for version_key, expected_hash in expected_hashes.items():
            if not isinstance(version_key, str) or not version_key.isdecimal():
                raise ValidationError(f"released_hashes.{section} keys must be numeric strings")
            if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
                raise ValidationError(f"released_hashes.{section}.{version_key} must be sha256")
            actual_hash = actual_hashes.get(version_key)
            if actual_hash is None:
                raise ValidationError(f"released {section}.{version_key} is missing from artifact")
            if actual_hash != expected_hash:
                raise ValidationError(
                    f"released {section}.{version_key} hash changed: "
                    f"expected {expected_hash}, got {actual_hash}"
                )


def _validate_word(context: str, word: Any) -> None:
    if not isinstance(word, str):
        raise ValidationError(f"{context} contains non-string")
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


def _require_hash(parent: dict[str, Any], key: str, context: str) -> str:
    value = _require_str(parent, key, context)
    if not SHA256_RE.fullmatch(value):
        raise ValidationError(f"{context}.{key} must be lowercase sha256")
    return value


def _reject_unknown_fields(parent: dict[str, Any], allowed: set[str], context: str) -> None:
    unknown = set(parent) - allowed
    if unknown:
        raise ValidationError(f"{context} has unknown fields: {', '.join(sorted(unknown))}")


def _validate_generated(value: str) -> None:
    if not value.endswith("Z"):
        raise ValidationError("artifact.generated must be UTC RFC3339 ending in Z")
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise ValidationError("artifact.generated must be RFC3339") from exc
