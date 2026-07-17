# -*- coding: utf-8 -*-
"""Focused tests for logic that does not require Revit."""

import os
import sys
import unittest


REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBRARY_PATH = os.path.join(REPOSITORY_ROOT, "PyrevitTools.extension", "lib")
if LIBRARY_PATH not in sys.path:
    sys.path.insert(0, LIBRARY_PATH)

from batch_sheet_logic import (  # noqa: E402
    OP_FIND_REPLACE,
    OP_PREFIX,
    OP_SUFFIX,
    TARGET_NAME,
    TARGET_NUMBER,
    natural_sort_key,
    sequence_values,
    transform_text,
    validate_new_value,
)


class NaturalSortTests(unittest.TestCase):

    def test_sheet_numbers_sort_naturally(self):
        values = ["A10", "A2", "A1", "G003", "G20"]
        self.assertEqual(
            ["A1", "A2", "A10", "G003", "G20"],
            sorted(values, key=natural_sort_key),
        )


class TextRuleTests(unittest.TestCase):

    def test_find_and_replace_is_case_sensitive(self):
        self.assertEqual(
            "Level 01 plan",
            transform_text(
                "Floor 01 plan",
                OP_FIND_REPLACE,
                find_text="Floor",
                replacement_text="Level",
            ),
        )
        self.assertEqual(
            "FLOOR 01 plan",
            transform_text(
                "FLOOR 01 plan",
                OP_FIND_REPLACE,
                find_text="Floor",
                replacement_text="Level",
            ),
        )

    def test_find_and_replace_can_remove_text(self):
        self.assertEqual(
            "Ground Plan",
            transform_text(
                "Ground Floor Plan",
                OP_FIND_REPLACE,
                find_text="Floor ",
                replacement_text="",
            ),
        )

    def test_prefix_and_suffix(self):
        self.assertEqual(
            "ISS-A101",
            transform_text("A101", OP_PREFIX, affix="ISS-"),
        )
        self.assertEqual(
            "A101-P",
            transform_text("A101", OP_SUFFIX, affix="-P"),
        )

    def test_empty_find_is_rejected(self):
        with self.assertRaises(ValueError):
            transform_text(
                "A101",
                OP_FIND_REPLACE,
                find_text="",
                replacement_text="A",
            )


class SequenceTests(unittest.TestCase):

    def test_sequence_uses_prefix_start_and_padding(self):
        self.assertEqual(
            ["A-009", "A-010", "A-011"],
            sequence_values(3, "A-", 9, 3),
        )

    def test_sequence_rejects_invalid_inputs(self):
        with self.assertRaises(ValueError):
            sequence_values(1, "A-", -1, 3)
        with self.assertRaises(ValueError):
            sequence_values(1, "A-", 1, 0)


class ValidationTests(unittest.TestCase):

    def test_blank_values_are_rejected(self):
        self.assertIsNotNone(validate_new_value("   ", TARGET_NAME))
        self.assertIsNotNone(validate_new_value("", TARGET_NUMBER))

    def test_documented_sheet_number_characters_are_rejected(self):
        for character in "{}[]|;<>?`~":
            self.assertIsNotNone(
                validate_new_value("A{0}101".format(character), TARGET_NUMBER)
            )

    def test_ordinary_values_are_accepted(self):
        self.assertIsNone(validate_new_value("A-101.1", TARGET_NUMBER))
        self.assertIsNone(validate_new_value("GROUND FLOOR PLAN", TARGET_NAME))

    def test_control_characters_are_rejected(self):
        self.assertIsNotNone(validate_new_value("A101\nA", TARGET_NUMBER))


if __name__ == "__main__":
    unittest.main()
