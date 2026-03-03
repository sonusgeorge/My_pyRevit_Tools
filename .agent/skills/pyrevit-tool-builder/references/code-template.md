# pyRevit Tool Code Template

Standard boilerplate structure used across all challenge days.

## Template

```python
# -*- coding: utf-8 -*-
__title__   = "XX - Tool Name"
__doc__     = """Version = 1.0
Date    = DD.MM.YYYY
________________________________________________________________
Description:
Brief description of what the tool does.
What problem it solves and how.

________________________________________________________________
How-To:
1. Open a supported view (Floor Plan, 3D, etc.)
2. Click the button to launch the tool
3. What happens next...
4. Review results in the pyRevit console

________________________________________________________________
Last Updates:
- [DD.MM.YYYY] v1.0 Initial Release
________________________________________________________________
Author: Sonu George in association with Erik Frits (from LearnRevitAPI.com)"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
from Autodesk.Revit.DB import *
from pyrevit import forms, script

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
doc    = __revit__.ActiveUIDocument.Document #type:Document
uidoc  = __revit__.ActiveUIDocument
app    = __revit__.Application
output = script.get_output()

# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

# Your code here...


#███████████████████████████████████████████████████████████████████████████
# Happy Coding!
```

## Notes

- **Imports**: Keep at the top. Only import what you need. `from Autodesk.Revit.DB import *` covers most Revit API classes.
- **`__doc__`**: Always update with proper description, how-to, and your name before shipping.
- **`.NET imports`**: Only add `clr` / `System.Collections.Generic` when you actually need them (e.g., for `List[ElementId]`).
- **`output`**: Always get `script.get_output()` if you plan to use `print_table`, `print_html`, or `linkify`.
