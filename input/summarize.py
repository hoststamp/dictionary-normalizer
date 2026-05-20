#!/usr/bin/env python3
"""Build PROVENANCE.md: per-list license, source, DNS-safety, and a sample."""
import random
import re
from pathlib import Path

ROOT = Path(__file__).parent
random.seed(42)

DNS_RE = re.compile(r"^[a-z0-9-]+$")

LISTS = [
    ("petname/adjectives.txt", "petname", "Apache-2.0",
     "github.com/dustinkirkland/golang-petname (petname.go)"),
    ("petname/adverbs.txt", "petname", "Apache-2.0",
     "github.com/dustinkirkland/golang-petname (petname.go)"),
    ("petname/names.txt", "petname (animals)", "Apache-2.0",
     "github.com/dustinkirkland/golang-petname (petname.go)"),
    ("docker-moby/adjectives.txt", "docker/moby", "Apache-2.0",
     "github.com/moby/moby@v24.0.7 pkg/namesgenerator"),
    ("docker-moby/surnames.txt", "docker/moby (scientists)", "Apache-2.0",
     "github.com/moby/moby@v24.0.7 pkg/namesgenerator"),
    ("haikunator/adjectives.txt", "haikunator", "MIT",
     "github.com/Atrox/haikunatorgo (haikunator.go)"),
    ("haikunator/nouns.txt", "haikunator", "MIT",
     "github.com/Atrox/haikunatorgo (haikunator.go)"),
    ("iau-star-names/star-names.txt", "IAU star names", "factual / public domain",
     "IAU WGSN Catalog of Star Names (IAU-CSN), pas.rochester.edu/~emamajek/WGSN"),
    ("corpora/greek-gods.txt", "Greek gods", "CC0", "dariusk/corpora"),
    ("corpora/greek-titans.txt", "Greek titans", "CC0", "dariusk/corpora"),
    ("corpora/greek-monsters.txt", "Greek monsters", "CC0", "dariusk/corpora"),
    ("corpora/roman-deities.txt", "Roman deities", "CC0", "dariusk/corpora"),
    ("corpora/norse-gods.txt", "Norse gods", "CC0", "dariusk/corpora"),
    ("corpora/egyptian-gods.txt", "Egyptian gods", "CC0", "dariusk/corpora"),
    ("corpora/elements.txt", "Periodic elements", "CC0", "dariusk/corpora"),
    ("corpora/planets.txt", "Planets", "CC0", "dariusk/corpora"),
    ("corpora/minor-planets.txt", "Minor planets", "CC0", "dariusk/corpora"),
    ("corpora/gemstones.txt", "Gemstones", "CC0", "dariusk/corpora"),
    ("corpora/decorative-stones.txt", "Decorative stones", "CC0", "dariusk/corpora"),
    ("corpora/metals.txt", "Metals", "CC0", "dariusk/corpora"),
    ("corpora/rivers.txt", "Rivers", "CC0", "dariusk/corpora"),
    ("corpora/winds.txt", "Winds", "CC0", "dariusk/corpora"),
    ("corpora/oceans.txt", "Oceans/seas", "CC0", "dariusk/corpora"),
    ("corpora/scientists.txt", "Scientists", "CC0", "dariusk/corpora"),
    ("corpora/tolkien.txt", "Tolkien characters", "CC0", "dariusk/corpora"),
    ("corpora/neutral-names.txt", "Neutral given names", "CC0", "dariusk/corpora"),
    ("facts/nato-phonetic.txt", "NATO phonetic", "public domain", "ICAO/NATO alphabet (fact)"),
]

lines = [
    "# Hoststamp dictionary candidates — review staging",
    "",
    "Scratch only (gitignored, not committed). All sources below are",
    "license-compatible with bundling in an FSL-1.1-ALv2 project:",
    "Apache-2.0 / MIT need a NOTICE-style attribution line; CC0 and",
    "factual data (star names, elements, NATO) carry no obligation.",
    "",
    "`clean%` = share of entries already DNS-label-safe as-is",
    "(`^[a-z0-9-]+$` after lowercasing). Low values mean the list needs",
    "ASCII-folding / space-and-punctuation stripping before use, not that",
    "it is unusable — just more normalization work.",
    "",
    "| List | Theme | License | N | Len | clean% (lower) | Sample |",
    "| --- | --- | --- | --: | --- | --- | --- |",
]

detail = ["", "## Full samples (20 random per list)", ""]

for rel, theme, lic, src in LISTS:
    p = ROOT / rel
    if not p.exists():
        continue
    words = [w for w in p.read_text().splitlines() if w]
    n = len(words)
    lo = min(len(w) for w in words)
    hi = max(len(w) for w in words)
    clean = sum(1 for w in words if DNS_RE.match(w.lower())) * 100 // n
    sample = random.sample(words, min(20, n))
    short_sample = ", ".join(sample[:6])
    lines.append(
        f"| `{rel}` | {theme} | {lic} | {n} | {lo}-{hi} | {clean}% | "
        f"{short_sample} |"
    )
    detail.append(f"### {theme} — `{rel}` ({n}, len {lo}-{hi}, "
                  f"{lic}, src: {src})")
    detail.append("")
    detail.append(", ".join(sample))
    detail.append("")

(ROOT / "PROVENANCE.md").write_text("\n".join(lines + detail) + "\n")
print("\n".join(lines))
