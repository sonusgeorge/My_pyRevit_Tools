# SG-Tools

Custom pyRevit tools for civil / infrastructure BIM work.

**Author:** Sonu S George

## Tools

| Panel | Tool | Status | What it does |
|---|---|---|---|
| Sheets | List Sheets | Shipped | Lists every sheet in the model, sorted naturally, with clickable links |

Work-in-progress tools live in the **Dev** panel until they ship.

## Requirements

- Revit (developed against 2026 / 2027)
- [pyRevit](https://github.com/pyrevitlabs/pyRevit) 6.4 or newer
- Scripts run on pyRevit's default **IronPython 2.7** engine

## Install

Clone into your pyRevit extensions folder, using the extension name as the
folder name:

```bash
git clone https://github.com/sonusgeorge/My_pyRevit_Tools.git "%APPDATA%\pyRevit\Extensions\SG-Tools.extension"
```

Then reload pyRevit (pyRevit tab → Reload) and the **SG Tools** tab appears.

To update later:

```bash
git pull origin main
```

followed by a pyRevit reload.

## Developing

Read [AGENTS.md](AGENTS.md) before making changes — it covers the engine
constraints, repo layout, testing setup, and the workflow for shipping a
tool.

If you are on the machine running Revit, you can test API assumptions
against the live model:

```bash
python _dev/revit_probe.py -c "print(doc.Title)"
```

This needs the
[mcp-server-for-revit-python](https://github.com/JotaDeRodriguez/revit-mcp-python)
extension installed with pyRevit Routes enabled.
