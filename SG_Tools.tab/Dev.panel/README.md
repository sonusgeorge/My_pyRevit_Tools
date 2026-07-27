# Dev panel

This panel holds two different kinds of thing.

**1. Work-in-progress tools.** A new tool stays here until it is shipped.
Shipping means the Definition of Done in `AGENTS.md` is met — including a
real click-test inside Revit. Then it moves to its real panel.

**2. Permanent development utilities.** Tools that only exist to make
building tools easier, and are never promoted. They stay here forever.
`Reload.pushbutton` is one: it restarts the pyRevit session so new buttons
appear, saving a trip to the pyRevit tab.

The difference shows in the docstring `Status:` line — a WIP tool says
`In development`, a permanent utility says `Shipped` and simply lives here.

## Moving a tool out

When a tool ships:

1. Move the whole `.pushbutton` folder into its real panel
   (for example `Sheets.panel`).
2. Change `Status:` in the script docstring from `In development`
   to `Shipped`.
3. Add the new panel to `layout:` in `SG_Tools.tab/bundle.yaml` if it
   does not exist yet.
4. Reload pyRevit and click the button once in its new home.

## Why a folder and not a flag

pyRevit does have an `is_beta: true` bundle option, but beta tools are
hidden entirely unless `loadbeta` is switched on in pyRevit settings —
which is the opposite of what we want while developing. A visible panel
that is obviously named "Dev" is simpler and harder to forget about.

This README is ignored by pyRevit. Only `*.pushbutton`, `*.pulldown`,
`*.stack` and similar bundle folders are loaded.
