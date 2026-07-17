# -*- coding: utf-8 -*-
"""Batch-edit Revit sheet names or sheet numbers with a safe preview."""

from __future__ import print_function

import uuid

from pyrevit import DB, forms, revit, script

from batch_sheet_logic import (
    OP_FIND_REPLACE,
    OP_PREFIX,
    OP_SEQUENCE,
    OP_SUFFIX,
    TARGET_NAME,
    TARGET_NUMBER,
    natural_sort_key,
    sequence_values,
    to_text,
    transform_text,
    validate_new_value,
)


__title__ = "Batch Sheet\nEdit"
__author__ = "Pyrevit Tools"
__min_revit_ver__ = 2022
__max_revit_ver__ = 2027


COMMAND_TITLE = "Batch Sheet Edit"

LABEL_FIND_REPLACE = "Find and Replace"
LABEL_PREFIX = "Add Prefix"
LABEL_SUFFIX = "Add Suffix"
LABEL_SEQUENCE = "Sequential Numbers"

OPERATION_BY_LABEL = {
    LABEL_FIND_REPLACE: OP_FIND_REPLACE,
    LABEL_PREFIX: OP_PREFIX,
    LABEL_SUFFIX: OP_SUFFIX,
    LABEL_SEQUENCE: OP_SEQUENCE,
}

logger = script.get_logger()
output = script.get_output()


def alert_and_exit(message, warning=False):
    """Show an actionable message and stop without an error traceback."""
    forms.alert(
        message,
        title=COMMAND_TITLE,
        warn_icon=warning,
    )
    script.exit()


def choose_option(options, message):
    """Show a standard pyRevit command switch and handle cancellation."""
    selected = forms.CommandSwitchWindow.show(options, message=message)
    if selected is None:
        script.exit()
    return selected


def ask_text(prompt, default_value="", allow_empty=False):
    """Ask for text, distinguishing Cancel from an intentionally blank value."""
    while True:
        value = forms.ask_for_string(
            default=default_value,
            prompt=prompt,
            title=COMMAND_TITLE,
        )
        if value is None:
            script.exit()
        if allow_empty or to_text(value):
            return to_text(value)
        forms.alert(
            "Enter a value, or click Cancel to stop.",
            title=COMMAND_TITLE,
            warn_icon=True,
        )

def ask_nonnegative_integer(prompt, default_value):
    """Ask until the user supplies a whole number of zero or greater."""
    while True:
        value = forms.ask_for_string(
            default=to_text(default_value),
            prompt=prompt,
            title=COMMAND_TITLE,
        )
        if value is None:
            script.exit()
        try:
            parsed = int(to_text(value).strip())
            if parsed >= 0:
                return parsed
        except (TypeError, ValueError):
            pass
        forms.alert(
            "Enter a whole number of zero or greater.",
            title=COMMAND_TITLE,
            warn_icon=True,
        )


def ask_positive_integer(prompt, default_value, maximum=None):
    """Ask until the user supplies a positive whole number."""
    while True:
        value = forms.ask_for_string(
            default=to_text(default_value),
            prompt=prompt,
            title=COMMAND_TITLE,
        )
        if value is None:
            script.exit()
        try:
            parsed = int(to_text(value).strip())
            if parsed > 0 and (maximum is None or parsed <= maximum):
                return parsed
        except (TypeError, ValueError):
            pass

        if maximum is None:
            guidance = "Enter a whole number greater than zero."
        else:
            guidance = "Enter a whole number from 1 to {0}.".format(maximum)
        forms.alert(
            guidance,
            title=COMMAND_TITLE,
            warn_icon=True,
        )


def get_sheet_name(sheet):
    """Read the locale-independent built-in Sheet Name parameter."""
    parameter = sheet.get_Parameter(DB.BuiltInParameter.SHEET_NAME)
    if parameter is not None:
        value = parameter.AsString()
        if value is not None:
            return to_text(value)
    return to_text(sheet.Name)


def get_sheet_value(sheet, target):
    """Read the selected editable value from a sheet."""
    if target == TARGET_NUMBER:
        return to_text(sheet.SheetNumber)
    return get_sheet_name(sheet)


def get_target_parameter(sheet, target):
    """Return the built-in parameter used to assess editability."""
    if target == TARGET_NUMBER:
        built_in = DB.BuiltInParameter.SHEET_NUMBER
    else:
        built_in = DB.BuiltInParameter.SHEET_NAME
    return sheet.get_Parameter(built_in)


def set_sheet_name(sheet, new_name):
    """Set Sheet Name through its locale-independent built-in parameter."""
    parameter = sheet.get_Parameter(DB.BuiltInParameter.SHEET_NAME)
    if parameter is None:
        raise RuntimeError("Sheet Name parameter is unavailable.")
    if parameter.IsReadOnly:
        raise RuntimeError("Sheet Name parameter is read-only.")
    if not parameter.Set(new_name):
        raise RuntimeError("Revit did not accept the new Sheet Name.")


def element_id_value(element_id):
    """Read ElementId across the 32-bit (2022-2023) and 64-bit APIs."""
    try:
        return element_id.Value
    except AttributeError:
        return element_id.IntegerValue


def sheet_collection_key(sheet):
    """Return the number-uniqueness scope for the current Revit version.

    Revit 2022-2024 has document-wide uniqueness. Revit 2025 and newer can
    reuse a sheet number in different Sheet Collections.
    """
    try:
        collection_id = sheet.SheetCollectionId
    except AttributeError:
        return ("document", 0)
    return ("collection", element_id_value(collection_id))


def normalized_number(value):
    """Normalize a number for a conservative, user-friendly preflight check."""
    return to_text(value).lower()


def all_sheets(document):
    """Collect every non-type sheet in the active project document."""
    return list(
        DB.FilteredElementCollector(document)
        .OfClass(DB.ViewSheet)
        .WhereElementIsNotElementType()
        .ToElements()
    )


def find_number_conflicts(document, changes):
    """Find final-value conflicts without rejecting cross-collection reuse."""
    changing_ids = set(change["sheet"].UniqueId for change in changes)
    occupied = {}

    for sheet in all_sheets(document):
        if sheet.UniqueId in changing_ids:
            continue
        key = (sheet_collection_key(sheet), normalized_number(sheet.SheetNumber))
        occupied[key] = sheet

    conflicts = []
    for change in changes:
        sheet = change["sheet"]
        key = (sheet_collection_key(sheet), normalized_number(change["new"]))
        existing_sheet = occupied.get(key)
        if existing_sheet is not None:
            conflicts.append((change, existing_sheet))
        else:
            occupied[key] = sheet
    return conflicts


def make_temporary_numbers(document, count):
    """Create globally unique, valid temporary numbers for collision-free swaps."""
    used_numbers = set(
        normalized_number(sheet.SheetNumber) for sheet in all_sheets(document)
    )
    temporary_numbers = []
    token = uuid.uuid4().hex[:10].upper()
    index = 1

    while len(temporary_numbers) < count:
        candidate = "BSE-TMP-{0}-{1}".format(token, index)
        normalized = normalized_number(candidate)
        if normalized not in used_numbers:
            temporary_numbers.append(candidate)
            used_numbers.add(normalized)
        index += 1
    return temporary_numbers


def collect_rule_input(target, operation):
    """Collect only the inputs needed for the chosen rule."""
    rule_input = {}

    if operation == OP_FIND_REPLACE:
        rule_input["find_text"] = ask_text(
            "Text to find (matching is case-sensitive):"
        )
        rule_input["replacement_text"] = ask_text(
            "Replacement text (leave blank to remove the found text):",
            allow_empty=True,
        )
    elif operation == OP_PREFIX:
        rule_input["affix"] = ask_text(
            "Prefix to add to each {0}:".format(target.lower())
        )
    elif operation == OP_SUFFIX:
        rule_input["affix"] = ask_text(
            "Suffix to add to each {0}:".format(target.lower())
        )
    elif operation == OP_SEQUENCE:
        rule_input["prefix"] = ask_text(
            "Prefix for the new numbers (for example A-; blank is allowed):",
            allow_empty=True,
        )
        rule_input["start"] = ask_nonnegative_integer(
            "Starting number:",
            1,
        )
        rule_input["padding"] = ask_positive_integer(
            "Minimum number of digits (3 produces 001):",
            3,
            maximum=12,
        )

    return rule_input


def build_changes(selected_sheets, target, operation, rule_input):
    """Calculate changes without modifying the Revit document."""
    ordered_sheets = sorted(
        selected_sheets,
        key=lambda sheet: natural_sort_key(sheet.SheetNumber),
    )

    sequential_results = None
    if operation == OP_SEQUENCE:
        sequential_results = sequence_values(
            len(ordered_sheets),
            rule_input["prefix"],
            rule_input["start"],
            rule_input["padding"],
        )

    changes = []
    for index, sheet in enumerate(ordered_sheets):
        old_value = get_sheet_value(sheet, target)
        if operation == OP_SEQUENCE:
            new_value = sequential_results[index]
        else:
            new_value = transform_text(
                old_value,
                operation,
                find_text=rule_input.get("find_text"),
                replacement_text=rule_input.get("replacement_text"),
                affix=rule_input.get("affix"),
            )

        if new_value != old_value:
            changes.append({
                "sheet": sheet,
                "old": old_value,
                "new": new_value,
            })

    return changes


def validate_changes(target, changes):
    """Return value and parameter-editability problems before opening a transaction."""
    problems = []
    for change in changes:
        sheet = change["sheet"]
        validation_message = validate_new_value(change["new"], target)
        if validation_message:
            problems.append(
                "{0} - {1}: {2}".format(
                    sheet.SheetNumber,
                    get_sheet_name(sheet),
                    validation_message,
                )
            )

        parameter = get_target_parameter(sheet, target)
        if parameter is None:
            problems.append(
                "{0} - {1}: {2} parameter is unavailable.".format(
                    sheet.SheetNumber,
                    get_sheet_name(sheet),
                    target,
                )
            )
        elif parameter.IsReadOnly:
            problems.append(
                "{0} - {1}: {2} is read-only.".format(
                    sheet.SheetNumber,
                    get_sheet_name(sheet),
                    target,
                )
            )
    return problems


def abbreviated_list(lines, limit=12):
    """Keep task-dialog messages usable while reporting the full list in output."""
    visible = list(lines[:limit])
    remaining = len(lines) - len(visible)
    if remaining > 0:
        visible.append("...and {0} more. See the pyRevit output.".format(remaining))
    return "\n".join(visible)


def show_problems(title, problems):
    """Report complete diagnostics in output and a compact dialog."""
    output.print_md("## {0}".format(title))
    for problem in problems:
        output.print_md("- {0}".format(problem))
    alert_and_exit(
        abbreviated_list(problems),
        warning=True,
    )


def show_preview(target, operation_label, selected_count, changes):
    """Print every proposed change and ask for final confirmation."""
    output.print_md("# Batch Sheet Edit Preview")
    output.print_md(
        "**Target:** {0}  \n**Rule:** {1}  \n"
        "**Selected:** {2}  \n**Changing:** {3}".format(
            target,
            operation_label,
            selected_count,
            len(changes),
        )
    )

    table_data = []
    for index, change in enumerate(changes, 1):
        sheet = change["sheet"]
        if target == TARGET_NUMBER:
            context_value = get_sheet_name(sheet)
            context_header = "Sheet Name"
        else:
            context_value = to_text(sheet.SheetNumber)
            context_header = "Sheet Number"
        table_data.append([
            index,
            context_value,
            change["old"],
            change["new"],
        ])

    output.print_table(
        table_data=table_data,
        columns=["#", context_header, "Old {0}".format(target),
                 "New {0}".format(target)],
    )

    return forms.alert(
        "Review all {0} proposed changes in the pyRevit output window.\n\n"
        "Apply them as one undoable transaction?".format(len(changes)),
        title=COMMAND_TITLE,
        yes=True,
        no=True,
    )


def apply_changes(document, target, changes):
    """Apply all changes atomically; any failure rolls back the entire batch."""
    transaction = DB.Transaction(document, COMMAND_TITLE)
    transaction.Start()

    try:
        if target == TARGET_NUMBER:
            temporary_numbers = make_temporary_numbers(document, len(changes))
            for change, temporary_number in zip(changes, temporary_numbers):
                change["sheet"].SheetNumber = temporary_number
            for change in changes:
                change["sheet"].SheetNumber = change["new"]
        else:
            for change in changes:
                set_sheet_name(change["sheet"], change["new"])

        status = transaction.Commit()
        if status != DB.TransactionStatus.Committed:
            raise RuntimeError(
                "Revit did not commit the transaction (status: {0}).".format(
                    status
                )
            )
    except Exception:
        try:
            if transaction.GetStatus() == DB.TransactionStatus.Started:
                transaction.RollBack()
        except Exception:
            logger.exception("The failed transaction could not be rolled back cleanly.")
        raise


def main():
    """Run the interactive command."""
    document = revit.doc
    if document is None:
        alert_and_exit("Open a Revit project before running this tool.", warning=True)
    if document.IsFamilyDocument:
        alert_and_exit("This tool works in Revit project documents only.", warning=True)
    if document.IsReadOnly:
        alert_and_exit(
            "The active document is read-only. No sheets can be changed.",
            warning=True,
        )

    sheets = all_sheets(document)
    if not sheets:
        alert_and_exit("The active project contains no sheets.")

    selected_sheets = forms.select_sheets(
        title="Select sheets to edit",
        button_name="Continue",
        multiple=True,
        doc=document,
    )
    if not selected_sheets:
        script.exit()

    target = choose_option(
        [TARGET_NUMBER, TARGET_NAME],
        "Choose the sheet field to change",
    )

    operation_labels = [LABEL_FIND_REPLACE, LABEL_PREFIX, LABEL_SUFFIX]
    if target == TARGET_NUMBER:
        operation_labels.append(LABEL_SEQUENCE)
    operation_label = choose_option(
        operation_labels,
        "Choose how to change the selected {0}".format(target.lower()),
    )
    operation = OPERATION_BY_LABEL[operation_label]

    rule_input = collect_rule_input(target, operation)
    changes = build_changes(selected_sheets, target, operation, rule_input)
    if not changes:
        alert_and_exit(
            "The rule does not change any of the selected sheets."
        )

    problems = validate_changes(target, changes)
    if problems:
        show_problems("Changes cannot be applied", problems)

    if target == TARGET_NUMBER:
        conflicts = find_number_conflicts(document, changes)
        if conflicts:
            conflict_messages = []
            for change, existing_sheet in conflicts:
                conflict_messages.append(
                    "{0} would conflict with {1} - {2}.".format(
                        change["new"],
                        existing_sheet.SheetNumber,
                        get_sheet_name(existing_sheet),
                    )
                )
            show_problems("Duplicate sheet numbers", conflict_messages)

    if not show_preview(
        target,
        operation_label,
        len(selected_sheets),
        changes,
    ):
        output.print_md("**Canceled:** No sheets were changed.")
        script.exit()

    try:
        apply_changes(document, target, changes)
    except Exception as error:
        logger.exception("Batch Sheet Edit failed; the transaction was rolled back.")
        output.print_md("## Update failed")
        output.print_md(
            "No sheets were changed. Revit reported: `{0}`".format(
                to_text(error)
            )
        )
        alert_and_exit(
            "No sheets were changed; the complete batch was rolled back.\n\n"
            "Revit reported:\n{0}\n\n"
            "See the pyRevit output for diagnostics.".format(to_text(error)),
            warning=True,
        )

    output.print_md(
        "## Complete\n{0} {1} value(s) were updated in one transaction.".format(
            len(changes),
            target.lower(),
        )
    )
    forms.alert(
        "Updated {0} {1} value(s).\n\n"
        "Use Revit Undo once to revert the complete batch.".format(
            len(changes),
            target.lower(),
        ),
        title=COMMAND_TITLE,
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as unexpected_error:
        logger.exception("Unexpected Batch Sheet Edit error.")
        forms.alert(
            "The tool stopped before completing.\n\n"
            "No model changes should remain if the error happened during the update.\n\n"
            "Details: {0}\n\nSee the pyRevit output for diagnostics.".format(
                to_text(unexpected_error)
            ),
            title=COMMAND_TITLE,
            warn_icon=True,
        )
