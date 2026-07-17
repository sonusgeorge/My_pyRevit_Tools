# Batch Sheet Edit — Manual Revit Test Plan

## Model setup

Use a disposable copy of a project containing at least these sheets:

| Number | Name |
| --- | --- |
| A1 | GENERAL NOTES |
| A2 | GROUND FLOOR PLAN |
| A10 | FIRST FLOOR PLAN |
| A20 | ROOF PLAN |
| X-001 | TEST SHEET |

Add one placeholder sheet if the project uses them. For Revit 2025 or newer,
also place two test sheets in different Sheet Collections and give them the same
number using Revit's normal interface.

Run the main workflow in at least Revit 2022 and Revit 2027. Ideally smoke-test
every intermediate supported release used by the team.

## Normal workflows

### Sheet Name find and replace

1. Select A2, A10, and A20.
2. Choose **Sheet Name** and **Find and Replace**.
3. Find `PLAN`; replace it with `LAYOUT`.
4. Confirm that the preview shows three exact old/new pairs.
5. Apply the changes.

Expected: all three names change, Project Browser and title blocks refresh, and
one Revit Undo restores all three original names.

### Sheet Number prefix and suffix

1. Select several sheets.
2. Add prefix `ISS-` and apply.
3. Verify browser, title block labels, schedules, and view references.
4. Undo once.
5. Repeat with suffix `-P`, then undo once.

Expected: every selected number changes and a single Undo restores the batch.

### Sequential numbering and natural order

1. Select A1, A2, and A10.
2. Choose **Sequential Numbers**.
3. Enter prefix `S-`, start `1`, and minimum digits `3`.

Expected preview order and results: A1 -> S-001, A2 -> S-002, and A10 ->
S-003. After applying, one Undo restores all three.

### Temporary-number collision handling

1. Select A1 and A2.
2. Sequentially renumber with prefix `A`, start `2`, and one digit.

Expected: A1 becomes A2 and A2 becomes A3 without a transient duplicate-number
failure, provided no unselected A3 exists. Undo once.

## Cancellation and no-change tests

- Cancel the sheet selector: no error and no changes.
- Cancel the field, rule, and each text-input dialog: no changes.
- Cancel at the preview confirmation: no changes.
- Find text that is absent from every selected value: the tool reports no
  changes and does not start a transaction.

## Invalid and failure tests

- Attempt to create a blank sheet number by removing its entire value.
- Enter a prohibited number character such as `?`, `[`, or `|`.
- Create a final number that already belongs to an unselected sheet in the same
  number scope.
- In a workshared test model, have another user own one selected sheet and test
  the failure path.
- Run in a read-only project and in a family document.

Expected: the tool explains the problem; no partial batch remains. Confirm the
unchanged values in the Project Browser and a sheet schedule.

## Sheet Collection test — Revit 2025+

Select sheets from different Sheet Collections and create identical final sheet
numbers that Revit permits in those collections.

Expected: the preflight does not incorrectly report a cross-collection conflict,
and Revit accepts the batch. A duplicate within the same collection is rejected.

## What to report after testing

If any test fails, send:

- exact Revit version and build;
- exact pyRevit version and selected Python engine;
- which sheets, field, rule, and inputs were used;
- the dialog message;
- the complete pyRevit output/traceback;
- whether any sheet values remained changed and whether Undo was available.
