# -*- coding: UTF-8 -*-
"""Reload pyRevit without leaving the SG Tools tab.

Description:
Restarts the pyRevit session. Does exactly the same thing as
pyRevit tab -> Reload, just without switching tabs while developing.

How to use:
1. Click the button. It takes a few seconds.

Requirements:
- None. Works with no model open.

Notes:
- You only need this after ADDING, RENAMING or MOVING a button, because
  that changes the ribbon.
- You do NOT need it after editing code inside an existing button.
  pyRevit re-reads script.py and any XAML every time you click a button,
  so code changes are live immediately.
- Runs on a clean engine so the previous session's loaded modules do not
  linger.

Limitations / to-do:
- None known.

--------------------------------------------------
Status : Shipped
Version: 1.0
Updated: 2026-07-27
"""

from pyrevit import script
from pyrevit.loader import sessionmgr
from pyrevit.loader import sessioninfo


logger = script.get_logger()
results = script.get_results()

logger.info("Reloading pyRevit...")
sessionmgr.reload_pyrevit()

# Recording the new session id is what pyRevit's own Reload button does.
# It keeps pyRevit's telemetry and session tracking consistent.
results.newsession = sessioninfo.get_session_uuid()
