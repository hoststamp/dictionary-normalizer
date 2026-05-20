#!/usr/bin/env python3
"""Extract candidate hostname dictionaries into clean one-word-per-line files.

Scratch tooling for dictionary vibe review. Not part of the hoststamp build.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent


def write_words(path: Path, words):
    seen, out = set(), []
    for w in words:
        w = str(w).strip()
        if w and w.lower() not in seen:
            seen.add(w.lower())
            out.append(w)
    path.write_text("\n".join(out) + "\n")
    return len(out)


def go_array(text: str, var_name: str) -> list[str]:
    """Pull quoted strings from a Go slice/array literal for `var_name`.

    Tolerates gofmt alignment whitespace and both [...]string{ and []string{.
    """
    m = re.search(rf"\b{re.escape(var_name)}\s*=\s*\[[^\]]*\]string\s*{{",
                  text)
    if not m:
        raise SystemExit(f"array {var_name!r} not found")
    i = m.start()
    depth = 0
    j = i
    for j in range(m.end() - 1, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                break
    body = text[i:j]
    return re.findall(r'"([^"]+)"', body)


def _gather(node, out):
    """Recursively collect names from any nested list/dict structure."""
    if isinstance(node, list):
        for el in node:
            if isinstance(el, str):
                out.append(el)
            elif isinstance(el, dict):
                out.append(el.get("name") or next(iter(el.values())))
            else:
                _gather(el, out)
    elif isinstance(node, dict):
        for key, val in node.items():
            if key in ("description", "source", "url"):
                continue
            _gather(val, out)


def corpora(rel: str):
    url = f"https://raw.githubusercontent.com/dariusk/corpora/master/data/{rel}"
    data = json.loads(urllib.request.urlopen(url, timeout=30).read())
    items: list = []
    _gather(data, items)
    if not items:
        raise ValueError(f"no list found in {rel}")
    return rel.rsplit("/", 1)[-1].removesuffix(".json"), items


report = []

# --- petname (Apache-2.0): adjectives, adverbs, names(=animals) ---
pg = (ROOT / "petname/petname.go").read_text()
for name in ("adjectives", "adverbs", "names"):
    n = write_words(ROOT / f"petname/{name}.txt", go_array(pg, name))
    report.append(("petname", name, n, "Apache-2.0"))

# --- docker/moby names-generator (Apache-2.0): left=adjectives, right=surnames ---
mg = (ROOT / "docker-moby/names-generator.go").read_text()
n = write_words(ROOT / "docker-moby/adjectives.txt", go_array(mg, "left"))
report.append(("docker-moby", "adjectives", n, "Apache-2.0"))
n = write_words(ROOT / "docker-moby/surnames.txt", go_array(mg, "right"))
report.append(("docker-moby", "surnames", n, "Apache-2.0"))

# --- haikunator (MIT): adjectives, nouns ---
hg = (ROOT / "haikunator/haikunator.go").read_text()
n = write_words(ROOT / "haikunator/adjectives.txt", go_array(hg, "adjectives"))
report.append(("haikunator", "adjectives", n, "MIT"))
n = write_words(ROOT / "haikunator/nouns.txt", go_array(hg, "nouns"))
report.append(("haikunator", "nouns", n, "MIT"))

# --- IAU star names (factual / public domain): column 1 of IAU-CSN.txt ---
stars = []
for line in (ROOT / "iau-star-names/IAU-CSN.txt").read_text().splitlines():
    line = line.rstrip()
    if not line or line.startswith("#"):
        continue
    tok = line.split()[0]
    if tok and tok != "_":
        stars.append(tok)
n = write_words(ROOT / "iau-star-names/star-names.txt", stars)
report.append(("iau-star-names", "star-names", n, "factual/public-domain"))

# --- corpora (CC0): themed proper-noun sets ---
CORPORA = {
    "greek-gods": "mythology/greek_gods.json",
    "greek-titans": "mythology/greek_titans.json",
    "greek-monsters": "mythology/greek_monsters.json",
    "roman-deities": "mythology/roman_deities.json",
    "norse-gods": "mythology/norse_gods.json",
    "egyptian-gods": "mythology/egyptian_gods.json",
    "elements": "science/elements.json",
    "planets": "science/planets.json",
    "minor-planets": "science/minor_planets.json",
    "gemstones": "materials/gemstones.json",
    "decorative-stones": "materials/decorative-stones.json",
    "metals": "materials/metals.json",
    "rivers": "geography/rivers.json",
    "winds": "geography/winds.json",
    "oceans": "geography/oceans.json",
    "scientists": "humans/scientists.json",
    "tolkien": "humans/tolkienCharacterNames.json",
    "neutral-names": "humans/neutralNames.json",
}
for out, rel in CORPORA.items():
    try:
        key, items = corpora(rel)
        n = write_words(ROOT / f"corpora/{out}.txt", items)
        report.append(("corpora", f"{out} ({key})", n, "CC0"))
    except Exception as e:  # noqa: BLE001 - scratch tool, report and continue
        report.append(("corpora", f"{out} FAILED: {e}", 0, "CC0"))

# --- pure facts (public domain) ---
nato = ("Alfa Bravo Charlie Delta Echo Foxtrot Golf Hotel India Juliett Kilo "
        "Lima Mike November Oscar Papa Quebec Romeo Sierra Tango Uniform "
        "Victor Whiskey Xray Yankee Zulu").split()
n = write_words(ROOT / "facts/nato-phonetic.txt", nato)
report.append(("facts", "nato-phonetic", n, "public-domain"))

print(f"{'source':<16}{'list':<34}{'count':>7}  license")
print("-" * 78)
for src, lst, cnt, lic in report:
    print(f"{src:<16}{lst:<34}{cnt:>7}  {lic}")
