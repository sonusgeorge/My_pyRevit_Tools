# -*- coding: UTF-8 -*-
"""Helpers for sorting and comparing Revit names and numbers.

Runs on IronPython 2.7 (see AGENTS.md), so no f-strings here.
"""

import re

# Splits a string into text chunks and number chunks.
# The brackets around \d+ tell re.split to KEEP the numbers in the result.
#   "A-102" -> ['A-', '102', '']
_NUMBER_CHUNKS = re.compile(r'(\d+)')


def natural_sort_key(text):
    """Return a sort key that orders embedded numbers by value, not by text.

    Why this exists:
        Plain sorting compares strings character by character, so "A10"
        comes before "A9" (because the character "1" is less than "9").
        Humans expect A9, then A10. This fixes that.

            plain   : A-1, A-10, A-2, A10, A100, A2, A9
            natural : A2, A9, A10, A100, A-1, A-2, A-10

    Usage:
        sheets.sort(key=lambda s: natural_sort_key(s.SheetNumber))

    Args:
        text (str): the value to build a sort key from. None is treated
            as an empty string so a missing name never crashes the sort.

    Returns:
        list: chunks of (kind, value) pairs. `kind` is 0 for text and 1
            for numbers. Pairing them like this keeps Python from ever
            comparing a number directly against a string, which is a
            common source of confusing sort errors.
    """
    if text is None:
        text = ''

    key = []
    for chunk in _NUMBER_CHUNKS.split(text):
        if chunk.isdigit():
            key.append((1, int(chunk)))
        else:
            # lower() so "a10" and "A10" sort together
            key.append((0, chunk.lower()))
    return key


def matches_search(search_text, *values):
    """Return True if the search text appears in any of the given values.

    Used to filter lists as the user types in a search box.

    An empty search matches everything, which is what a user expects
    from an empty search box -- clearing the box shows the full list
    again rather than nothing.

    Args:
        search_text (str): what the user typed. None or blank matches all.
        *values (str): the fields to search, for example a sheet number
            and a sheet name. None entries are skipped.

    Returns:
        bool: True if the row should stay visible.

    Examples:
        matches_search("101", "C-101", "Site Plan")  -> True
        matches_search("site", "C-101", "Site Plan") -> True
        matches_search("zzz", "C-101", "Site Plan")  -> False
        matches_search("", "C-101", "Site Plan")     -> True
    """
    if search_text is None:
        return True

    needle = search_text.strip().lower()
    if not needle:
        return True

    for value in values:
        if value and needle in value.lower():
            return True
    return False
