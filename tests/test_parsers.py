from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from dictionary_normalizer.errors import ParserError
from dictionary_normalizer.parsers import (
    parse_corpora_json,
    parse_eff_diceware,
    parse_go_array,
    parse_iau_csn,
    parse_plain_lines,
    parse_source,
)


class ParserTests(unittest.TestCase):
    def test_go_array(self) -> None:
        text = """
        var words = []string{
            "alpha",
            "beta",
        }
        """
        self.assertEqual(parse_go_array(text, "words"), ["alpha", "beta"])

    def test_go_array_errors(self) -> None:
        with self.assertRaises(ParserError):
            parse_go_array("var other = []string{}", "words")
        with self.assertRaises(ParserError):
            parse_go_array('var words = []string{"alpha"', "words")

    def test_plain_lines(self) -> None:
        self.assertEqual(parse_plain_lines("# comment\nalpha\n\n beta \n"), ["alpha", "beta"])

    def test_iau_csn(self) -> None:
        text = (
            "# comment\n$ url continuation\nSirius alpha canis\n"
            "_ placeholder\nVega alpha lyrae\n"
        )
        self.assertEqual(parse_iau_csn(text), ["Sirius", "Vega"])

    def test_eff_diceware(self) -> None:
        self.assertEqual(parse_eff_diceware("1111\tabacus\n1112 abdomen\n"), ["abacus", "abdomen"])

    def test_eff_diceware_rejects_malformed_lines(self) -> None:
        with self.assertRaises(ParserError):
            parse_eff_diceware("1111\n")

    def test_corpora_json(self) -> None:
        text = '{"description": "x", "items": [{"name": "Alpha"}, "Beta", {"nested": ["Gamma"]}]}'
        self.assertEqual(parse_corpora_json(text), ["Alpha", "Beta", "Gamma"])

    def test_corpora_json_handles_nested_non_string_values(self) -> None:
        text = '{"items": [{"values": [1, {"name": 2, "fallback": ["Delta"]}]}]}'
        self.assertEqual(parse_corpora_json(text), ["Delta"])

    def test_corpora_json_rejects_empty_sources(self) -> None:
        with self.assertRaises(ParserError):
            parse_corpora_json('{"description": "only metadata"}')

    def test_parse_source_dispatch_and_errors(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "words.txt"
            path.write_text("alpha\n", encoding="utf-8")
            self.assertEqual(parse_source(path, "plain-lines"), ["alpha"])
            path.write_text('{"items": ["alpha"]}', encoding="utf-8")
            self.assertEqual(parse_source(path, "corpora-json"), ["alpha"])
            path.write_text("# comment\n1111 alpha\n", encoding="utf-8")
            self.assertEqual(parse_source(path, "eff-diceware"), ["alpha"])
            path.write_text("# comment\nSirius alpha canis\n", encoding="utf-8")
            self.assertEqual(parse_source(path, "iau-csn"), ["Sirius"])
            with self.assertRaises(ParserError):
                parse_source(path, "go-array")
            with self.assertRaises(ParserError):
                parse_source(path, "unknown")


if __name__ == "__main__":
    unittest.main()
