# AGENTS.md

This is the primary context file for this repository. Several different
agents work on this project from several different machines. Read this
file fully before doing anything else.

## Project purpose

Designing, building, testing, and shipping reliable pyRevit tools for
civil / infrastructure BIM work.

Treat each tool as a small product. Build the smallest useful version
first, prove that it works, and only then add features and production
quality UI.

## Who you are working with

The user is a **civil BIM engineer**, not a professional programmer, and
is **actively learning Python**. This changes how you should work:

- Explain what you did and why, in plain language, with concrete examples.
- Prefer clear, explicit code over clever or compact code, even when the
  clever version is shorter.
- Comment the non-obvious parts. Assume the reader knows Revit well and
  Python only a little.
- When you use a Python idea the user may not have met yet (list
  comprehension, decorator, context manager, lambda), add a short comment
  saying what it does.
- Do not silently fix something and move on. Say what was wrong, why it
  was wrong, and what the fix does.
- Teaching is part of the job, but do not turn every reply into a lecture.
  Explain what is relevant to the change at hand.

## Communication

- The user often uses speech-to-text. Infer obvious transcription
  mistakes from context (for example, "told" may mean "tool").
- Do not repeatedly correct minor wording or spelling mistakes.
- Ask a concise clarification only when an ambiguity would materially
  change the tool's behavior, data, safety, or architecture.
- Always distinguish clearly between what you verified and what is still
  untested. Never imply a tool was tested in Revit unless it actually ran
  there.

---

## Working environments

Work happens from more than one place. **Check which one you are in
before planning any testing.**

| Environment | Revit available? | How to tell |
|---|---|---|
| The user's Windows PC | Yes | `_dev/revit_probe.py` connects |
| VPS / Claude Code web / any other machine | No | probe fails to connect |

To check, run:

```bash
python _dev/revit_probe.py -c "print(doc.Title)"
```

If that connects, you can test live. If it does not, you are on a machine
without Revit — write code carefully and hand the user a manual test plan.
Never assume Revit is reachable.

### Live testing on the user's PC

The `mcp-server-for-revit-python` extension runs a pyRevit Routes server
on `127.0.0.1:48884`. `_dev/revit_probe.py` sends Python to the live Revit
session and prints the result.

Use it to check assumptions in seconds instead of writing a whole button
and reloading pyRevit:

```bash
python _dev/revit_probe.py my_probe.py
python _dev/revit_probe.py -c "print(len(list(DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet))))"
```

Inside a probe you already have `doc`, `uidoc`, `DB`, and `revit`.

**Rules for probes:**

- Keep them **read-only**. This is the user's live model, not a sandbox.
  Never create, modify, or delete elements in a probe.
- A passing probe is not a passing tool. It proves an API assumption. It
  does not prove the button works. Before shipping, the button itself must
  be clicked once in Revit.
- The probe host runs IronPython 2.7, the same engine our buttons use, so
  language behaviour matches.

---

## Git workflow

The repository is <https://github.com/sonusgeorge/My_pyRevit_Tools.git>
and the working branch is `main`.

On the user's PC the repo lives at, and is loaded directly from:

```
%APPDATA%\pyRevit\Extensions\SG-Tools.extension
```

so a `git pull` changes the live toolbar after a pyRevit reload.

**Start of every session — before changing anything:**

```bash
git pull --rebase origin main
```

**End of every session — before finishing:**

```bash
git add -A
git commit -m "Clear description of what changed"
git push origin main
```

Because work moves between machines, an unpushed change is a lost change.
If the user seems to be wrapping up, remind them to push.

`.gitattributes` normalises line endings to LF. Do not remove it — without
it, files edited on the VPS appear 100% modified on Windows.

---

## Python engine — read this before writing any code

**Write IronPython 2.7 compatible code. This is not optional.**

Verified on 2026-07-27 on the user's machine (Revit 2027, pyRevit 6.4.0):
the engine reports `2.7.12 (IronPython on .NET 10)`. IronPython 2.7
(`IPY2712PR`) is the pyRevit default engine, set in `pyRevitfile`.

### Why not CPython 3

pyRevit switches a script to CPython 3.12 if `#! python3` is the **first
line** of `script.py`. Do not do this.

In pyRevit 6.4, `pyrevit.forms` is a facade (`pyrevit/forms/__init__.py`).
Under IronPython it loads a full backend. Under CPython it loads
`forms/_cpy.py`, where **every single member raises
`PyRevitCPythonNotSupported`** — `alert`, `ask_for_string`, `pick_file`,
`SelectFromList`, `ProgressBar`, `WPFWindow`, all of them. Separately,
`framework.py` only imports the `wpf` module when running IronPython, so
**WPF and XAML do not work under CPython at all.**

The user wants rich WPF interfaces eventually. That requires IronPython.

Only consider CPython for a tool that genuinely needs a pip package such
as `pandas`, and only if it needs no UI beyond the output window. Treat
that as an explicit, discussed exception, not a default.

Do not switch the global engine to IronPython 3.4 either. It is installed,
but the setting is global and would also affect EF-Tools, pyRevit's own
tools, and the Routes extension, which are all IronPython 2 code.

### What IronPython 2.7 means in practice

- **No f-strings.** Use `"{}".format(value)`.
- **Keep `# -*- coding: UTF-8 -*-`** as the first line of every script.
- **Integer division truncates.** `5 / 2` is `2`, not `2.5` — verified in
  this engine. This is a real hazard for quantity and setting-out
  calculations. Use `5.0 / 2`, or `float(a) / b`, whenever a fraction
  matters.
- `print` behaves as a statement; the pyRevit output window is the normal
  way to show results.
- Standard library is Python 2.7's. No `pathlib`, no `dataclasses`,
  no `typing` syntax.
- Third-party pip packages are generally unavailable.

---

## WPF notes

Hard-won findings. Each of these cost real debugging time once.

**Reloading.** You only need to reload pyRevit after adding, renaming, or
moving a *button*, because that changes the ribbon. Editing code inside an
existing button needs no reload — pyRevit re-reads `script.py` and its
XAML on every click. Use **SG Tools → Dev → Reload** when you do need one.

**`DataGrid.RowBackground` breaks selection highlighting.** .NET applies
it as a *local value* on each row, and in WPF a local value beats a style
trigger. An `IsSelected` trigger in `DataGrid.RowStyle` will silently
never paint. Set the row background as a `Setter` inside `RowStyle`
instead, so trigger and default sit at the same precedence level. Also
override `DataGrid.CellStyle` to transparent, or the default cell
background covers the row colour.

**WPF has no `LetterSpacing`.** That is a UWP/WinUI property. Putting it
in XAML makes the whole file fail to parse at runtime.

**XML comments cannot contain `--`.** A comment like `<!-- a -- b -->` is
not well-formed XML and the window will not load. Easy to write by
accident when using dashes as punctuation.

**Binding to Python objects works.** WPF reads plain IronPython attributes
by reflection — `{Binding my_attr}` finds `self.my_attr`. pyRevit's own
`SelectFromList.xaml` relies on this. A typo gives a blank column rather
than an error, so check binding names first when a column is empty.

**Sharing styles between tools, when the time comes.** `forms.WPFWindow`
has a `merge_resource_dict` method, and `_resolve_xaml_source` merges a
`<name>.ResourceDictionary.<locale>.xaml` sitting beside the window XAML
*before* parsing. That is the mechanism to reuse the SG palette across
tools without the `StaticResource` timing problem. Currently the palette
is defined inline in each window's `<Window.Resources>`.

## Repository layout

```
SG-Tools.extension/
├── AGENTS.md                  <- this file, the main context
├── CLAUDE.md                  <- points here
├── extension.json             <- extension metadata
├── .gitattributes             <- line ending normalisation
├── _dev/                      <- dev helpers, ignored by pyRevit
│   └── revit_probe.py
├── lib/                       <- shared code, auto-added to sys.path
│   └── sg/
│       ├── __init__.py
│       └── naming.py
└── SG_Tools.tab/
    ├── bundle.yaml            <- panel order
    ├── Dev.panel/             <- work in progress
    └── Sheets.panel/
        └── List Sheets.pushbutton/
            ├── bundle.yaml
            ├── icon.png
            └── script.py
```

pyRevit only loads `*.tab` folders and `lib/`. Anything else at the root
(`_dev/`, markdown files) is ignored, which is why dev helpers are safe to
keep in the repo.

### The `lib/` folder

pyRevit automatically adds `<extension>/lib` to the Python path for every
script in the extension. So any script can do:

```python
from sg.naming import natural_sort_key
```

with no path setup.

**Move code into `lib/sg/` once it is used by a second tool, not before.**
Speculative helpers written for one imaginary future caller are harder to
delete than to write. Each helper needs a docstring explaining what it
does and why it exists.

---

## The Dev panel convention

Every new tool starts in `SG_Tools.tab/Dev.panel/`.

It moves to its real panel only when it ships — meaning the Definition of
Done below is met, including a real click-test inside Revit. See
`SG_Tools.tab/Dev.panel/README.md` for the move checklist.

This keeps half-finished tools clearly separated from trusted ones, which
matters because these tools run against real project models.

---

## Tool documentation standard

pyRevit builds the button tooltip from the **script docstring**, and the
docstring overrides any `tooltip:` in `bundle.yaml`. So the docstring is
both the code documentation and the user-facing help. Write it for the
person hovering over the button.

Every `script.py` starts with this block:

```python
# -*- coding: UTF-8 -*-
"""One line saying what the tool does.

Description:
Two or three sentences. What it does, and what it changes if anything.

How to use:
1. Numbered steps, starting from what the user must select or open.
2. Keep it short.

Requirements:
- What must be true before running (open project, selection, view type).

Notes:
- Behaviour worth knowing that is not obvious.

Limitations / to-do:
- Known gaps, planned work, anything deliberately not handled.

--------------------------------------------------
Status : In development | Shipped
Version: 1.0
Updated: YYYY-MM-DD
"""
```

Keep it complete but compact — enough that the user knows what the tool
does and what it will touch, without a wall of text. Update `Version` and
`Updated` whenever behaviour changes. Put the button title and author in
`bundle.yaml`, not in the docstring.

---

## Workflow — scale it to the risk

Not every tool needs the same ceremony. Choose the track by what the tool
touches, and say which track you are on.

### Track A — read-only tools

Listing, auditing, reporting, exporting. Nothing in the model changes.

1. Confirm the goal and the output format.
2. Probe the API against the live model if Revit is reachable.
3. Build it in `Dev.panel`.
4. User clicks it once in Revit.
5. Ship it — move the folder, update the docstring status.

No written proposal needed. If the tool turns out to need a transaction,
stop and switch to Track B.

### Track B — tools that modify the model

Creating, renaming, deleting, bulk parameter edits. Anything inside a
transaction. **No shortcuts here.** A bug damages real project data.

**1. Research and propose.** Before writing code:

- Understand the problem, the affected elements, and the expected workflow.
- Check the repo for existing patterns to reuse.
- Research the Revit API — [RevitAPIDocs](https://www.revitapidocs.com/)
  for fast lookup, Autodesk official docs to confirm.
- Confirm the API exists in the targeted Revit version. Never assume.
- Probe the live model to confirm your assumptions.
- Identify constraints: required selection and inputs; document and view
  requirements; transaction and regeneration needs; read-only, linked
  model, group, design option and worksharing limits; cancellation, empty
  result and invalid element behaviour.
- Present a short proposal: recommended approach, main API classes, user
  workflow, risks and edge cases, what is in the first version and what
  waits.

If approaches have meaningful tradeoffs, explain them and recommend one.
Get the user's decision when the choice materially changes the result.

**2. Build the smallest working version** in `Dev.panel`.

- Show the user what will change **before** committing the transaction.
- One transaction, wrapped so a failure rolls back cleanly.
- Handle cancellation without showing an error.
- Never modify more elements than the user expects.
- Skip elaborate UI, settings, and optional features at this stage.

**3. Improve one feature at a time**, re-testing the core workflow after
each change. Do not mix a functional rewrite with UI polish.

**4. Test hard.** Automated checks and probes where possible, then a
manual test plan for the user covering: required model setup; exact steps;
expected results; how to verify the model changed correctly; cancellation;
invalid input; edge cases; undo behaviour; and what error output to send
back if it fails. Fix, retest, repeat.

**5. Productionise and ship.** Clear name, docstring documentation, icon,
`pyrevit.forms` or WPF as the workflow needs, sensible defaults, validation
near each input, clear success/warning/empty/error messages, progress and
cancellation for long operations, and a final run of the whole workflow.
Then move it out of `Dev.panel`.

---

## Coding principles

- Optimise first for correctness, model safety, and readability.
- Follow the conventions already in this repo rather than inventing a new
  pattern per tool.
- Prefer explicit, understandable Revit API code over clever abstractions.
- Keep Revit API objects within valid document and transaction lifetimes.
- Do not silently modify more elements than the user expects.
- Do not swallow unexpected exceptions. Give an actionable message and
  keep the diagnostic detail.
- Treat selections, names, parameter values, and form input as untrusted.
- Preserve the user's existing work and unrelated changes.

## Definition of done

A tool is shipped only when:

- its behaviour and supported Revit versions are documented in the
  docstring;
- the core workflow has been run successfully **inside Revit**;
- normal, cancellation, invalid-input, and edge-case scenarios were checked;
- errors found during testing were fixed and retested;
- the interface is understandable to its intended users;
- remaining limitations are written down in the docstring;
- it has been moved out of `Dev.panel`;
- the work is committed and pushed to `main`.
