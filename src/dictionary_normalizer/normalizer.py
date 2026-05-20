from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

WORD_RE = re.compile(r"^[a-z]+$")

SPECIAL_FOLD = str.maketrans(
    {
        "þ": "th",
        "Þ": "Th",
        "ð": "d",
        "Ð": "D",
        "æ": "ae",
        "Æ": "Ae",
        "ø": "o",
        "Ø": "O",
        "ß": "ss",
    }
)


@dataclass(frozen=True)
class NormalizationSettings:
    ascii_fold: bool = True
    charset: str = "^[a-z]+$"
    length_min: int = 3
    length_max: int = 12
    rfc1123_label: bool = True

    def as_json(self) -> dict[str, object]:
        return {
            "ascii_fold": self.ascii_fold,
            "charset": self.charset,
            "length_min": self.length_min,
            "length_max": self.length_max,
            "rfc1123_label": self.rfc1123_label,
        }


DEFAULT_SETTINGS = NormalizationSettings()


def load_default_blocklist() -> set[str]:
    data = resources.files("dictionary_normalizer").joinpath("data/blocked-server-words.txt")
    return {
        line.strip().lower()
        for line in data.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


def load_blocklist(path: Path | None = None) -> set[str]:
    if path is None:
        return load_default_blocklist()
    return {
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


def ascii_fold(value: str) -> str:
    folded = value.translate(SPECIAL_FOLD)
    folded = unicodedata.normalize("NFKD", folded)
    return folded.encode("ascii", "ignore").decode("ascii")


def normalize_word(
    raw: object,
    *,
    settings: NormalizationSettings = DEFAULT_SETTINGS,
    blocklist: set[str] | None = None,
    drop_words: set[str] | None = None,
) -> str | None:
    value = str(raw).strip()
    if not value or re.search(r"\s", value):
        return None

    if settings.ascii_fold:
        value = ascii_fold(value)
    value = value.lower()

    if not WORD_RE.fullmatch(value):
        return None
    if not settings.length_min <= len(value) <= settings.length_max:
        return None
    if settings.rfc1123_label and not is_rfc1123_label(value):
        return None
    if blocklist and value in blocklist:
        return None
    if drop_words and value in drop_words:
        return None
    return value


def is_rfc1123_label(value: str) -> bool:
    return (
        len(value) <= 63
        and not value.isnumeric()
        and not value.startswith("-")
        and not value.endswith("-")
        and "--" not in value
    )


def normalize_words(
    raw_words: list[str],
    *,
    settings: NormalizationSettings = DEFAULT_SETTINGS,
    blocklist: set[str] | None = None,
    drop_words: set[str] | None = None,
) -> list[str]:
    normalized = {
        word
        for raw in raw_words
        if (
            word := normalize_word(
                raw,
                settings=settings,
                blocklist=blocklist,
                drop_words=drop_words,
            )
        )
    }
    return sorted(normalized)


def bucket_by_length(words: list[str]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {}
    for word in words:
        buckets.setdefault(str(len(word)), []).append(word)
    return {length: sorted(set(values)) for length, values in sorted(buckets.items(), key=_int_key)}


def _int_key(item: tuple[str, list[str]]) -> int:
    return int(item[0])
