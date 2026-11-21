#!/usr/bin/env bash
# KalenderGen - Starter fuer Linux (z. B. Linux Mint)
# Legt beim ersten Start .venv an und installiert die Pakete (Internet nur dann noetig).
cd "$(dirname "$0")" || exit 1

PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "Python 3.9 oder neuer wurde nicht gefunden."
  echo "Installation unter Linux Mint/Ubuntu:  sudo apt install python3 python3-venv python3-pip"
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  echo "[KalenderGen] Erster Start: lege .venv an ..."
  if ! "$PY" -m venv .venv; then
    rm -rf .venv
    echo "Das Modul venv fehlt. Installation:  sudo apt install python3-venv"
    exit 1
  fi
fi

# shellcheck disable=SC1091
. .venv/bin/activate
STAMP=".venv/.deps_ok"
if [ ! -f "$STAMP" ] || [ requirements.txt -nt "$STAMP" ]; then
  echo "[KalenderGen] Installiere Pakete ..."
  if ls wheels/*.whl >/dev/null 2>&1; then
    pip install --disable-pip-version-check --no-index --find-links wheels -r requirements.txt || exit 1
  else
    pip install --disable-pip-version-check --upgrade pip >/dev/null 2>&1
    pip install --disable-pip-version-check -r requirements.txt || {
      echo "Paketinstallation fehlgeschlagen (Internet?). Alternativ .whl-Dateien in den Ordner wheels/ legen."
      exit 1
    }
  fi
  touch "$STAMP"
fi

exec python main.py "$@"
