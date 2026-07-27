# List Sheets WPF Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the output-window presentation of List Sheets with a modal WPF window (dark branded header, live search, double-click to open).

**Architecture:** A `forms.WPFWindow` subclass loads `ListSheetsWindow.xaml` from its own pushbutton folder. `script.py` guards the document, collects and sorts sheets, wraps each in a plain `SheetRow` object, and shows the window modally. WPF binds directly to the Python attributes of those rows. After the dialog closes, the script activates the chosen sheet. Built in `Dev.panel`, promoted to `Sheets.panel` only after the manual tests pass.

**Tech Stack:** IronPython 2.7, pyRevit 6.4 `pyrevit.forms.WPFWindow`, WPF/XAML, Revit API (`FilteredElementCollector`, `ViewSheet`, `UIDocument.ActiveView`).

**Spec:** `docs/superpowers/specs/2026-07-27-list-sheets-wpf-design.md`

## Global Constraints

- **IronPython 2.7 only.** No f-strings — use `"{}".format(x)`. Every `.py` file starts with `# -*- coding: UTF-8 -*-`. Integer division truncates (`5 / 2 == 2`).
- **Read-only tool.** No `Transaction` anywhere. Setting `uidoc.ActiveView` is a view change, not a model change.
- **No new dependencies.** Standard library and pyRevit only.
- **Font:** Segoe UI. **Window:** 560×620 default, min 420×320, centred.
- **Palette (exact):** header `#1F2A37`, body `#FFFFFF`, surface `#FAFBFC`, border `#E8EAED`, accent `#1565C0`, selection `#EAF3FB`, dim text `#6B7280`.
- **Tests must run without Revit** so they also work on the VPS. No pytest — plain asserts run by `python tests/<file>.py`.
- Every task ends with a commit. Push at the end of the session.

### Deviation from the spec, already decided

The spec asks for `letter-spacing: 1.6` on the `SG TOOLS` eyebrow text. **WPF has no `LetterSpacing` property** (that is a UWP/WinUI feature) and using it would make the XAML fail to parse. The eyebrow is rendered as plain uppercase 10px text at 60% opacity instead. Do not attempt to add letter spacing.

## File Structure

| File | Responsibility |
|---|---|
| `lib/sg/naming.py` (modify) | Add `matches_search` — pure, testable text matching |
| `tests/test_naming.py` (create) | Plain-assert tests for `lib/sg/naming.py`, runs anywhere |
| `SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/bundle.yaml` (create) | Button title and author |
| `SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/icon.png` (create) | Copied from the existing tool |
| `SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/ListSheetsWindow.xaml` (create) | Window layout, palette, control styles |
| `SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/script.py` (create) | Guards, data assembly, event handlers |
| `README.md` (modify, Task 3) | Tool table |

---

### Task 1: Add and test `matches_search`

The window filters rows as the user types. That matching is pure text logic, so it belongs in `lib/` where it can be tested without Revit — this is a testability decision, not speculative reuse.

**Files:**
- Modify: `lib/sg/naming.py` (append)
- Create: `tests/test_naming.py`

**Interfaces:**
- Consumes: `natural_sort_key(text)` from `lib/sg/naming.py` (already exists)
- Produces: `matches_search(search_text, *values) -> bool`. Returns `True` when `search_text` is empty/whitespace/None, or when its lowercased, stripped form appears in any of `values`. `None` entries in `values` are skipped, never raise.

- [ ] **Step 1: Write the failing test**

Create `tests/test_naming.py`:

```python
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
```

- [ ] **Step 2: Run it and confirm it fails**

```bash
python tests/test_naming.py
```

Expected: `ImportError: cannot import name 'matches_search' from 'sg.naming'`

On the user's PC, `python` may not be on PATH. Use the venv interpreter:
`"$APPDATA/pyRevit/Extensions/mcp-server-for-revit-python.extension/.venv/Scripts/python.exe" tests/test_naming.py`

- [ ] **Step 3: Write the implementation**

Append to `lib/sg/naming.py`:

```python


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
```

- [ ] **Step 4: Run the tests and confirm they pass**

```bash
python tests/test_naming.py
```

Expected: 13 `ok` lines, then `13 checks passed`, exit code 0.

- [ ] **Step 5: Confirm it works on IronPython 2.7 too**

The tests run on CPython 3. The tool runs on IronPython 2.7. Verify the function behaves identically there:

Create a scratch probe file and run it:

```python
from sg.naming import matches_search
print("empty  : " + str(matches_search("", "C-101", "Site Plan")))
print("number : " + str(matches_search("101", "C-101", "Site Plan")))
print("name   : " + str(matches_search("SITE", "C-101", "Site Plan")))
print("miss   : " + str(matches_search("zzz", "C-101", "Site Plan")))
print("none   : " + str(matches_search("101", None, "C-101")))
```

```bash
python _dev/revit_probe.py <scratch-probe-path>
```

Expected: `True, True, True, False, True`. If Revit is not running, skip this step and note it as unverified.

- [ ] **Step 6: Commit**

```bash
git add lib/sg/naming.py tests/test_naming.py
git commit -m "Add matches_search helper with tests"
```

---

### Task 2: Build the WPF window in Dev.panel

**Files:**
- Create: `SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/bundle.yaml`
- Create: `SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/icon.png` (copy)
- Create: `SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/ListSheetsWindow.xaml`
- Create: `SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/script.py`

**Interfaces:**
- Consumes: `natural_sort_key(text)`, `matches_search(search_text, *values)` from `sg.naming`
- Produces: `SheetRow` with attributes `number`, `name`, `is_placeholder`, `element_id`, `display_number`; and `ListSheetsWindow(rows)` exposing `selected_id` (an `ElementId` or `None` after the dialog closes)

**Critical:** the XAML `Binding` paths and `x:Name` values must match the Python attribute and method names exactly. WPF binds to Python attributes by reflection under IronPython — a typo shows as a blank column, not an error.

- [ ] **Step 1: Create the button folder and copy the icon**

```bash
mkdir -p "SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton"
cp "SG_Tools.tab/Sheets.panel/List Sheets.pushbutton/icon.png" "SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/icon.png"
```

- [ ] **Step 2: Write `bundle.yaml`**

Create `SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/bundle.yaml`:

```yaml
title: List Sheets WPF
author: Sonu S George

# No `tooltip:` -- pyRevit builds the tooltip from the script docstring,
# which overrides this file. See AGENTS.md.
```

- [ ] **Step 3: Write the XAML**

Create `SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/ListSheetsWindow.xaml`:

```xml
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="List Sheets"
        Height="620" Width="560"
        MinHeight="320" MinWidth="420"
        WindowStartupLocation="CenterScreen"
        ShowInTaskbar="False"
        FontFamily="Segoe UI"
        Background="#FFFFFF">

  <Window.Resources>
    <!-- ================================================================
         SG-Tools palette. Every colour in this window is defined here so
         it can be lifted into a shared ResourceDictionary later without
         hunting through the markup.
         ================================================================ -->
    <SolidColorBrush x:Key="SgHeader"    Color="#1F2A37"/>
    <SolidColorBrush x:Key="SgBody"      Color="#FFFFFF"/>
    <SolidColorBrush x:Key="SgSurface"   Color="#FAFBFC"/>
    <SolidColorBrush x:Key="SgBorder"    Color="#E8EAED"/>
    <SolidColorBrush x:Key="SgAccent"    Color="#1565C0"/>
    <SolidColorBrush x:Key="SgSelection" Color="#EAF3FB"/>
    <SolidColorBrush x:Key="SgTextDim"   Color="#6B7280"/>
    <SolidColorBrush x:Key="SgText"      Color="#1A1A1A"/>
    <SolidColorBrush x:Key="SgHint"      Color="#9AA0A6"/>

    <!-- Primary button: dark pill with rounded corners. WPF buttons are
         square by default, so this needs a full ControlTemplate. -->
    <Style x:Key="SgPrimaryButton" TargetType="Button">
      <Setter Property="Foreground" Value="White"/>
      <Setter Property="FontSize" Value="12"/>
      <Setter Property="Padding" Value="16,6"/>
      <Setter Property="Cursor" Value="Hand"/>
      <Setter Property="Template">
        <Setter.Value>
          <ControlTemplate TargetType="Button">
            <Border x:Name="back"
                    Background="{StaticResource SgHeader}"
                    CornerRadius="4"
                    Padding="{TemplateBinding Padding}">
              <ContentPresenter HorizontalAlignment="Center"
                                VerticalAlignment="Center"/>
            </Border>
            <ControlTemplate.Triggers>
              <Trigger Property="IsMouseOver" Value="True">
                <Setter TargetName="back" Property="Background" Value="#2C3A4B"/>
              </Trigger>
              <Trigger Property="IsEnabled" Value="False">
                <Setter TargetName="back" Property="Background" Value="#C9CDD3"/>
              </Trigger>
            </ControlTemplate.Triggers>
          </ControlTemplate>
        </Setter.Value>
      </Setter>
    </Style>

    <!-- Column headers: flat, with the dark rule underneath. -->
    <Style x:Key="SgColumnHeader" TargetType="DataGridColumnHeader">
      <Setter Property="Background" Value="{StaticResource SgBody}"/>
      <Setter Property="Foreground" Value="{StaticResource SgText}"/>
      <Setter Property="FontWeight" Value="SemiBold"/>
      <Setter Property="FontSize" Value="12"/>
      <Setter Property="Padding" Value="12,8"/>
      <Setter Property="HorizontalContentAlignment" Value="Left"/>
      <Setter Property="BorderBrush" Value="{StaticResource SgHeader}"/>
      <Setter Property="BorderThickness" Value="0,0,0,2"/>
    </Style>
  </Window.Resources>

  <Grid>
    <Grid.RowDefinitions>
      <RowDefinition Height="Auto"/>  <!-- branded header -->
      <RowDefinition Height="Auto"/>  <!-- search -->
      <RowDefinition Height="*"/>     <!-- grid -->
      <RowDefinition Height="Auto"/>  <!-- footer -->
    </Grid.RowDefinitions>

    <!-- ===================== HEADER ===================== -->
    <Border Grid.Row="0" Background="{StaticResource SgHeader}" Padding="14,11">
      <StackPanel>
        <!-- No letter-spacing: WPF has no LetterSpacing property. -->
        <TextBlock Text="SG TOOLS"
                   Foreground="#99FFFFFF"
                   FontSize="10"/>
        <TextBlock Text="List Sheets"
                   Foreground="White"
                   FontSize="15"
                   FontWeight="SemiBold"
                   Margin="0,1,0,0"/>
      </StackPanel>
    </Border>

    <!-- ===================== SEARCH ===================== -->
    <Border Grid.Row="1"
            Background="{StaticResource SgSurface}"
            BorderBrush="{StaticResource SgBorder}"
            BorderThickness="0,0,0,1"
            Padding="14,11">
      <Grid>
        <TextBox x:Name="search_box"
                 FontSize="12.5"
                 Padding="8,5"
                 BorderBrush="{StaticResource SgBorder}"
                 BorderThickness="1"
                 Background="White"
                 TextChanged="on_search_changed"/>
        <!-- WPF has no placeholder property. This TextBlock sits on top of
             the empty TextBox and hides as soon as any text is typed. -->
        <TextBlock Text="Search sheets..."
                   Foreground="{StaticResource SgHint}"
                   FontSize="12.5"
                   Margin="10,0,0,0"
                   VerticalAlignment="Center"
                   IsHitTestVisible="False">
          <TextBlock.Style>
            <Style TargetType="TextBlock">
              <Setter Property="Visibility" Value="Collapsed"/>
              <Style.Triggers>
                <DataTrigger Binding="{Binding Text, ElementName=search_box}" Value="">
                  <Setter Property="Visibility" Value="Visible"/>
                </DataTrigger>
              </Style.Triggers>
            </Style>
          </TextBlock.Style>
        </TextBlock>
      </Grid>
    </Border>

    <!-- ===================== SHEET GRID ===================== -->
    <DataGrid x:Name="sheet_grid"
              Grid.Row="2"
              AutoGenerateColumns="False"
              IsReadOnly="True"
              CanUserAddRows="False"
              CanUserDeleteRows="False"
              CanUserResizeRows="False"
              CanUserSortColumns="False"
              SelectionMode="Single"
              SelectionUnit="FullRow"
              HeadersVisibility="Column"
              GridLinesVisibility="None"
              BorderThickness="0"
              Background="{StaticResource SgBody}"
              RowBackground="{StaticResource SgBody}"
              ColumnHeaderStyle="{StaticResource SgColumnHeader}"
              MouseDoubleClick="on_row_double_click"
              SelectionChanged="on_selection_changed">

      <DataGrid.RowStyle>
        <Style TargetType="DataGridRow">
          <Setter Property="Height" Value="26"/>
          <Style.Triggers>
            <Trigger Property="IsSelected" Value="True">
              <Setter Property="Background" Value="{StaticResource SgSelection}"/>
              <Setter Property="Foreground" Value="{StaticResource SgText}"/>
            </Trigger>
          </Style.Triggers>
        </Style>
      </DataGrid.RowStyle>

      <!-- Without this, the default system highlight paints over the
           row background and the selection colour above is invisible. -->
      <DataGrid.CellStyle>
        <Style TargetType="DataGridCell">
          <Setter Property="Background" Value="Transparent"/>
          <Setter Property="BorderThickness" Value="0"/>
          <Setter Property="Foreground" Value="{StaticResource SgText}"/>
          <Style.Triggers>
            <Trigger Property="IsSelected" Value="True">
              <Setter Property="Background" Value="Transparent"/>
              <Setter Property="Foreground" Value="{StaticResource SgText}"/>
            </Trigger>
          </Style.Triggers>
        </Style>
      </DataGrid.CellStyle>

      <DataGrid.Columns>
        <DataGridTextColumn Header="Sheet Number"
                            Binding="{Binding display_number}"
                            Width="150">
          <DataGridTextColumn.ElementStyle>
            <Style TargetType="TextBlock">
              <Setter Property="Foreground" Value="{StaticResource SgAccent}"/>
              <Setter Property="FontWeight" Value="SemiBold"/>
              <Setter Property="Margin" Value="12,0,0,0"/>
              <Setter Property="VerticalAlignment" Value="Center"/>
            </Style>
          </DataGridTextColumn.ElementStyle>
        </DataGridTextColumn>

        <DataGridTextColumn Header="Sheet Name"
                            Binding="{Binding name}"
                            Width="*">
          <DataGridTextColumn.ElementStyle>
            <Style TargetType="TextBlock">
              <Setter Property="Margin" Value="12,0,0,0"/>
              <Setter Property="VerticalAlignment" Value="Center"/>
              <Setter Property="TextTrimming" Value="CharacterEllipsis"/>
            </Style>
          </DataGridTextColumn.ElementStyle>
        </DataGridTextColumn>
      </DataGrid.Columns>
    </DataGrid>

    <!-- ===================== FOOTER ===================== -->
    <Border Grid.Row="3"
            Background="{StaticResource SgSurface}"
            BorderBrush="{StaticResource SgBorder}"
            BorderThickness="0,1,0,0"
            Padding="14,9">
      <Grid>
        <TextBlock x:Name="count_label"
                   Text=""
                   FontSize="11.5"
                   Foreground="{StaticResource SgTextDim}"
                   VerticalAlignment="Center"
                   HorizontalAlignment="Left"/>
        <Button x:Name="open_button"
                Content="Open Sheet"
                Style="{StaticResource SgPrimaryButton}"
                HorizontalAlignment="Right"
                IsEnabled="False"
                Click="on_open_click"/>
      </Grid>
    </Border>

  </Grid>
</Window>
```

- [ ] **Step 4: Write `script.py`**

Create `SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/script.py`:

```python
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
Status : In development
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
```

- [ ] **Step 5: Syntax-check the script**

```bash
python -c "import ast,io; ast.parse(io.open('SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/script.py', encoding='utf-8').read()); print('script OK')"
```

Expected: `script OK`

- [ ] **Step 6: Check the XAML is well-formed**

A malformed XAML file fails at runtime with an unhelpful error, so parse it first:

```bash
python -c "import xml.etree.ElementTree as ET; ET.parse('SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/ListSheetsWindow.xaml'); print('xaml well-formed')"
```

Expected: `xaml well-formed`

This proves the XML is valid. It does **not** prove WPF accepts every property — only Revit can confirm that.

A linter may flag `xml.etree.ElementTree` as unsafe against XXE and
billion-laughs attacks. That warning is about parsing *untrusted* XML.
Here the input is a file we authored, in our own repo, parsed at
development time only. The safe alternative, `defusedxml`, is a
third-party package, and this project deliberately takes no new
dependencies. Keep the stdlib parser.

- [ ] **Step 7: Probe the data path against the live model**

This tests everything except the window. Create a scratch probe:

```python
from sg.naming import natural_sort_key, matches_search

sheets = list(DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet).ToElements())
sheets.sort(key=lambda s: natural_sort_key(s.SheetNumber))
print("sheets found: " + str(len(sheets)))

rows = []
for s in sheets:
    number = s.SheetNumber
    name = s.Name
    display = number + " (placeholder)" if s.IsPlaceholder else number
    rows.append((number, name, display, s.IsPlaceholder))

for r in rows[:10]:
    print("  " + r[2] + " | " + r[1])

visible = [r for r in rows if matches_search("1", r[0], r[1])]
print("rows matching '1': " + str(len(visible)) + " of " + str(len(rows)))
visible = [r for r in rows if matches_search("", r[0], r[1])]
print("rows matching '' : " + str(len(visible)) + " of " + str(len(rows)))
```

```bash
python _dev/revit_probe.py <scratch-probe-path>
```

Expected: the sheet count matches the model, rows are listed in natural order, the empty search returns every row. If Revit is not running, skip and record this as unverified.

- [ ] **Step 8: Reload pyRevit and hand over for manual testing**

Tell the user: pyRevit tab → Reload, then **SG Tools → Dev → List Sheets WPF**.

Give them these nine checks from the spec:

1. Window opens, sheets listed, natural order (A9 before A10).
2. Type part of a sheet number → list filters. Clear → full list returns.
3. Type part of a sheet **name** → list filters on name too.
4. Type nonsense → empty list, no crash, footer shows `0 of N sheets`.
5. Double-click a sheet → window closes, that sheet opens.
6. Select a sheet, click **Open Sheet** → same result.
7. Press Escape → window closes, active view unchanged.
8. Placeholder sheet (if any) → marked, **Open Sheet** greyed out, double-click does nothing.
9. Open a family, run the tool → family-document alert appears.

**Known risk to watch for:** if both columns are blank but rows exist, WPF binding is not reaching the Python attributes. The fix is a name mismatch between the `Binding` paths in the XAML and the `SheetRow` attributes — check `display_number` and `name` first.

- [ ] **Step 9: Fix anything the manual test found, then commit**

Do not proceed to Task 3 until all nine checks pass.

```bash
git add "SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton"
git commit -m "Add WPF sheet browser in Dev panel"
```

---

### Task 3: Promote to Sheets.panel and retire the old tool

Only start once every check in Task 2 Step 8 passes.

**Files:**
- Delete: `SG_Tools.tab/Sheets.panel/List Sheets.pushbutton/` (the output-window version)
- Move: `SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton/` → `SG_Tools.tab/Sheets.panel/List Sheets.pushbutton/`
- Modify: the moved `bundle.yaml` and `script.py`
- Modify: `README.md`

- [ ] **Step 1: Move the folder, replacing the old tool**

```bash
git rm -r --quiet "SG_Tools.tab/Sheets.panel/List Sheets.pushbutton"
git mv "SG_Tools.tab/Dev.panel/List Sheets WPF.pushbutton" "SG_Tools.tab/Sheets.panel/List Sheets.pushbutton"
```

- [ ] **Step 2: Fix the button title**

In `SG_Tools.tab/Sheets.panel/List Sheets.pushbutton/bundle.yaml`, change:

```yaml
title: List Sheets WPF
```

to:

```yaml
title: List Sheets
```

- [ ] **Step 3: Mark it shipped**

In `SG_Tools.tab/Sheets.panel/List Sheets.pushbutton/script.py`, change:

```
Status : In development
```

to:

```
Status : Shipped
```

- [ ] **Step 4: Update the README tool table**

In `README.md`, replace the List Sheets row with:

```markdown
| Sheets | List Sheets | Shipped | Searchable window listing every sheet; double-click to open |
```

- [ ] **Step 5: Reload and confirm in its new home**

Tell the user: pyRevit → Reload, then check **SG Tools → Sheets → List Sheets** opens the new window, and that the **Dev** panel is now empty (an empty panel simply does not render — that is expected, not an error).

- [ ] **Step 6: Commit and push**

```bash
git add -A
git commit -m "Ship WPF sheet browser, retire output-window version"
git push origin main
```

---

## Self-review notes

Checked against `docs/superpowers/specs/2026-07-27-list-sheets-wpf-design.md`:

- Every spec section maps to a task. Guards, sorting, filtering, placeholder handling, the palette, window sizing, the nine manual tests, and the Definition of Done all appear above.
- `SheetRow` attribute names are identical in the XAML bindings (Task 2 Step 3), the class definition (Step 4), and the Interfaces block.
- `matches_search(search_text, *values)` has the same signature in Task 1 and both call sites in Task 2.
- One spec deviation, documented in Global Constraints: no letter-spacing on the eyebrow text, because WPF lacks the property.
- One spec detail made concrete: the footer reads `"N sheets"` unfiltered and `"N of M sheets"` when filtered. The spec did not pin this down.
