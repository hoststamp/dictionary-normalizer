from __future__ import annotations

import hashlib
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import URLError

from dictionary_normalizer import artifact as artifact_module
from dictionary_normalizer.artifact import build_artifact, read_artifact, refresh_sources
from dictionary_normalizer.cli import main
from dictionary_normalizer.errors import DictionaryNormalizerError
from dictionary_normalizer.manifest import Manifest
from tests._fixtures import source_config


class ArtifactAndCliTests(unittest.TestCase):
    def test_build_artifact_rejects_missing_input_file(self) -> None:
        digest = hashlib.sha256(b"alpha\n").hexdigest()
        with TemporaryDirectory() as temp_dir:
            manifest = Manifest((source_config(expected_sha256=digest),))
            with self.assertRaises(DictionaryNormalizerError):
                build_artifact(Path(temp_dir), manifest)

    def test_build_artifact_rejects_paths_outside_input_dir(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            outside = root.parent / f"{root.name}-outside.txt"
            try:
                outside.write_text("alpha\n", encoding="utf-8")
                digest = hashlib.sha256(outside.read_bytes()).hexdigest()
                manifest = Manifest((source_config(expected_sha256=digest, path="../outside.txt"),))
                with self.assertRaises(DictionaryNormalizerError):
                    build_artifact(root, manifest)
            finally:
                outside.unlink(missing_ok=True)

    def test_build_artifact_rejects_sha256_mismatch(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "words.txt").write_text("alpha\n", encoding="utf-8")
            manifest = Manifest((source_config(expected_sha256="0" * 64),))
            with self.assertRaises(DictionaryNormalizerError):
                build_artifact(root, manifest)

    def test_read_artifact_rejects_non_object_json(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "artifact.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(DictionaryNormalizerError):
                read_artifact(path)

    def test_refresh_sources_downloads_and_verifies_file_urls(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            download = root / "download.txt"
            download.write_text("alpha\n", encoding="utf-8")
            digest = hashlib.sha256(download.read_bytes()).hexdigest()
            manifest = Manifest(
                (
                    source_config(
                        expected_sha256=digest,
                        path="nested/words.txt",
                        download_url=download.as_uri(),
                    ),
                )
            )

            refresh_sources(root, manifest)
            self.assertEqual((root / "nested/words.txt").read_text(encoding="utf-8"), "alpha\n")

    def test_refresh_sources_rejects_download_hash_mismatch(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            download = root / "download.txt"
            download.write_text("alpha\n", encoding="utf-8")
            manifest = Manifest(
                (
                    source_config(
                        expected_sha256="0" * 64,
                        download_url=download.as_uri(),
                    ),
                )
            )

            with self.assertRaises(DictionaryNormalizerError):
                refresh_sources(root, manifest)
            self.assertFalse((root / "words.txt").exists())

    def test_refresh_sources_skips_non_refreshable_sources(self) -> None:
        digest = hashlib.sha256(b"alpha\n").hexdigest()
        manifest = Manifest(
            (
                source_config(
                    expected_sha256=digest,
                    refreshable=False,
                ),
            )
        )
        with TemporaryDirectory() as temp_dir:
            refresh_sources(Path(temp_dir), manifest)
            self.assertFalse((Path(temp_dir) / "words.txt").exists())

    def test_refresh_sources_requires_urls_for_refreshable_sources(self) -> None:
        digest = hashlib.sha256(b"alpha\n").hexdigest()
        manifest = Manifest((source_config(expected_sha256=digest),))
        with TemporaryDirectory() as temp_dir, self.assertRaises(DictionaryNormalizerError):
            refresh_sources(Path(temp_dir), manifest)

    def test_refresh_sources_rejects_unsupported_url_schemes(self) -> None:
        digest = hashlib.sha256(b"alpha\n").hexdigest()
        for url in ("http://example.com/words.txt", "ftp://example.com/words.txt", "words.txt"):
            with self.subTest(url=url), TemporaryDirectory() as temp_dir:
                manifest = Manifest((source_config(expected_sha256=digest, download_url=url),))
                with self.assertRaises(DictionaryNormalizerError):
                    refresh_sources(Path(temp_dir), manifest)

    def test_refresh_sources_rejects_paths_outside_input_dir(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            download = root / "download.txt"
            download.write_text("alpha\n", encoding="utf-8")
            digest = hashlib.sha256(download.read_bytes()).hexdigest()
            manifest = Manifest(
                (
                    source_config(
                        expected_sha256=digest,
                        path="../outside.txt",
                        download_url=download.as_uri(),
                    ),
                )
            )
            with self.assertRaises(DictionaryNormalizerError):
                refresh_sources(root, manifest)

    def test_refresh_sources_wraps_download_errors(self) -> None:
        digest = hashlib.sha256(b"alpha\n").hexdigest()
        manifest = Manifest(
            (
                source_config(
                    expected_sha256=digest,
                    download_url="https://example.com/words.txt",
                ),
            )
        )
        with (
            TemporaryDirectory() as temp_dir,
            patch("urllib.request.urlopen", side_effect=URLError("offline")),
            self.assertRaises(DictionaryNormalizerError),
        ):
            refresh_sources(Path(temp_dir), manifest)

    def test_refresh_sources_rejects_oversized_downloads(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            download = root / "download.txt"
            download.write_text("alpha\n", encoding="utf-8")
            digest = hashlib.sha256(download.read_bytes()).hexdigest()
            manifest = Manifest(
                (
                    source_config(
                        expected_sha256=digest,
                        download_url=download.as_uri(),
                    ),
                )
            )
            with (
                patch.object(artifact_module, "MAX_DOWNLOAD_BYTES", 1),
                self.assertRaises(DictionaryNormalizerError),
            ):
                refresh_sources(root, manifest)
            self.assertFalse((root / "words.txt").exists())

    def test_disabled_sources_are_omitted(self) -> None:
        digest = hashlib.sha256(b"alpha\n").hexdigest()
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "words.txt").write_text("alpha\n", encoding="utf-8")
            manifest = Manifest(
                (
                    source_config(expected_sha256=digest, enabled=False),
                    source_config(expected_sha256=digest),
                )
            )
            artifact = build_artifact(root, manifest)
            self.assertEqual(len(artifact["meta"]["sources"]), 1)

    def test_cli_validate_success_and_build_error(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        artifact = repo / "output/artifact.json"
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["--validate", str(artifact)]), 0)
        self.assertIn("valid", out.getvalue())

        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(main(["--input", "missing", "--output", "output/nope.json"]), 1)
        self.assertIn("error:", err.getvalue())

    def test_cli_validate_rejects_invalid_artifact(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
            err = io.StringIO()
            with redirect_stderr(err):
                self.assertEqual(main(["--validate", str(path)]), 1)
            self.assertIn("error:", err.getvalue())


if __name__ == "__main__":
    unittest.main()
