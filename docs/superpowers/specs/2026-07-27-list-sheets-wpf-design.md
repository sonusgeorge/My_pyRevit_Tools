# List Sheets — WPF interface

**Date:** 2026-07-27
**Status:** Approved, not yet implemented
**Track:** A (read-only — see `AGENTS.md`)

## Goal

Replace the output-window presentation of List Sheets with a modal WPF
window, and establish the visual standard that later SG-Tools windows
will follow.

The information shown does not change. The presentation does, plus live
search. This is a look-and-feel upgrade, chosen deliberately over adding
features.

## Non-goals

Explicitly out of scope for this version:

- Exporting the sheet list to Excel or CSV
- Selecting more than one sheet at a time
- Editing sheet numbers or names
- Extra columns (revision, discipline, date)
- Click-to-sort column headers
- Remembering window size or position between runs
- A shared style library for future tools (see "Styling" below)

## User experience

1. User clicks **SG Tools → Sheets → List Sheets**.
2. A modal window opens, listing every sheet sorted naturally by number.
3. Typing in the search box filters rows live, matching against sheet
   number and sheet name.
4. Double-clicking a row, or selecting a row and clicking **Open Sheet**,
   closes the window and opens that sheet in Revit.
5. Escape or the window's close button dismisses it with no side effects.

Modal was chosen over a floating window. A floating window cannot call
the Revit API directly and would require an `ExternalEvent` bridge —
significantly more code and failure modes than this tool justifies.

## Architecture

### Location

Built in `SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/`.

The existing output-window tool stays live in `Sheets.panel` throughout
development. Once the WPF version passes the manual test plan below, it
replaces `Sheets.panel/List Sheets.pushbutton/` and the old one is
deleted. The Dev panel folder is then removed.

### Files

```
List Sheets WPF.pushbutton/
├── bundle.yaml            title and author only
├── icon.png               copied from the current tool
├── script.py              guards, data assembly, event wiring
└── ListSheetsWindow.xaml  layout and styling
```

### Control flow

```
script.py
  ├─ guard: doc is not None            -> forms.alert, exit
  ├─ guard: not doc.IsFamilyDocument   -> forms.alert, exit
  ├─ collect ViewSheet via FilteredElementCollector
  ├─ sort with sg.naming.natural_sort_key(sheet.SheetNumber)
  ├─ guard: at least one sheet         -> forms.alert, exit
  ├─ build list of SheetRow objects
  ├─ window = ListSheetsWindow(rows)
  ├─ window.show_dialog()              (blocks until closed)
  └─ if window.selected_id is not None:
         uidoc.ActiveView = doc.GetElement(window.selected_id)
```

Setting `uidoc.ActiveView` is a view change, not a model change. No
transaction is opened and nothing is added to the undo stack. This tool
never modifies the model.

The view change happens **after** the dialog closes, while still inside
the pyRevit command's API context, which is a valid place to call the
Revit API.

### Data model

A plain IronPython class, one instance per sheet, used as the WPF row
item:

| Attribute | Type | Purpose |
|---|---|---|
| `number` | str | `SheetNumber`, shown in column 1 |
| `name` | str | `Name`, shown in column 2 |
| `is_placeholder` | bool | Controls the marker and blocks opening |
| `element_id` | ElementId | Used to activate the sheet |
| `display_number` | str | `number`, plus a marker when placeholder |

WPF binds to these attributes by reflection, which works under
IronPython 2.7. This is the same approach EF-Tools uses.

### Filtering

On each keystroke, rebuild the list assigned to the grid's `ItemsSource`
from the full row list, keeping rows where the lowercased search text
appears in either `number` or `name`.

Filtering uses the raw `number`, not `display_number`, so typing
"placeholder" does not match every placeholder sheet. The marker is
presentation only.

Rebuilding the whole list is fast enough for realistic sheet counts and
avoids the complexity of a `CollectionView` filter. If a model with
thousands of sheets ever feels slow, revisit then.

An empty search box shows everything.

### Placeholder sheets

Listed, and marked in the number column with `(placeholder)`. They have
no view, so they cannot be opened: double-clicking one or pressing
**Open Sheet** on one does nothing. The button is disabled while a
placeholder row is selected, so the behaviour is visible rather than
silent.

## Styling

Style B from the mockups: dark branded header, white body, one accent
colour.

| Element | Value |
|---|---|
| Font | Segoe UI |
| Header background | `#1F2A37` |
| Header eyebrow text (`SG TOOLS`) | white, 60% opacity, 10px, letter-spacing 1.6 |
| Header title text | white, 15px, semibold |
| Body background | `#FFFFFF` |
| Toolbar and footer background | `#FAFBFC` |
| Divider and border | `#E8EAED` |
| Column header underline | 2px `#1F2A37` |
| Sheet number text | `#1565C0`, semibold, tabular figures |
| Selected row background | `#EAF3FB` |
| Primary button | `#1F2A37` background, white text, 4px corner radius |

Window: 560×620 default, resizable, minimum 420×320, centred on screen.

**These values live in `<Window.Resources>` inside
`ListSheetsWindow.xaml`, not in a shared file.**

Two reasons. `AGENTS.md` says move code into `lib/` on second use rather
than in anticipation, and there is no second WPF tool yet. Separately,
sharing a WPF `ResourceDictionary` across pyRevit tools has a real
loading problem: styles referenced with `StaticResource` must resolve
when the XAML is parsed, which conflicts with attaching a dictionary at
runtime from a computed file path. That is worth solving once, with a
real second tool as the test case, rather than guessing now.

Defining all colours in one resource block at the top of the XAML keeps
the later extraction to a copy-paste.

## Error handling

| Situation | Behaviour |
|---|---|
| No active document | `forms.alert`, exit, no window |
| Family document open | `forms.alert` explaining sheets need a project, exit |
| Project has no sheets | `forms.alert`, exit — no empty window |
| User closes window without choosing | Nothing happens, no error |
| Placeholder row selected | **Open Sheet** disabled, double-click ignored |
| Selected sheet no longer valid | Checked with `IsValidObject` before activating |

Unexpected exceptions are not caught. They surface in the pyRevit output
window with a full traceback, per the coding principles in `AGENTS.md`.

## Testing

### Verifiable without clicking

- Syntax check of `script.py`
- The full data path — collect, sort, build rows, filter — probed against
  the live model with `_dev/revit_probe.py`

### Requires the user, in Revit

The probe cannot render WPF, so the window itself must be clicked:

1. Open a project with several sheets. Run the tool. Window opens, sheets
   listed, sorted naturally (A9 before A10).
2. Type part of a sheet number. List filters. Clear it. Full list returns.
3. Type part of a sheet *name*. List filters on name too.
4. Type text matching nothing. List is empty, no crash.
5. Double-click a sheet. Window closes, that sheet opens.
6. Select a sheet, click **Open Sheet**. Same result.
7. Press Escape. Window closes, active view unchanged.
8. If the model has a placeholder sheet: it is marked, **Open Sheet** is
   disabled, double-click does nothing.
9. Open a family. Run the tool. Family-document alert appears.

A failure at any step goes back to the fix/retest cycle before the tool
leaves `Dev.panel`.

## Definition of done

Per `AGENTS.md`, plus:

- All nine manual test steps pass
- Tool moved from `Dev.panel` to `Sheets.panel`
- Old output-window `List Sheets.pushbutton` deleted
- Docstring `Status:` set to `Shipped`, version and date updated
- `README.md` tool table updated
- Committed and pushed to `main`
