# -*- coding: utf-8 -*-
"""Pure-Python rules used by the Batch Sheet Edit pyRevit command.

This module deliberately contains no Revit or pyRevit imports so its behavior
can be checked outside Revit. Keep the syntax compatible with IronPython 2.7.
"""

import re


try:
    text_type = unicode
except NameError:
    text_type = str


TARGET_NAME = "Sheet Name"
TARGET_NUMBER = "Sheet Number"

OP_FIND_REPLACE = "find_replace"
OP_PREFIX = "prefix"
OP_SUFFIX = "suffix"
OP_SEQUENCE = "sequence"

# Autodesk documents these characters as prohibited in sheet numbers.
PROHIBITED_NUMBER_CHARACTERS = set("{}[]|;<>?`~")


def to_text(value):
    """Return a Python text value without depending on the active engine."""
    if value is None:
        return text_type("")
    if isinstance(value, text_type):
        return value
    return text_type(value)


def natural_sort_key(value):
    """Return a Python 2/3-safe key that sorts A2 before A10."""
    parts = re.split(r"(\d+)", to_text(value))
    key = []
    for part in parts:
        if part.isdigit():
            key.append((0, int(part)))
        else:
            key.append((1, part.lower()))
    return key


def transform_text(value, operation, find_text=None, replacement_text=None,
                   affix=None):
    """Apply one supported text rule to a single value."""
    original = to_text(value)

    if operation == OP_FIND_REPLACE:
        find_value = to_text(find_text)
        if not find_value:
            raise ValueError("Find text must not be empty.")
        return original.replace(find_value, to_text(replacement_text))

    if operation == OP_PREFIX:
        prefix = to_text(affix)
        if not prefix:
            raise ValueError("Prefix must not be empty.")
        return prefix + original

    if operation == OP_SUFFIX:
        suffix = to_text(affix)
        if not suffix:
            raise ValueError("Suffix must not be empty.")
        return original + suffix

    raise ValueError("Unsupported text operation: {0}".format(operation))


def sequence_values(count, prefix, start, padding):
    """Build sequential values such as A-001, A-002, A-003."""
    if count < 0:
        raise ValueError("Count must be zero or greater.")
    if start < 0:
        raise ValueError("Starting number must be zero or greater.")
    if padding < 1:
        raise ValueError("Minimum digits must be at least 1.")

    prefix_value = to_text(prefix)
    values = []
    for offset in range(count):
        number_text = to_text(start + offset).zfill(padding)
        values.append(prefix_value + number_text)
    return values


def validate_new_value(value, target):
    """Return a validation message, or None when the value is acceptable."""
    candidate = to_text(value)
    if not candidate.strip():
        return "{0} cannot be blank.".format(target)

    if any(ord(character) < 32 for character in candidate):
        return "{0} cannot contain line breaks or control characters.".format(
            target
        )

    if target == TARGET_NUMBER:
        invalid = sorted(set(candidate).intersection(
            PROHIBITED_NUMBER_CHARACTERS
        ))
        if invalid:
            return "Sheet Number contains prohibited character(s): {0}".format(
                " ".join(invalid)
            )

    return None
