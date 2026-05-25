#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dictionary_normalizer.validator import decode_blocked_token  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Decode artifact words.blocked tokens.")
    parser.add_argument("artifact", nargs="?", default="output/artifact.json")
    args = parser.parse_args()

    artifact = json.loads(Path(args.artifact).read_text(encoding="utf-8"))
    for encoded in artifact["words"]["blocked"]:
        print(decode_blocked_token(encoded))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
