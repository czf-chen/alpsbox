# -*- coding: utf-8 -*-
"""Remember the import source directory so later plots can locate eddy files.

The recorded path survives restarts.
"""
import json
import os

from ..ui import session as _sess

MARK_FILE = os.path.join(os.path.expanduser("~"), ".alpsbox", "last_import.json")


def remember(root: str) -> None:
    try:
        os.makedirs(os.path.dirname(MARK_FILE), exist_ok=True)
        with open(MARK_FILE, "w", encoding="utf-8") as fh:
            json.dump({"root": os.path.abspath(root)}, fh)
    except Exception:
        pass


def recall() -> str:
    try:
        if os.path.isfile(MARK_FILE):
            with open(MARK_FILE, encoding="utf-8") as fh:
                d = json.load(fh)
            r = d.get("root", "")
            if r and os.path.isdir(r):
                return r
    except Exception:
        pass
    return ""
