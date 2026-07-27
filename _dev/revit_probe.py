# -*- coding: UTF-8 -*-
"""Send a Python snippet to the running Revit session and print the result.

This is a DEVELOPMENT helper, not a pyRevit tool. It lives in `_dev/` so
pyRevit ignores it (pyRevit only loads `*.tab` folders and `lib/`).

It talks to the pyRevit Routes server provided by the
`mcp-server-for-revit-python` extension, which must be installed and
running inside Revit.

WHAT IT IS FOR
    Checking a Revit API assumption in seconds instead of writing a whole
    button, reloading pyRevit, and clicking it. For example: "does this
    collector return what I think?", "does this property exist in 2027?"

REQUIREMENTS
    - Revit is open on this machine with a document loaded
    - pyRevit Routes enabled on 127.0.0.1:48884

IMPORTANT
    - The code runs inside YOUR live Revit session against YOUR open model.
    - Keep probes READ-ONLY. Do not create, modify or delete elements here.
    - The Routes host runs IronPython 2.7, which is the same engine our
      buttons use, so behaviour matches. It is still not a substitute for
      clicking the real button once before shipping.

USAGE
    python _dev/revit_probe.py probe.py      # run a file
    python _dev/revit_probe.py -c "print(doc.Title)"

AVAILABLE NAMES INSIDE THE PROBE
    doc, uidoc, DB, revit    (already imported for you)

    This extension's `lib/` folder is added to the path automatically, so
    `from sg.naming import natural_sort_key` works in a probe just as it
    does in a real button.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

ENDPOINT = "http://127.0.0.1:48884/revit_mcp/execute_code/"
STATUS = "http://127.0.0.1:48884/revit_mcp/status/"
TIMEOUT = 60

# The probe executes inside the *routes* extension, so this extension's
# `lib/` folder is NOT on its search path -- `from sg.naming import ...`
# would fail with ImportError. Prepending it here means probes can test
# our shared helpers exactly as a real button would use them.
_EXTENSION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LIB_PATH = os.path.join(_EXTENSION_ROOT, "lib")

_PREAMBLE = (
    "import sys\n"
    "if {lib!r} not in sys.path:\n"
    "    sys.path.insert(0, {lib!r})\n"
).format(lib=_LIB_PATH)


def _post(url, payload, timeout=TIMEOUT):
    """POST a dict as JSON and return the decoded response.

    A failing probe usually comes back as HTTP 500 with the real traceback
    in the body, so read the body on HTTPError instead of discarding it.
    """
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return json.loads(raw)
        except ValueError:
            return {"error": "HTTP {}: {}".format(exc.code, raw)}


def check_revit():
    """Return a short status string, or None if Revit is unreachable."""
    try:
        with urllib.request.urlopen(STATUS, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("document_title") or "(no document)"
    except Exception:
        return None


def run(code, description="probe"):
    """Execute code in Revit. Returns the process exit code."""
    doc_title = check_revit()
    if doc_title is None:
        print(
            "Cannot reach Revit on 127.0.0.1:48884.\n"
            "  - Is Revit open on this machine?\n"
            "  - Is the mcp-server-for-revit-python extension loaded?\n"
            "  - Are Routes enabled in pyRevit settings?\n"
            "If you are on the VPS or Claude Code web, Revit is not "
            "available here -- write a manual test plan instead.",
            file=sys.stderr,
        )
        return 2

    print("Revit document: {}".format(doc_title))
    print("-" * 60)

    try:
        result = _post(ENDPOINT, {
            "code": _PREAMBLE + code,
            "description": description,
            "use_transaction": False,
        })
    except urllib.error.URLError as exc:
        print("Request failed: {}".format(exc), file=sys.stderr)
        return 2

    # The route returns either a success payload, an error payload with a
    # traceback, or a routes-level exception.
    if "exception" in result:
        print(result["exception"].get("message", result["exception"]),
              file=sys.stderr)
        return 1

    if result.get("status") == "error" or "error" in result:
        print(result.get("traceback") or result.get("error", ""), file=sys.stderr)
        return 1

    output = result.get("output", "")
    print(output if output else "(the probe printed nothing)")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Run read-only Python inside the live Revit session."
    )
    parser.add_argument("file", nargs="?", help="path to a .py file to run")
    parser.add_argument("-c", "--code", help="inline code to run")
    args = parser.parse_args()

    if args.code:
        code = args.code
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as handle:
            code = handle.read()
    else:
        parser.error("give a file path or -c \"code\"")

    return run(code, description=args.file or "inline probe")


if __name__ == "__main__":
    sys.exit(main())
