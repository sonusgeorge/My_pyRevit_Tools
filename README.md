# Pyrevit Tools

This repository currently contains **Batch Sheet Edit**, a basic pyRevit tool
for changing multiple sheet names or sheet numbers with one rule.

## Supported environment

- Autodesk Revit 2022 through 2027
- pyRevit's default IronPython engine
- Revit project documents (`.rvt` and project templates), not family documents

Revit 2027 requires a pyRevit release that supports Revit 2027's add-in loading
and runtime. Use pyRevit 6.4 or newer for that Revit version. The reusable rule
module is Python 2/3-compatible, but the interactive command intentionally uses
`pyrevit.forms`; current pyRevit CPython form stubs do not support this workflow.

## Installation

1. Copy `PyrevitTools.extension` into a folder configured under pyRevit's
   **Custom Extension Directories**, or add this repository directory there.
2. Reload pyRevit.
3. Open the **PyrevitTools** tab, then **Sheets**, then **Batch Sheet Edit**.

## Basic workflow

1. Select the sheets to change.
2. Choose **Sheet Number** or **Sheet Name**.
3. Choose one rule:
   - Find and Replace (case-sensitive)
   - Add Prefix
   - Add Suffix
   - Sequential Numbers (sheet numbers only)
4. Supply the rule values.
5. Review every old and new value in the pyRevit output window.
6. Confirm to apply the batch as one Revit transaction.

Sequential numbering follows the natural order of the sheets' current numbers,
so `A2` comes before `A10`. Temporary unique sheet numbers are used inside the
same transaction so selected sheets can exchange occupied numbers safely.

## Safety and current scope

- Cancellation before confirmation makes no model changes.
- A duplicate number, invalid value, read-only parameter, worksharing failure,
  or other Revit error rolls back the complete batch.
- Number-conflict checks respect Revit 2025+ Sheet Collections while retaining
  document-wide checking in Revit 2022-2024.
- Linked documents are not modified.
- Placeholder sheets are included and can be edited when Revit allows it.
- This basic version applies one rule to selected sheets. Per-row editing,
  CSV/Excel import, presets, and saved settings are deferred enhancements.

## Verification status

Pure rule logic and Python syntax can be tested locally without Revit. The
command must still be run in each required Revit/pyRevit environment before it
is considered production-ready. See
[`docs/manual-test-plan.md`](docs/manual-test-plan.md) for the Revit test cycle.
