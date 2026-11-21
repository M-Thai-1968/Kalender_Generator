"""Einstellungen (JSON) - bleiben zwischen Programmstarts erhalten."""
from __future__ import annotations

import datetime as dt
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def defaults() -> dict:
    return {
        "year": dt.date.today().year + 1,
        "paper": "A3",
        "landscape": True,
        "country": "DE",
        "state": "",
        "title": "",
        "logo": "",
        "cal_palette": "Klassisch (wie Vorlage)",
        "ui_theme": "Hell",
        "ui_lang": "de",
        "cat_public": True,
        "cat_partial": False,
        "cat_obs": False,
        "cat_sub": True,
        "week_numbers": True,
        "workday_row": True,
        "workdays_deduct": False,
        "highlight_leap": True,
        "weekend_wins": True,
        "show_bg": True,
        "fields": True,
        "legend": True,
        "out_dir": OUTPUT_DIR,
        "excluded": {},          # "DE|BY" -> [deutsche Namen]
        "custom": [],            # [monat, tag, jahr(0=jedes), name]
        "preview_px": 1100,
    }


def load() -> dict:
    s = defaults()
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            s.update(json.load(f))
    except (OSError, ValueError):
        pass
    return s


def save(s: dict) -> None:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def region_key(s: dict) -> str:
    return f"{s['country']}|{s['state'] if s['country'] == 'DE' else ''}"
