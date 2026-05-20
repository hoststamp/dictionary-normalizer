from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from dictionary_normalizer.errors import ManifestError
from dictionary_normalizer.manifest import load_manifest

VALID_SOURCE = """
[[sources]]
id = "sample"
title = "Sample"
path = "sample.txt"
parser_kind = "plain-lines"
category = "sample"
url = "https://example.com"
retrieved = "2026-05-19"
expected_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
license = "CC0-1.0"
license_url = "https://example.com/license"
attribution = "Example"
changes = "normalized"
notice_required = false
"""


class ManifestTests(unittest.TestCase):
    def test_load_manifest_with_optional_fields(self) -> None:
        manifest = self.load(
            VALID_SOURCE
            + """
enabled = false
array = "words"
download_url = "file:///tmp/source.txt"
drop_words = ["Alpha"]
"""
        )

        source = manifest.sources[0]
        self.assertFalse(source.enabled)
        self.assertEqual(source.array, "words")
        self.assertEqual(source.download_url, "file:///tmp/source.txt")
        self.assertEqual(source.drop_words, ("alpha",))

    def test_duplicate_source_ids_are_rejected(self) -> None:
        with self.assertRaises(ManifestError):
            self.load(VALID_SOURCE + VALID_SOURCE)

    def test_invalid_toml_is_rejected(self) -> None:
        with self.assertRaises(ManifestError):
            self.load("[[sources]")

    def test_missing_sources_are_rejected(self) -> None:
        with self.assertRaises(ManifestError):
            self.load("[other]\nvalue = true\n")

    def test_non_table_source_is_rejected(self) -> None:
        with self.assertRaises(ManifestError):
            self.load("sources = [1]\n")

    def test_required_string_fields_are_validated(self) -> None:
        with self.assertRaises(ManifestError):
            self.load(VALID_SOURCE.replace('id = "sample"', 'id = ""'))

    def test_boolean_and_optional_field_types_are_validated(self) -> None:
        invalid_cases = [
            VALID_SOURCE.replace("notice_required = false", 'notice_required = "no"'),
            VALID_SOURCE + 'enabled = "yes"\n',
            VALID_SOURCE + "array = 3\n",
            VALID_SOURCE + "download_url = 3\n",
            VALID_SOURCE + 'drop_words = ["ok", 3]\n',
        ]
        for text in invalid_cases:
            with self.subTest(text=text), self.assertRaises(ManifestError):
                self.load(text)

    def load(self, text: str):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sources.toml"
            path.write_text(text, encoding="utf-8")
            return load_manifest(path)


if __name__ == "__main__":
    unittest.main()
