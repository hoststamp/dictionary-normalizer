from __future__ import annotations

import copy
import unittest
from collections.abc import Callable
from typing import Any
from unittest.mock import patch

from dictionary_normalizer.errors import ValidationError
from dictionary_normalizer.validator import (
    blocklist_version_hash,
    decode_blocked_token,
    dictionary_version_hash,
    encode_blocked_token,
    validate_artifact,
)


def valid_artifact() -> dict[str, Any]:
    artifact: dict[str, Any] = {
        "schema_version": 1,
        "generated": "2026-05-19T00:00:00Z",
        "generator": "dictionary-normalizer 0.1.0",
        "normalization": {
            "ascii_fold": True,
            "charset": "^[a-z]+$",
            "length_min": 3,
            "length_max": 12,
            "rfc1123_label": True,
        },
        "default_dictionary_version": 2,
        "default_blocklist_version": 2,
        "words": {
            "allowed": ["alpha", "bravo", "delta", "echo"],
            "blocked": [encode_blocked_token("b00b"), encode_blocked_token("crack")],
        },
        "dictionary_versions": {
            "1": {
                "label": "sample-v1",
                "sources": ["sample"],
                "categories": {
                    "adjective": [0, 2],
                    "noun": [1],
                },
                "hash": "",
            },
            "2": {
                "label": "sample-v2",
                "sources": ["sample"],
                "categories": {
                    "adjective": [0, 3],
                    "noun": [1],
                },
                "hash": "",
            },
        },
        "blocklist_versions": {
            "1": {
                "label": "safety-v1",
                "sources": {"safety": [1]},
                "hash": "",
            },
            "2": {
                "label": "safety-v2",
                "sources": {"safety": [0, 1]},
                "hash": "",
            },
        },
        "sources": {
            "sample": {
                "title": "Sample",
                "url": "https://example.com",
                "retrieved": "2026-05-19",
                "sha256": "0" * 64,
                "license": "CC0-1.0",
                "license_url": "https://example.com/license",
                "attribution": "Example",
                "changes": "normalized",
                "notice_required": False,
            },
            "safety": {
                "title": "Safety",
                "url": "https://example.com/safety",
                "retrieved": "2026-05-19",
                "sha256": "1" * 64,
                "license": "MIT",
                "license_url": "https://example.com/license",
                "attribution": "Example",
                "changes": "encoded",
                "notice_required": False,
            },
        },
    }
    refresh_hashes(artifact)
    return artifact


def refresh_hashes(artifact: dict[str, Any]) -> None:
    allowed_words = artifact["words"]["allowed"]
    blocked_words = [decode_blocked_token(token) for token in artifact["words"]["blocked"]]
    for version_key, body in artifact["dictionary_versions"].items():
        body["hash"] = dictionary_version_hash(
            int(version_key),
            body["label"],
            body["sources"],
            {
                category: [allowed_words[word_id] for word_id in ids]
                for category, ids in body["categories"].items()
            },
        )
    for version_key, body in artifact["blocklist_versions"].items():
        body["hash"] = blocklist_version_hash(
            int(version_key),
            body["label"],
            {
                source_id: [blocked_words[word_id] for word_id in ids]
                for source_id, ids in body["sources"].items()
            },
        )


class ValidatorTests(unittest.TestCase):
    def test_valid_artifact(self) -> None:
        validate_artifact(valid_artifact())

    def test_rejects_invalid_top_level_shapes(self) -> None:
        invalid_cases = [
            lambda artifact: artifact.update({"schema_version": 2}),
            lambda artifact: artifact.update({"generated": ""}),
            lambda artifact: artifact.update({"generated": "2026-05-19T00:00:00"}),
            lambda artifact: artifact.update({"generated": "not-a-dateZ"}),
            lambda artifact: artifact.update({"generator": ""}),
            lambda artifact: artifact.update({"normalization": []}),
            lambda artifact: artifact.update({"dictionary_versions": {}}),
            lambda artifact: artifact.update({"blocklist_versions": {}}),
            lambda artifact: artifact.update({"sources": {}}),
            lambda artifact: artifact.update({"extra": True}),
        ]
        self.assert_invalid_cases(invalid_cases)

    def test_rejects_invalid_normalization_metadata(self) -> None:
        def normalization(artifact: dict[str, Any]) -> dict[str, Any]:
            return artifact["normalization"]

        invalid_cases = [
            lambda artifact: normalization(artifact).update({"extra": True}),
            lambda artifact: normalization(artifact).update({"length_min": "3"}),
            lambda artifact: normalization(artifact).update({"length_min": 0}),
            lambda artifact: normalization(artifact).update({"length_max": 2}),
            lambda artifact: normalization(artifact).update({"ascii_fold": False}),
            lambda artifact: normalization(artifact).update({"charset": "^[a-z0-9-]+$"}),
            lambda artifact: normalization(artifact).update({"rfc1123_label": False}),
        ]
        self.assert_invalid_cases(invalid_cases)

    def test_rejects_invalid_sources(self) -> None:
        def source(artifact: dict[str, Any]) -> dict[str, Any]:
            return artifact["sources"]["sample"]

        invalid_cases = [
            lambda artifact: artifact.update({"sources": {"sample": "bad"}}),
            lambda artifact: source(artifact).update({"extra": True}),
            lambda artifact: source(artifact).pop("title"),
            lambda artifact: source(artifact).update({"title": ""}),
            lambda artifact: source(artifact).update({"sha256": "x"}),
            lambda artifact: source(artifact).update({"notice_required": "false"}),
        ]
        self.assert_invalid_cases(invalid_cases)

    def test_rejects_malformed_global_words(self) -> None:
        invalid_cases = [
            lambda artifact: artifact.update({"words": []}),
            lambda artifact: artifact["words"].update({"extra": []}),
            lambda artifact: artifact["words"].update({"allowed": []}),
            lambda artifact: artifact["words"].update({"allowed": ["alpha", "alpha"]}),
            lambda artifact: artifact["words"].update({"allowed": ["bravo", "alpha"]}),
            lambda artifact: artifact["words"].update({"allowed": ["bad-word"]}),
            lambda artifact: artifact["words"].update({"allowed": [1]}),
            lambda artifact: artifact["words"].update({"blocked": []}),
            lambda artifact: artifact["words"].update({"blocked": ["not+padded=="]}),
            lambda artifact: artifact["words"].update({"blocked": [encode_blocked_token("bad!")]}),
            lambda artifact: artifact["words"].update(
                {"blocked": [encode_blocked_token("crack"), encode_blocked_token("b00b")]}
            ),
            lambda artifact: artifact["words"].update(
                {"allowed": ["alpha"], "blocked": [encode_blocked_token("alpha")]}
            ),
        ]
        self.assert_invalid_cases(invalid_cases, refresh=False)

    def test_rejects_invalid_word_ids(self) -> None:
        invalid_cases = [
            lambda artifact: artifact["dictionary_versions"]["1"]["categories"].update(
                {"adjective": [0, 99]}
            ),
            lambda artifact: artifact["blocklist_versions"]["1"]["sources"].update(
                {"safety": [99]}
            ),
            lambda artifact: artifact["dictionary_versions"]["1"]["categories"].update(
                {"adjective": ["0"]}
            ),
        ]
        self.assert_invalid_cases(invalid_cases, refresh=False)

    def test_rejects_duplicate_ids_in_category_and_blocklist(self) -> None:
        invalid_cases = [
            lambda artifact: artifact["dictionary_versions"]["1"]["categories"].update(
                {"adjective": [0, 0]}
            ),
            lambda artifact: artifact["blocklist_versions"]["1"]["sources"].update(
                {"safety": [1, 1]}
            ),
        ]
        self.assert_invalid_cases(invalid_cases, refresh=False)

    def test_rejects_invalid_version_shapes(self) -> None:
        invalid_cases = [
            lambda artifact: artifact.update({"sources": {1: artifact["sources"]["sample"]}}),
            lambda artifact: artifact["dictionary_versions"].update({"x": {}}),
            lambda artifact: artifact["dictionary_versions"].update({"0": {}}),
            lambda artifact: artifact["dictionary_versions"].update({"1": []}),
            lambda artifact: artifact["dictionary_versions"]["1"].update({"sources": []}),
            lambda artifact: artifact["dictionary_versions"]["1"].update(
                {"sources": ["sample", "sample"]}
            ),
            lambda artifact: artifact["dictionary_versions"]["1"].update({"sources": ["missing"]}),
            lambda artifact: artifact["dictionary_versions"]["1"].update({"categories": {}}),
            lambda artifact: artifact["dictionary_versions"]["1"]["categories"].update({"": [0]}),
            lambda artifact: artifact["dictionary_versions"]["1"]["categories"].update(
                {"adjective": []}
            ),
            lambda artifact: artifact["blocklist_versions"].update({"x": {}}),
            lambda artifact: artifact["blocklist_versions"].update({"0": {}}),
            lambda artifact: artifact["blocklist_versions"].update({"1": []}),
            lambda artifact: artifact["blocklist_versions"]["1"].update({"sources": {}}),
            lambda artifact: artifact["blocklist_versions"]["1"]["sources"].update(
                {"missing": [0]}
            ),
        ]
        self.assert_invalid_cases(invalid_cases, refresh=False)

    def test_rejects_missing_default_versions(self) -> None:
        invalid_cases = [
            lambda artifact: artifact.update({"default_dictionary_version": 99}),
            lambda artifact: artifact.update({"default_blocklist_version": 99}),
        ]
        self.assert_invalid_cases(invalid_cases)

    def test_rejects_hash_mismatch(self) -> None:
        invalid_cases = [
            lambda artifact: artifact["dictionary_versions"]["1"].update({"label": "changed"}),
            lambda artifact: artifact["blocklist_versions"]["1"].update({"label": "changed"}),
            lambda artifact: artifact["dictionary_versions"]["1"].update({"hash": "0" * 64}),
        ]
        self.assert_invalid_cases(invalid_cases, refresh=False)

    def test_rejects_changed_released_version_hash(self) -> None:
        artifact = valid_artifact()
        released_hashes = {
            "dictionary_versions": {"1": artifact["dictionary_versions"]["1"]["hash"]},
            "blocklist_versions": {"1": artifact["blocklist_versions"]["1"]["hash"]},
        }
        validate_artifact(artifact, released_hashes=released_hashes)

        artifact["dictionary_versions"]["1"]["categories"]["adjective"] = [0, 3]
        refresh_hashes(artifact)
        with self.assertRaises(ValidationError):
            validate_artifact(artifact, released_hashes=released_hashes)

    def test_rejects_malformed_released_hashes(self) -> None:
        artifact = valid_artifact()
        invalid_released_hashes = [
            {"dictionary_versions": {}, "blocklist_versions": {}, "extra": {}},
            {"dictionary_versions": [], "blocklist_versions": {}},
            {"dictionary_versions": {"x": "0" * 64}, "blocklist_versions": {}},
            {"dictionary_versions": {"1": "bad"}, "blocklist_versions": {}},
            {"dictionary_versions": {"99": "0" * 64}, "blocklist_versions": {}},
        ]
        for released_hashes in invalid_released_hashes:
            with self.subTest(released_hashes=released_hashes), self.assertRaises(ValidationError):
                validate_artifact(artifact, released_hashes=released_hashes)

    def test_v2_can_remove_word_without_mutating_v1(self) -> None:
        artifact = valid_artifact()
        v1_words = [
            artifact["words"]["allowed"][word_id]
            for word_id in artifact["dictionary_versions"]["1"]["categories"]["adjective"]
        ]
        v2_words = [
            artifact["words"]["allowed"][word_id]
            for word_id in artifact["dictionary_versions"]["2"]["categories"]["adjective"]
        ]
        self.assertEqual(v1_words, ["alpha", "delta"])
        self.assertEqual(v2_words, ["alpha", "echo"])
        self.assertNotIn("delta", v2_words)
        validate_artifact(artifact)

    def test_v1_and_v2_share_word_string_through_global_table(self) -> None:
        artifact = valid_artifact()
        v1_alpha_id = artifact["dictionary_versions"]["1"]["categories"]["adjective"][0]
        v2_alpha_id = artifact["dictionary_versions"]["2"]["categories"]["adjective"][0]
        self.assertEqual(v1_alpha_id, v2_alpha_id)
        self.assertEqual(artifact["words"]["allowed"][v1_alpha_id], "alpha")
        self.assertEqual(artifact["words"]["allowed"].count("alpha"), 1)

    def test_decodes_blocked_words_through_separate_table(self) -> None:
        artifact = valid_artifact()
        blocked_words = [
            decode_blocked_token(artifact["words"]["blocked"][word_id])
            for word_id in artifact["blocklist_versions"]["2"]["sources"]["safety"]
        ]
        self.assertEqual(blocked_words, ["b00b", "crack"])

    def test_rejects_non_rfc1123_word_when_called_directly(self) -> None:
        class FakeWordRe:
            def fullmatch(self, value: str) -> bool:
                return True

        artifact = valid_artifact()
        artifact["words"]["allowed"] = ["---"]
        with (
            patch("dictionary_normalizer.validator.WORD_RE", FakeWordRe()),
            self.assertRaises(ValidationError),
        ):
            validate_artifact(artifact)

    def assert_invalid_cases(
        self,
        invalid_cases: list[Callable[[dict[str, Any]], object]],
        *,
        refresh: bool = True,
    ) -> None:
        for mutate in invalid_cases:
            artifact = copy.deepcopy(valid_artifact())
            with self.subTest(mutate=mutate), self.assertRaises(ValidationError):
                mutate(artifact)
                if refresh:
                    refresh_hashes(artifact)
                validate_artifact(artifact)


if __name__ == "__main__":
    unittest.main()
