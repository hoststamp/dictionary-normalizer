#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "hoststamp/dictionary-normalizer"
VERSION_RE = re.compile(r"^(?:v)?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
PROJECT_VERSION_RE = re.compile(r'(?m)^version = "([^"]+)"$')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dispatch the release workflow.")
    parser.add_argument("version", help="full release version, for example 0.2.0 or v0.2.0")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="run the workflow without publishing",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="watch the workflow run until completion",
    )
    args = parser.parse_args(argv)

    version = normalize_version(args.version)
    ensure_clean_current_main()
    current_version = read_current_version()
    if version != current_version:
        raise SystemExit(
            f"requested version {version} does not match current project version {current_version}"
        )
    ensure_tag_available(version)

    before_run_ids = workflow_run_ids()
    run(
        "gh",
        "workflow",
        "run",
        "release.yml",
        "--repo",
        REPO,
        "--ref",
        "main",
        "-f",
        f"version={version}",
        "-f",
        f"dry_run={str(args.dry_run).lower()}",
    )
    run_id = wait_for_new_run(before_run_ids)
    print(f"https://github.com/{REPO}/actions/runs/{run_id}")
    if args.watch:
        run("gh", "run", "watch", run_id, "--repo", REPO, "--exit-status", stream=True)
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


def ensure_clean_current_main() -> None:
    if git("status", "--porcelain").stdout.strip():
        raise SystemExit("worktree must be clean before releasing")

    branch = git("branch", "--show-current").stdout.strip()
    if branch != "main":
        raise SystemExit(f"release workflow must be dispatched from main, currently on {branch}")

    git("fetch", "origin", "main:refs/remotes/origin/main", "--tags")
    local_head = git("rev-parse", "main").stdout.strip()
    remote_head = git("rev-parse", "origin/main").stdout.strip()
    if local_head != remote_head:
        raise SystemExit("main must match origin/main before releasing")

    upstream = git(
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
        check=False,
    ).stdout.strip()
    if upstream != "origin/main":
        raise SystemExit("main must track origin/main before releasing")


def ensure_tag_available(version: str) -> None:
    tag = f"v{version}"
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


def workflow_run_ids() -> set[str]:
    result = run(
        "gh",
        "run",
        "list",
        "--repo",
        REPO,
        "--workflow",
        "release.yml",
        "--limit",
        "10",
        "--json",
        "databaseId",
    )
    return set(re.findall(r'"databaseId":(\d+)', result.stdout))


def wait_for_new_run(previous_ids: set[str]) -> str:
    for _attempt in range(20):
        current_ids = workflow_run_ids()
        new_ids = current_ids - previous_ids
        if new_ids:
            return sorted(new_ids, reverse=True)[0]
        time.sleep(1)
    raise SystemExit("release workflow was dispatched, but the run id was not found")


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def run(*args: str, stream: bool = False) -> subprocess.CompletedProcess[str]:
    if stream:
        return subprocess.run(list(args), cwd=ROOT, text=True, check=True)
    return subprocess.run(
        list(args),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
