# CLAUDE.md

**Read [AGENTS.md](AGENTS.md) first and follow it.**

`AGENTS.md` is the single source of truth for this repository. Everything
about how to work here lives there — the Python engine constraints, the
git workflow, the live Revit testing setup, the Dev panel convention, the
documentation standard, and the definition of done.

This file exists only so that Claude Code reliably picks up that context.
Do not duplicate rules here; they will drift. Add them to `AGENTS.md`.

## The three things people forget

1. **`git pull --rebase origin main` before starting, `git push` before
   finishing.** Work moves between the user's PC, a VPS, and Claude Code
   web. Unpushed work is lost work.

2. **Write IronPython 2.7 code.** No f-strings, `5 / 2` is `2`, and
   `pyrevit.forms` breaks completely under CPython. See the engine section
   in `AGENTS.md`.

3. **Revit is only reachable from the user's PC.** Check with
   `python _dev/revit_probe.py -c "print(doc.Title)"` before planning any
   live test.
