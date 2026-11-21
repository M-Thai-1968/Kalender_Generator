"""Betriebssystem-Helfer: Datei oeffnen / drucken (Windows, Linux, macOS)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys


def open_file(path: str) -> None:
    if sys.platform.startswith("win"):
        os.startfile(path)                                    # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def print_file(path: str) -> str:
    """Schickt die Datei an den Standarddrucker. Rueckgabe: kurze Statusmeldung."""
    if sys.platform.startswith("win"):
        try:
            os.startfile(path, "print")                       # type: ignore[attr-defined]
            return "print"
        except OSError:
            os.startfile(path)                                # type: ignore[attr-defined]
            return "open"
    lp = shutil.which("lp") or shutil.which("lpr")
    if lp:
        subprocess.Popen([lp, path])
        return "print"
    open_file(path)
    return "open"
