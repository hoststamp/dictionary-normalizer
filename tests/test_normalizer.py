from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from dictionary_normalizer.normalizer import (
    NormalizationSettings,
    load_blocklist,
    normalize_word,
    normalize_words,
)


class NormalizerTests(unittest.TestCase):
    def test_ascii_fold_special_letters_and_accents(self) -> None:
        self.assertEqual(normalize_word("Þrúðr"), "thrudr")
        self.assertEqual(normalize_word("Eärendil"), "earendil")
        self.assertEqual(normalize_word("Straße"), "strasse")

    def test_drops_multiword_and_punctuation(self) -> None:
        self.assertIsNone(normalize_word(""))
        self.assertIsNone(normalize_word("Sol Invictus"))
        self.assertIsNone(normalize_word("d'euville"))
        self.assertIsNone(normalize_word("Haldir (First Age)"))

    def test_alpha_only_rfc1123_and_length_rejections(self) -> None:
        self.assertIsNone(normalize_word("12"))
        self.assertIsNone(normalize_word("123"))
        self.assertIsNone(normalize_word("abc123"))
        self.assertIsNone(normalize_word("good-word"))
        self.assertIsNone(normalize_word("-bad"))
        self.assertIsNone(normalize_word("bad-"))
        self.assertIsNone(normalize_word("bad--label"))
        self.assertIsNone(normalize_word("ab"))
        self.assertIsNone(normalize_word("abcdefghijklmnop"))

    def test_dedupe_and_drop_words(self) -> None:
        words = normalize_words(["Alpha", "alpha", "Beta"], drop_words={"beta"})
        self.assertEqual(words, ["alpha"])
        self.assertIsNone(normalize_word("alpha", drop_words={"alpha"}))

    def test_custom_blocklist_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "blocklist.txt"
            path.write_text("# comment\n Alpha \n\n", encoding="utf-8")
            self.assertEqual(load_blocklist(path), {"alpha"})

    def test_settings_can_disable_ascii_fold_and_rfc1123_check(self) -> None:
        no_fold = NormalizationSettings(ascii_fold=False)
        self.assertIsNone(normalize_word("éclair", settings=no_fold))

        settings = NormalizationSettings(rfc1123_label=False)
        self.assertEqual(normalize_word("alpha", settings=settings), "alpha")


if __name__ == "__main__":
    unittest.main()
