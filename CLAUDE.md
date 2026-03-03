# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **pyRevit extension** project — a collection of custom IronPython tools that run inside Autodesk Revit via the pyRevit framework. Tools automate repetitive Revit tasks (element filtering, graphic overrides, reports, view creation, etc.).

## pyRevit Extension Structure

```
My_PyRevit_Tools/
├── extension.json              # Extension metadata (name, author, type)
├── SG Tools.tab/               # Tab shown in Revit ribbon
│   ├── Views.panel/            # View creation, management, visibility
│   ├── Elements.panel/         # Element filtering, selection, modification
│   ├── Sheets.panel/           # Sheet and printing tools
│   ├── Reports.panel/          # Data extraction, tables, export
│   └── Dev.panel/              # Work-in-progress / experimental tools
│       └── ToolName.pushbutton/
│           ├── script.py       # Main tool script (IronPython)
│           └── icon.png        # 96x96 button icon (optional)
```

- **`.tab`** = Revit ribbon tab
- **`.panel`** = group of buttons within a tab
- **`.pushbutton`** = single clickable tool containing `script.py`
- **`Dev.panel`** = staging area for WIP tools; move to the appropriate panel when ready to ship

## Development Methodology

Use the **pyrevit-tool-builder** skill (`.agent/skills/pyrevit-tool-builder/SKILL.md`) which follows a 7-step process: **Plan → Research → Outline → Code → Edit → Stress Test → Ship**.

### Key reference files (load on demand, not upfront):
- `.agent/skills/pyrevit-tool-builder/references/api-patterns.md` — Accumulated Revit API patterns and snippets (read during Research step)
- `.agent/skills/pyrevit-tool-builder/references/code-template.md` — Standard script boilerplate (read during Code step)

## Critical Constraints

### IronPython Compatibility
All scripts run in **pyRevit's IronPython 2.7 runtime** (not CPython). This means:
- No f-strings — use `"text {}".format(val)` or `%` formatting
- No `pathlib`, no `dataclasses`, no Python 3 stdlib modules
- `.NET` interop via `clr` is available and often required
- Many Revit API methods need `.NET` typed collections (e.g., `List[ElementId]`) not Python lists

### Revit API Essentials
- All document modifications require a `Transaction` — start it as late as possible, after validation
- `FilteredElementCollector` is the primary way to query elements — use `.OfClass()` for exact types, `.OfCategory()` for broader categories
- `GroupType.Name` fails in pyRevit — use `Element.Name.GetValue(group_type)` instead
- `uidoc.ActiveView = view` must be called **outside** a Transaction (UI operation)
- Revit internal units are imperial (sq ft for area) — use `UnitUtils.ConvertFromInternalUnits()` for display

### Script Conventions
- Every script starts with `__title__` and `__doc__` metadata header
- Standard variables: `doc`, `uidoc`, `app`, `output` (see code template)
- Use `from Autodesk.Revit.DB import *` for Revit API access
- Use `from pyrevit import forms, script` for UI dialogs and output
- Author line: `Sonu George in association with Erik Frits (from LearnRevitAPI.com)`

## Stress Test Checklist (before shipping any tool)

1. Wrong ViewType — validate `active_view.ViewType` against allowed types
2. No elements found — check empty collections before processing
3. Resource limits — ensure lists (colors, etc.) have enough items
4. Element safety — check `CanBeHidden` or similar before modifying
5. Parameter missing — check `LookupParameter` returns non-None
6. Transaction safety — start Transaction after all validation
7. Dict key collision — use Types (not instances) as dict keys
8. UI cancellation — handle `None` from `forms.SelectFromList` / `forms.alert`

## Skill Improvement Loop

At the end of every shipped tool, analyze the session and suggest updates to:
- `api-patterns.md` — new patterns discovered
- `code-template.md` — template improvements
- Stress test checklist — new edge cases found
