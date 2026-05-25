from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .artifact import build_artifact, read_artifact, write_artifact
from .errors import DictionaryNormalizerError
from .manifest import load_manifest
from .released import find_released_hashes_path, load_released_hashes
from .validator import validate_artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dictionary-normalizer")
    parser.add_argument("--input", default="./input", help="input source directory")
    parser.add_argument(
        "--output",
        default="output/artifact.json",
        help="artifact JSON path to write",
    )
    parser.add_argument("--manifest", default="sources.toml", help="source manifest path")
    parser.add_argument(
        "--released-hashes",
        help="released version hash lock path; defaults to searching near the artifact/manifest",
    )
    parser.add_argument(
        "--generated",
        help="UTC RFC3339 artifact timestamp to write; useful for reproducible rebuild checks",
    )
    parser.add_argument("--refresh", action="store_true", help="refresh sources before building")
    parser.add_argument("--validate", metavar="ARTIFACT", help="validate an existing artifact")

    args = parser.parse_args(argv)

    try:
        if args.validate:
            artifact_path = Path(args.validate)
            released_hashes = load_released_hashes(_released_hashes_path(args, artifact_path))
            artifact = read_artifact(artifact_path)
            validate_artifact(artifact, released_hashes=released_hashes)
            print(f"{args.validate}: valid")
            return 0

        manifest_path = Path(args.manifest)
        released_hashes = load_released_hashes(_released_hashes_path(args, manifest_path))
        manifest = load_manifest(manifest_path)
        artifact = build_artifact(
            Path(args.input),
            manifest,
            refresh=args.refresh,
            released_hashes=released_hashes,
            generated=args.generated,
        )
        write_artifact(Path(args.output), artifact)
        print(f"wrote {args.output}")
        return 0
    except DictionaryNormalizerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _released_hashes_path(args: argparse.Namespace, primary_anchor: Path) -> Path:
    if args.released_hashes:
        return Path(args.released_hashes)
    return find_released_hashes_path(primary_anchor, Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
