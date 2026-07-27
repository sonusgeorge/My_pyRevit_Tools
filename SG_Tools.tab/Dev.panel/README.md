# Dev panel

Work-in-progress tools live here.

A tool stays in this panel until it is shipped. Shipping means the
Definition of Done in `AGENTS.md` is met — including a real click-test
inside Revit.

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
