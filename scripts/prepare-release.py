#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"^(?:v)?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
PROJECT_VERSION_RE = re.compile(r'(?m)^version = "([^"]+)"$')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare a dictionary-normalizer release.")
    parser.add_argument(
        "release",
        help="release version or bump level: patch, minor, major, 0.2.0, or v0.2.0",
    )
    args = parser.parse_args(argv)

    current_version = read_current_version()
    version = resolve_release_version(current_version, args.release)
    ensure_not_downgrade(current_version, version)
    update_project_version(version)
    rebuild_artifact()
    return 0


def normalize_version(raw_version: str) -> str:
    stripped = raw_version.strip()
    match = VERSION_RE.fullmatch(stripped)
    if match is None:
        raise SystemExit("version must be a three-part release version like 0.2.0")
    return stripped.removeprefix("v")


def resolve_release_version(current_version: str, requested_release: str) -> str:
    match requested_release:
        case "patch" | "minor" | "major":
            return bump_version(current_version, requested_release)
        case _:
            return normalize_version(requested_release)


def bump_version(version: str, level: str) -> str:
    major, minor, patch = version_tuple(version)
    match level:
        case "patch":
            patch += 1
        case "minor":
            minor += 1
            patch = 0
        case "major":
            major += 1
            minor = 0
            patch = 0
        case _:
            raise SystemExit(f"unsupported bump level: {level}")
    return f"{major}.{minor}.{patch}"


def read_current_version() -> str:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    pyproject_match = PROJECT_VERSION_RE.search(pyproject)
    if pyproject_match is None:
        raise SystemExit("pyproject.toml: project version field not found")

    package_init = (ROOT / "src/dictionary_normalizer/__init__.py").read_text(encoding="utf-8")
    package_match = re.search(r'(?m)^__version__ = "([^"]+)"$', package_init)
    if package_match is None:
        raise SystemExit("src/dictionary_normalizer/__init__.py: package version not found")

    pyproject_version = normalize_version(pyproject_match.group(1))
    package_version = normalize_version(package_match.group(1))
    if package_version != pyproject_version:
        raise SystemExit(
            "project version mismatch: "
            f"pyproject.toml has {pyproject_version}, "
            f"__init__.py has {package_version}"
        )
    return pyproject_version


def ensure_not_downgrade(current_version: str, release_version: str) -> None:
    if version_tuple(release_version) < version_tuple(current_version):
        raise SystemExit(
            f"release version {release_version} is lower than current version {current_version}"
        )


def version_tuple(version: str) -> tuple[int, int, int]:
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def update_project_version(version: str) -> None:
    replace_once(
        ROOT / "pyproject.toml",
        r'(?m)^version = "[^"]+"$',
        f'version = "{version}"',
    )
    replace_once(
        ROOT / "src/dictionary_normalizer/__init__.py",
        r'(?m)^__version__ = "[^"]+"$',
        f'__version__ = "{version}"',
    )


def replace_once(path: Path, pattern: str, replacement: str) -> None:
    original = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, original, count=1)
    if count != 1:
        raise SystemExit(f"{path.relative_to(ROOT)}: expected exactly one version field")
    path.write_text(updated, encoding="utf-8")


def rebuild_artifact() -> None:
    artifact_path = ROOT / "output/artifact.json"
    generated = json.loads(artifact_path.read_text(encoding="utf-8"))["generated"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    run(
        [
            sys.executable,
            "-m",
            "dictionary_normalizer",
            "--input",
            "input",
            "--output",
            "output/artifact.json",
            "--generated",
            generated,
        ],
        env=env,
    )
    run(
        [
            sys.executable,
            "-m",
            "dictionary_normalizer",
            "--validate",
            "output/artifact.json",
        ],
        env=env,
    )


def run(command: list[str], *, env: dict[str, str]) -> None:
    subprocess.run(command, cwd=ROOT, env=env, check=True)


if __name__ == "__main__":
    raise SystemExit(main())
