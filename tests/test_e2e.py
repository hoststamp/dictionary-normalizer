from __future__ import annotations

import os
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from dictionary_normalizer.artifact import build_artifact, read_artifact, write_artifact
from dictionary_normalizer.cli import main
from dictionary_normalizer.errors import DictionaryNormalizerError
from dictionary_normalizer.manifest import load_manifest
from dictionary_normalizer.normalizer import load_default_blocklist
from dictionary_normalizer.validator import validate_artifact


@contextmanager
def working_directory(path: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class EndToEndTests(unittest.TestCase):
    def test_builds_and_validates_fixture_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        manifest = load_manifest(root / "sources.toml")
        artifact = build_artifact(root / "input", manifest)

        self.assertEqual(artifact["schema_version"], 1)
        self.assertIn("adjective", artifact["categories"])
        self.assertIn("animal", artifact["categories"])
        self.assertIn("diceware", artifact["categories"])
        deity_words = {
            word for words in artifact["categories"]["deity"]["lengths"].values() for word in words
        }
        self.assertNotIn("hospitality", deity_words)
        validate_artifact(artifact)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "artifact.json"
            write_artifact(output, artifact)
            validate_artifact(read_artifact(output))

    def test_refresh_fails_until_manifest_has_download_urls(self) -> None:
        root = Path(__file__).resolve().parents[1]
        manifest = load_manifest(root / "sources.toml")
        with self.assertRaises(DictionaryNormalizerError):
            build_artifact(root / "input", manifest, refresh=True)

    def test_artifact_has_no_blocklisted_words(self) -> None:
        root = Path(__file__).resolve().parents[1]
        manifest = load_manifest(root / "sources.toml")
        artifact = build_artifact(root / "input", manifest)
        blocklist = load_default_blocklist()
        words = {
            word
            for body in artifact["categories"].values()
            for bucket in body["lengths"].values()
            for word in bucket
        }
        self.assertFalse(words & blocklist)
        self.assertFalse(words & {"aids", "crack", "debugging", "opium", "slave"})

    def test_cli_uses_default_output_path(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            with working_directory(temp_root):
                self.assertEqual(
                    main(
                        [
                            "--input",
                            str(root / "input"),
                            "--manifest",
                            str(root / "sources.toml"),
                        ]
                    ),
                    0,
                )
                self.assertTrue((temp_root / "output/artifact.json").exists())


if __name__ == "__main__":
    unittest.main()
