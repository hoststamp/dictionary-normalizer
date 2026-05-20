from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .artifact import build_artifact, read_artifact, write_artifact
from .errors import DictionaryNormalizerError
from .manifest import load_manifest
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
    parser.add_argument("--refresh", action="store_true", help="refresh sources before building")
    parser.add_argument("--validate", metavar="ARTIFACT", help="validate an existing artifact")

    args = parser.parse_args(argv)

    try:
        if args.validate:
            artifact = read_artifact(Path(args.validate))
            validate_artifact(artifact)
            print(f"{args.validate}: valid")
            return 0

        manifest = load_manifest(Path(args.manifest))
        artifact = build_artifact(Path(args.input), manifest, refresh=args.refresh)
        write_artifact(Path(args.output), artifact)
        print(f"wrote {args.output}")
        return 0
    except DictionaryNormalizerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
