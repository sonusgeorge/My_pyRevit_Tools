# -*- coding: UTF-8 -*-
"""Tests for lib/sg/naming.py.

Pure text logic only -- no Revit needed -- so these run anywhere,
including the VPS and Claude Code web.

Run:
    python tests/test_naming.py

Prints one line per check and exits non-zero on the first failure.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "lib"))

from sg.naming import natural_sort_key, matches_search


_CHECKS = []


def check(label, actual, expected):
    """Compare and report. Raises AssertionError on mismatch."""
    if actual != expected:
        raise AssertionError(
            "{}\n    expected: {!r}\n    actual  : {!r}".format(
                label, expected, actual
            )
        )
    _CHECKS.append(label)
    print("  ok   " + label)


def test_natural_sort_key():
    print("natural_sort_key")
    check(
        "numbers sort by value, not text",
        sorted(["A10", "A9", "A100", "A2"], key=natural_sort_key),
        ["A2", "A9", "A10", "A100"],
    )
    check(
        "case is ignored",
        sorted(["b1", "A1"], key=natural_sort_key),
        ["A1", "b1"],
    )
    check(
        "None and empty do not crash",
        sorted([None, "", "A1"], key=natural_sort_key),
        [None, "", "A1"],
    )


def test_matches_search():
    print("matches_search")
    check("empty search matches", matches_search("", "C-101", "Site Plan"), True)
    check("whitespace search matches", matches_search("   ", "C-101", "x"), True)
    check("None search matches", matches_search(None, "C-101", "x"), True)
    check("matches the number", matches_search("101", "C-101", "Site Plan"), True)
    check("matches the name", matches_search("site", "C-101", "Site Plan"), True)
    check("is case insensitive", matches_search("SITE", "C-101", "Site Plan"), True)
    check("ignores surrounding spaces", matches_search("  site ", "C-101", "Site Plan"), True)
    check("returns False when nothing matches", matches_search("zzz", "C-101", "Site Plan"), False)
    check("skips None values safely", matches_search("101", None, "C-101"), True)
    check("handles all-None values", matches_search("x", None, None), False)


if __name__ == "__main__":
    test_natural_sort_key()
    test_matches_search()
    print("\n{} checks passed".format(len(_CHECKS)))
