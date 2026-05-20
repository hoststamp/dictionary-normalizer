from __future__ import annotations

import copy
import unittest
from collections.abc import Callable
from typing import Any
from unittest.mock import patch

from dictionary_normalizer.errors import ValidationError
from dictionary_normalizer.validator import _validate_word, validate_artifact


def valid_artifact() -> dict[str, object]:
    return {
        "schema_version": 1,
        "meta": {
            "generated": "2026-05-19T00:00:00Z",
            "generator": "dictionary-normalizer 0.1.0",
            "normalization": {
                "ascii_fold": True,
                "charset": "^[a-z]+$",
                "length_min": 3,
                "length_max": 12,
                "rfc1123_label": True,
            },
            "sources": [
                {
                    "id": "sample",
                    "title": "Sample",
                    "url": "https://example.com",
                    "retrieved": "2026-05-19",
                    "sha256": "0" * 64,
                    "license": "CC0-1.0",
                    "license_url": "https://example.com/license",
                    "attribution": "Example",
                    "changes": "normalized",
                    "notice_required": False,
                }
            ],
        },
        "categories": {
            "animal": {
                "source_ids": ["sample"],
                "lengths": {"3": ["ant", "ape"], "4": ["bear"]},
            }
        },
    }


class ValidatorTests(unittest.TestCase):
    def test_valid_artifact(self) -> None:
        validate_artifact(valid_artifact())

    def test_rejects_invalid_top_level_and_meta_shapes(self) -> None:
        invalid_cases = [
            lambda artifact: artifact.update({"schema_version": 2}),
            lambda artifact: artifact.update({"meta": []}),
            lambda artifact: artifact["meta"].update({"extra": True}),
            lambda artifact: artifact.update({"categories": []}),
            lambda artifact: artifact.update({"categories": {}}),
        ]
        self.assert_invalid_cases(invalid_cases)

    def test_rejects_invalid_normalization_metadata(self) -> None:
        def normalization(artifact: dict[str, Any]) -> dict[str, Any]:
            return artifact["meta"]["normalization"]

        invalid_cases = [
            lambda artifact: artifact["meta"].update({"normalization": []}),
            lambda artifact: normalization(artifact).update({"extra": True}),
            lambda artifact: normalization(artifact).update({"length_min": "3"}),
            lambda artifact: normalization(artifact).update({"length_min": 0}),
            lambda artifact: normalization(artifact).update({"length_max": 2}),
            lambda artifact: normalization(artifact).update({"ascii_fold": False}),
            lambda artifact: normalization(artifact).update({"charset": "^[a-z0-9-]+$"}),
            lambda artifact: normalization(artifact).update({"rfc1123_label": False}),
            lambda artifact: artifact["meta"].update({"generated": ""}),
            lambda artifact: artifact["meta"].update({"generated": "2026-05-19T00:00:00"}),
            lambda artifact: artifact["meta"].update({"generated": "not-a-dateZ"}),
            lambda artifact: artifact["meta"].update({"generator": ""}),
        ]
        self.assert_invalid_cases(invalid_cases)

    def test_rejects_invalid_sources(self) -> None:
        def source(artifact: dict[str, Any]) -> dict[str, Any]:
            return artifact["meta"]["sources"][0]

        invalid_cases = [
            lambda artifact: artifact["meta"].update({"sources": []}),
            lambda artifact: artifact["meta"].update({"sources": ["sample"]}),
            lambda artifact: source(artifact).update({"extra": True}),
            lambda artifact: source(artifact).pop("title"),
            lambda artifact: artifact["meta"].update(
                {"sources": [source(artifact), copy.deepcopy(source(artifact))]}
            ),
            lambda artifact: source(artifact).update({"id": ""}),
            lambda artifact: source(artifact).update({"sha256": "x"}),
            lambda artifact: source(artifact).update({"notice_required": "false"}),
        ]
        self.assert_invalid_cases(invalid_cases)

    def test_rejects_unknown_source_reference(self) -> None:
        artifact = copy.deepcopy(valid_artifact())
        artifact["categories"]["animal"]["source_ids"] = ["missing"]  # type: ignore[index]
        with self.assertRaises(ValidationError):
            validate_artifact(artifact)

    def test_rejects_invalid_categories_and_buckets(self) -> None:
        def category(artifact: dict[str, Any]) -> dict[str, Any]:
            return artifact["categories"]["animal"]

        def lengths(artifact: dict[str, Any]) -> dict[str, Any]:
            return category(artifact)["lengths"]

        invalid_cases = [
            lambda artifact: artifact.update({"categories": {"": category(artifact)}}),
            lambda artifact: artifact.update({"categories": {"animal": []}}),
            lambda artifact: category(artifact).update({"source_ids": []}),
            lambda artifact: category(artifact).update({"source_ids": ["sample", "sample"]}),
            lambda artifact: category(artifact).update({"source_ids": ["missing"]}),
            lambda artifact: category(artifact).update({"lengths": []}),
            lambda artifact: category(artifact).update({"lengths": {}}),
            lambda artifact: category(artifact).update({"lengths": {"x": ["ant"]}}),
            lambda artifact: category(artifact).update({"lengths": {"2": ["ox"]}}),
            lambda artifact: category(artifact).update({"lengths": {"3": []}}),
            lambda artifact: category(artifact).update({"lengths": {"3": ["ape", "ant", "ant"]}}),
            lambda artifact: lengths(artifact).update({"3": [3]}),
            lambda artifact: lengths(artifact).update({"4": ["ant"]}),
            lambda artifact: lengths(artifact).update({"3": ["a1b"]}),
        ]
        self.assert_invalid_cases(invalid_cases)

    def test_rejects_redundant_counts_field(self) -> None:
        artifact = copy.deepcopy(valid_artifact())
        artifact["categories"]["animal"]["counts"] = {"3": 2, "4": 1}  # type: ignore[index]
        with self.assertRaises(ValidationError):
            validate_artifact(artifact)

    def test_rejects_unknown_top_level_field(self) -> None:
        artifact = copy.deepcopy(valid_artifact())
        artifact["counts"] = {}
        with self.assertRaises(ValidationError):
            validate_artifact(artifact)

    def test_rejects_non_rfc1123_word_when_called_directly(self) -> None:
        class FakeWordRe:
            def fullmatch(self, value: str) -> bool:
                return True

        with (
            patch("dictionary_normalizer.validator.WORD_RE", FakeWordRe()),
            self.assertRaises(ValidationError),
        ):
            _validate_word("sample", "3", "---", 3)
        with self.assertRaises(ValidationError):
            _validate_word("sample", "3", "---", 3)

    def assert_invalid_cases(
        self,
        invalid_cases: list[Callable[[dict[str, Any]], object]],
    ) -> None:
        for mutate in invalid_cases:
            artifact = copy.deepcopy(valid_artifact())
            with self.subTest(mutate=mutate), self.assertRaises(ValidationError):
                mutate(artifact)
                validate_artifact(artifact)


if __name__ == "__main__":
    unittest.main()
