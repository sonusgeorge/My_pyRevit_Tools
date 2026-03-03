---
name: pyrevit-tool-builder
description: Guide for building pyRevit tools using the 7-step process (Plan → Research → Outline → Code → Edit → Stress Test → Ship). Use this skill whenever building a new pyRevit tool, working on a pyRevit challenge day, or creating Revit API automation scripts. Also use when the user mentions pyRevit, Revit API, IronPython scripting, or wants to create/modify pushbuttons. At the Ship step, always analyze the session's learnings and suggest improvements to this skill.
---

# pyRevit Tool Builder

A structured methodology for building pyRevit tools using the 7-step process (inspired by Erik Frits / LearnRevitAPI.com). This skill is designed to evolve — new API patterns and techniques are captured in the references as they are learned.

## When to Use

- Building a new pyRevit tool or pushbutton
- Creating Revit API automation scripts (IronPython)
- Learning or teaching Revit API concepts through hands-on coding
- Working on a pyRevit challenge day

---

## The 7-Step Process

### Step 1: PLAN
> Before touching code — is this worth automating?

Define:
- **The problem**: What repetitive task are we solving?
- **The goal**: What should the tool do?
- **Scope**: What category/elements? What criteria?
- **Feasibility**: Can the Revit API do this?

### Step 2: RESEARCH
> The biggest shortcut. Don't start from scratch.

- Check `references/api-patterns.md` for known patterns and snippets
- Look up Revit API docs for classes/methods needed
- Check existing pyRevit extensions for similar tools
- Break down each API concept clearly (Class | Method | What it does)

### Step 3: OUTLINE
> Write logic before writing code.

- Break the idea into small numbered steps
- Show data flow (what feeds into what)
- Identify inputs, processing, and outputs
- This reveals hidden steps you'd miss mid-code

### Step 4: CODE (Quick & Dirty)
> Build a proof of concept first. Ugly. Slow. No UI. Just make it work.

- Write a **working prototype** — not polished code
- Use the code template from `references/code-template.md` as a starting point
- Focus on: Does it run? Does it produce the expected result?
- Do NOT add error handling, UI polish, or optimizations yet

**Common patterns** (see `references/api-patterns.md` for details):
- `FilteredElementCollector` for getting elements
- `Transaction` for API changes
- `defaultdict` for grouping elements
- `OverrideGraphicSettings` for visual overrides
- `output.print_table` / `output.print_html` for reports

### Step 5: EDIT
> Now clean it up. Refactor, optimize, add proper UI.

- Refactor for readability (variable names, structure)
- Add UI elements (forms, dialogs, output reports)
- Move things to the right place (imports at top, constants before logic)
- Remove dead code, fix formatting
- Consolidate repeated operations outside loops

### Step 6: STRESS TEST
> Break it before your users do.

**Standard tests to check** (apply ALL relevant ones):

| # | Test | How |
|---|------|-----|
| 1 | **Wrong ViewType** | Check `active_view.ViewType` against allowed types |
| 2 | **No elements found** | Check if collection/dict is empty before processing |
| 3 | **Resource limits** | Check if lists (colors, etc.) have enough items |
| 4 | **Element safety** | Check `CanBeHidden` or similar before modifying |
| 5 | **Parameter missing** | Check `LookupParameter` returns non-None |
| 6 | **Transaction safety** | Start Transaction as late as possible |
| 7 | **Dict key collision** | Use Types (not instances) as dict keys to avoid silent overwrites |
| 8 | **UI cancellation** | Check if `forms.SelectFromList` / `forms.alert` returns `None` |

After stress tests, run the **API compatibility analysis**:

```
Analyze my pyRevit / Revit API code
- Identify every Revit API Class, Method, Property... And list in a table
- Check each attribute for changes and deprecations across Revit API 2022-2026
- Highlight parts prone to failures and suggest improvements
- Flag performance issues and recommended solutions
- Give a final score

[PASTE SCRIPT CODE HERE]

IMPORTANT:
- Do not guess API behavior. If not clear or documented - say so.
- The code must be IronPython compatible for pyRevit execution
```

### Step 7: SHIP
> Finalize, reflect, and improve the skill.

1. **Clean up the `__doc__` header** — description, how-to, date, author
2. **Final review** — read the whole script top-to-bottom
3. **Summarize what was learned** — new API concepts, patterns, gotchas

#### 🔄 Skill Improvement Step (CRITICAL)

At the end of every Ship step, you MUST:

1. **Analyze the session's learnings**:
   - What new Revit API classes/methods were used?
   - What new patterns emerged (data flow, error handling, UI)?
   - What mistakes were made and how were they fixed?
   - What reusable code snippets could help future tools?

2. **Compare with existing skill references**:
   - Read `references/api-patterns.md` — any new patterns to add?
   - Read `references/code-template.md` — does the template need updates?
   - Does the stress test checklist need new items?

3. **Suggest specific improvements** to the user:
   - "I'd like to add [X pattern] to the API patterns reference"
   - "The stress test checklist should include [new test]"
   - "The code template could benefit from [change]"

4. **Ask for approval** before making changes to the skill files

---

## Reference Files

Load on demand — don't read all at the start.

- `references/api-patterns.md` — Common Revit API patterns and code snippets. **Read at Step 2** to find relevant patterns.
- `references/code-template.md` — Standard boilerplate template. **Read at Step 4** when starting from scratch.

---

## Key Principles

- **Quick & dirty first** — working code before pretty code
- **The 80/20 rule** — tools don't need to be perfect to be valuable
- **Build the skill as you go** — every tool built makes this skill better
- **IronPython compatibility** — always ensure code works in pyRevit's IronPython runtime
