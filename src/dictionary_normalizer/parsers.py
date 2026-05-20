from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .errors import ParserError


def parse_source(path: Path, parser_kind: str, *, array: str | None = None) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if parser_kind == "go-array":
        if not array:
            raise ParserError(f"{path}: go-array parser requires an array name")
        return parse_go_array(text, array)
    if parser_kind == "plain-lines":
        return parse_plain_lines(text)
    if parser_kind == "iau-csn":
        return parse_iau_csn(text)
    if parser_kind == "eff-diceware":
        return parse_eff_diceware(text)
    if parser_kind == "corpora-json":
        return parse_corpora_json(text)
    raise ParserError(f"{path}: unsupported parser kind {parser_kind!r}")


def parse_go_array(text: str, var_name: str) -> list[str]:
    match = re.search(rf"\b{re.escape(var_name)}\s*=\s*\[[^\]]*\]string\s*{{", text)
    if not match:
        raise ParserError(f"go array {var_name!r} not found")

    depth = 0
    end = match.end() - 1
    for end in range(match.end() - 1, len(text)):
        if text[end] == "{":
            depth += 1
        elif text[end] == "}":
            depth -= 1
            if depth == 0:
                break
    else:
        raise ParserError(f"go array {var_name!r} is not closed")

    body = text[match.start() : end]
    return re.findall(r'"([^"]+)"', body)


def parse_plain_lines(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def parse_iau_csn(text: str) -> list[str]:
    words: list[str] = []
    for line in text.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#") or line.startswith("$"):
            continue
        token = line.split()[0]
        if token and token != "_":
            words.append(token)
    return words


def parse_eff_diceware(text: str) -> list[str]:
    words: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            raise ParserError(f"invalid EFF diceware line: {line!r}")
        words.append(parts[1])
    return words


def parse_corpora_json(text: str) -> list[str]:
    data = json.loads(text)
    words: list[str] = []
    _gather_corpora_values(data, words)
    if not words:
        raise ParserError("corpora-json source did not contain any candidate words")
    return words


def _gather_corpora_values(node: Any, words: list[str]) -> None:
    if isinstance(node, list):
        for value in node:
            if isinstance(value, str):
                words.append(value)
            elif isinstance(value, dict):
                name = value.get("name")
                if isinstance(name, str):
                    words.append(name)
                else:
                    _gather_corpora_values(value, words)
            else:
                _gather_corpora_values(value, words)
    elif isinstance(node, dict):
        for key, value in node.items():
            if key in {"description", "source", "url"}:
                continue
            _gather_corpora_values(value, words)
