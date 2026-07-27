# -*- coding: UTF-8 -*-
"""List all sheets in the current model, in a searchable window.

Description:
Opens a window listing every sheet in the model, sorted by sheet number.
Type in the search box to filter by number or name. Double-click a sheet,
or select it and click Open Sheet, to open it in Revit.

How to use:
1. Open a project model.
2. Click the button.
3. Type to filter, then double-click the sheet you want.

Requirements:
- A project document must be open (this does not work in the Family Editor).

Notes:
- Placeholder sheets are listed and marked, but cannot be opened because
  they have no view.
- Sheet numbers are sorted naturally, so A9 comes before A10.
- Opening a sheet only changes the active view. Nothing in the model is
  modified, and there is nothing to undo.

Limitations / to-do:
- Read-only. No export or editing yet.
- One sheet at a time.

--------------------------------------------------
Status : Shipped
Version: 2.0
Updated: 2026-07-27
"""

from pyrevit import revit, DB, forms, script

from sg.naming import natural_sort_key, matches_search


doc = revit.doc
uidoc = revit.uidoc

# ---------------------------------------------------------------- guards
if not doc:
    forms.alert("No active Revit document.", exitscript=True)

if doc.IsFamilyDocument:
    forms.alert(
        "This tool works on project documents.\n"
        "You currently have a family open.",
        exitscript=True,
    )


class SheetRow(object):
    """One row in the sheet grid.

    WPF reads these attribute names directly. `display_number` and `name`
    are referenced by the Binding expressions in ListSheetsWindow.xaml --
    renaming either one here silently blanks that column, so keep them
    in sync.
    """

    def __init__(self, sheet):
        self.number = sheet.SheetNumber
        self.name = sheet.Name
        self.is_placeholder = sheet.IsPlaceholder
        self.element_id = sheet.Id

        if self.is_placeholder:
            self.display_number = "{} (placeholder)".format(self.number)
        else:
            self.display_number = self.number


class ListSheetsWindow(forms.WPFWindow):
    """Modal sheet browser.

    After the window closes, read `selected_id`. It holds the ElementId of
    the sheet the user chose, or None if they cancelled.
    """

    def __init__(self, rows):
        # A bare filename resolves against this pushbutton folder.
        forms.WPFWindow.__init__(self, "ListSheetsWindow.xaml")
        self._rows = rows
        self.selected_id = None
        self._apply_filter("")
        self.search_box.Focus()

    # ------------------------------------------------------------ helpers
    def _apply_filter(self, text):
        """Rebuild the visible rows for the given search text."""
        visible = [
            row for row in self._rows
            if matches_search(text, row.number, row.name)
        ]
        self.sheet_grid.ItemsSource = visible

        total = len(self._rows)
        if len(visible) == total:
            self.count_label.Text = "{} sheets".format(total)
        else:
            self.count_label.Text = "{} of {} sheets".format(len(visible), total)

        self._refresh_button()

    def _refresh_button(self):
        """Open Sheet is only usable for a real, selected sheet."""
        row = self.sheet_grid.SelectedItem
        self.open_button.IsEnabled = row is not None and not row.is_placeholder

    def _choose_selected(self):
        """Record the chosen sheet and close. Ignores placeholders."""
        row = self.sheet_grid.SelectedItem
        if row is None or row.is_placeholder:
            return
        self.selected_id = row.element_id
        self.Close()

    # ------------------------------------------------------- XAML events
    # These names are referenced from ListSheetsWindow.xaml.
    def on_search_changed(self, sender, args):
        self._apply_filter(sender.Text)

    def on_selection_changed(self, sender, args):
        self._refresh_button()

    def on_row_double_click(self, sender, args):
        self._choose_selected()

    def on_open_click(self, sender, args):
        self._choose_selected()


# ------------------------------------------------------------------ data
sheets = list(DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet).ToElements())
sheets.sort(key=lambda s: natural_sort_key(s.SheetNumber))

if not sheets:
    forms.alert("No sheets found in this model.", exitscript=True)

rows = [SheetRow(sheet) for sheet in sheets]

# ----------------------------------------------------------------- show
window = ListSheetsWindow(rows)
window.show_dialog()

# ------------------------------------------------- act on the choice
if window.selected_id is not None:
    sheet = doc.GetElement(window.selected_id)
    # Guard against the sheet having gone away while the dialog was open.
    if sheet is not None and sheet.IsValidObject:
        # A view change, not a model change -- no transaction needed.
        uidoc.ActiveView = sheet
