from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from dictionary_normalizer.artifact import build_artifact, read_artifact, write_artifact
from dictionary_normalizer.cli import main
from dictionary_normalizer.manifest import Manifest, load_manifest
from dictionary_normalizer.normalizer import load_default_blocklist
from dictionary_normalizer.validator import decode_blocked_token, validate_artifact
from tests._fixtures import source_config


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
        dictionary = artifact["dictionary_versions"][str(artifact["default_dictionary_version"])]
        self.assertIn("adjective", dictionary["categories"])
        self.assertIn("animal", dictionary["categories"])
        self.assertIn("diceware", dictionary["categories"])
        deity_words = {
            artifact["words"]["allowed"][word_id] for word_id in dictionary["categories"]["deity"]
        }
        self.assertNotIn("hospitality", deity_words)
        validate_artifact(artifact)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "artifact.json"
            write_artifact(output, artifact)
            validate_artifact(read_artifact(output))

    def test_refresh_handles_mixed_refreshable_and_offline_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_dir = root / "input"
            input_dir.mkdir()
            offline = input_dir / "offline.txt"
            offline.write_text("bravo\n", encoding="utf-8")
            download = root / "download.txt"
            download.write_text("alpha\n", encoding="utf-8")
            manifest = Manifest(
                (
                    source_config(
                        source_id="refreshable",
                        title="Refreshable",
                        path="refreshable.txt",
                        category="refreshable",
                        expected_sha256=hashlib.sha256(download.read_bytes()).hexdigest(),
                        download_url=download.as_uri(),
                    ),
                    source_config(
                        source_id="offline",
                        title="Offline",
                        path="offline.txt",
                        category="offline",
                        expected_sha256=hashlib.sha256(offline.read_bytes()).hexdigest(),
                        refreshable=False,
                    ),
                )
            )

            artifact = build_artifact(input_dir, manifest, refresh=True)

            self.assertEqual(artifact["schema_version"], 1)
            self.assertEqual((input_dir / "refreshable.txt").read_text(encoding="utf-8"), "alpha\n")
            dictionary = artifact["dictionary_versions"][
                str(artifact["default_dictionary_version"])
            ]
            self.assertIn("refreshable", dictionary["categories"])
            self.assertIn("offline", dictionary["categories"])

    def test_artifact_emits_default_blocklist_version(self) -> None:
        root = Path(__file__).resolve().parents[1]
        manifest = load_manifest(root / "sources.toml")
        artifact = build_artifact(root / "input", manifest)
        blocklist = load_default_blocklist()
        blocked_words = [decode_blocked_token(token) for token in artifact["words"]["blocked"]]
        source_ids = artifact["blocklist_versions"][str(artifact["default_blocklist_version"])][
            "sources"
        ]
        server_words = {
            blocked_words[word_id] for word_id in source_ids["hoststamp-server-name-blocklist"]
        }
        sqids_words = {blocked_words[word_id] for word_id in source_ids["sqids-default-blocklist"]}
        self.assertTrue({"aids", "crack", "debugging", "opium", "slave"} <= server_words)
        self.assertTrue(server_words <= blocklist)
        self.assertTrue({"0rgasm", "1d10t", "b00b", "c0ck"} <= sqids_words)
        self.assertFalse(set(artifact["words"]["allowed"]) & set(blocked_words))

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
