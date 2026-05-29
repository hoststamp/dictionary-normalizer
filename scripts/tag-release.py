#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"^(?:v)?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
PROJECT_VERSION_RE = re.compile(r'(?m)^version = "([^"]+)"$')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create dictionary-normalizer release tags.")
    parser.add_argument(
        "version",
        nargs="?",
        help="release version; defaults to the current project version",
    )
    parser.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    parser.add_argument("--push", action="store_true", help="push created tags to origin")
    parser.add_argument(
        "--github-actions",
        action="store_true",
        help="allow a GitHub Actions main-branch checkout without a local upstream",
    )
    args = parser.parse_args(argv)

    ensure_clean_main(github_actions=args.github_actions)
    current_version = read_current_version()
    version = current_version if args.version is None else normalize_version(args.version)
    if version != current_version:
        raise SystemExit(
            f"requested version {version} does not match current project version {current_version}"
        )
    ensure_tag_available(version)
    if not args.yes:
        confirm(version, push=args.push)
    create_tags(version)
    if args.push:
        push_tags(version)
    return 0


def normalize_version(raw_version: str) -> str:
    stripped = raw_version.strip()
    match = VERSION_RE.fullmatch(stripped)
    if match is None:
        raise SystemExit("version must be a three-part release version like 0.2.0")
    return stripped.removeprefix("v")


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


def ensure_clean_main(*, github_actions: bool) -> None:
    if git("status", "--porcelain").stdout.strip():
        raise SystemExit("worktree must be clean before tagging")

    git("fetch", "origin", "main:refs/remotes/origin/main", "--tags")
    local_head = git("rev-parse", "HEAD").stdout.strip()
    remote_head = git("rev-parse", "origin/main").stdout.strip()

    if github_actions:
        if os.environ.get("GITHUB_REF_NAME") != "main":
            raise SystemExit("release tag must be created from the main GitHub Actions ref")
        if local_head != remote_head:
            raise SystemExit("GitHub Actions checkout must match origin/main before tagging")
        return

    branch = git("branch", "--show-current").stdout.strip()
    if branch != "main":
        raise SystemExit(f"release tag must be created from main, currently on {branch}")

    local_head = git("rev-parse", "main").stdout.strip()
    if local_head != remote_head:
        raise SystemExit("main must match origin/main before tagging")

    upstream = git(
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
        check=False,
    ).stdout.strip()
    if upstream != "origin/main":
        raise SystemExit("main must track origin/main before tagging")


def ensure_tag_available(version: str) -> None:
    tag = stable_tag(version)
    if git("show-ref", "--verify", "--quiet", f"refs/tags/{tag}", check=False).returncode == 0:
        raise SystemExit(f"local tag already exists: {tag}")
    if (
        git(
            "ls-remote",
            "--exit-code",
            "--tags",
            "origin",
            f"refs/tags/{tag}",
            check=False,
        ).returncode
        == 0
    ):
        raise SystemExit(f"remote tag already exists: {tag}")


def confirm(version: str, *, push: bool) -> None:
    commit = git("rev-parse", "HEAD").stdout.strip()
    action = "create and push" if push else "create"
    print(
        f"Release tag: {stable_tag(version)}\n"
        f"Moving tags: {major_tag(version)}, {minor_tag(version)}\n"
        f"Commit: {commit}\n\n"
        f"Ready to {action} release tags? [y/N]"
    )
    answer = input().strip()
    if answer not in {"y", "Y", "yes", "YES"}:
        raise SystemExit("Aborted.")


def create_tags(version: str) -> None:
    git("tag", "-a", stable_tag(version), "-m", f"Release {stable_tag(version)}")
    git("tag", "-f", major_tag(version))
    git("tag", "-f", minor_tag(version))


def push_tags(version: str) -> None:
    git("push", "origin", stable_tag(version))
    git(
        "push",
        "--force",
        "origin",
        f"refs/tags/{major_tag(version)}",
        f"refs/tags/{minor_tag(version)}",
    )


def stable_tag(version: str) -> str:
    return f"v{version}"


def major_tag(version: str) -> str:
    major = version.split(".", maxsplit=1)[0]
    return f"v{major}"


def minor_tag(version: str) -> str:
    major, minor, _patch = version.split(".")
    return f"v{major}.{minor}"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


if __name__ == "__main__":
    raise SystemExit(main())
