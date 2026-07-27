# -*- coding: UTF-8 -*-
"""List all sheets in the current model.

Description:
Shows every sheet in the model as a table in the pyRevit output window,
sorted by sheet number. Click a sheet number to open that sheet in Revit.

How to use:
1. Open a project model.
2. Click the button.
3. Click any sheet number in the output window to jump to that sheet.

Requirements:
- A project document must be open (this does not work in the Family Editor).

Notes:
- Placeholder sheets are listed but are not clickable, because they have
  no view to open.
- Sheet numbers are sorted naturally, so A9 comes before A10.

Limitations / to-do:
- Read-only. Does not modify the model.
- No export yet. Excel/CSV export is planned as a separate tool.

--------------------------------------------------
Status : Shipped
Version: 1.1
Updated: 2026-07-27
"""

from pyrevit import revit, DB, forms, script

from sg.naming import natural_sort_key

output = script.get_output()
doc = revit.doc

# No model open -> tell the user and stop.
if not doc:
    forms.alert("No active Revit document.", exitscript=True)

# Sheets only exist in project documents. Without this guard the tool would
# just say "no sheets found" in the Family Editor, which is confusing.
if doc.IsFamilyDocument:
    forms.alert(
        "This tool works on project documents.\n"
        "You currently have a family open.",
        exitscript=True,
    )

# Collect all sheets and sort them the way a human reads sheet numbers.
sheets = list(DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet).ToElements())
sheets.sort(key=lambda s: natural_sort_key(s.SheetNumber))

output.set_title("Sheets")

if not sheets:
    output.print_md("**No sheets found in this model.**")
    script.exit()

# Build table rows. linkify() turns the sheet number into a clickable link.
# Its output is already HTML-prepared, so it must go through print_table
# (markdown pipeline), NOT print_html -- print_html would double-encode it.
# Placeholder sheets have no view to open, so they are shown as plain text.
data = []
for sheet in sheets:
    if sheet.IsPlaceholder:
        number_cell = "{} (placeholder)".format(sheet.SheetNumber)
    else:
        number_cell = output.linkify(sheet.Id, title=sheet.SheetNumber)
    data.append([number_cell, sheet.Name])

output.print_table(
    table_data=data,
    columns=["Sheet Number", "Sheet Name"],
    title="Sheets in model: {}".format(len(sheets)),
)
