"""Verbindet Einstellungen, Feiertage, Layout und Ausgabe (ohne GUI)."""
from __future__ import annotations

import os
import re

from . import holidays as H
from .layout import Options, Page, build_page
from .render_pdf import render_pdf
from .settings import region_key


def options_from_settings(s: dict) -> Options:
    cats = []
    if s.get("cat_public", True):
        cats.append(H.PUBLIC)
    if s.get("cat_sub", True):
        cats.append(H.SUB)
    if s.get("cat_partial"):
        cats.append(H.PARTIAL)
    if s.get("cat_obs"):
        cats.append(H.OBS)
    state = s.get("state", "") if s.get("country") == "DE" else ""
    return Options(
        year=int(s["year"]), paper=s["paper"], landscape=bool(s["landscape"]), country=s["country"], state=state,
        lang=s.get("ui_lang", "de"), title=s.get("title", ""), logo=s.get("logo", ""),
        palette=s.get("cal_palette", "Klassisch (wie Vorlage)"), show_cats=tuple(cats),
        excluded=tuple(s.get("excluded", {}).get(region_key(s), [])),
        custom=tuple(tuple(c) for c in s.get("custom", [])),
        week_numbers=s.get("week_numbers", True), workday_row=s.get("workday_row", True),
        workdays_deduct=s.get("workdays_deduct", False), highlight_leap=s.get("highlight_leap", True),
        weekend_wins=s.get("weekend_wins", True), show_bg=s.get("show_bg", True),
        fields=s.get("fields", True), legend=s.get("legend", True))


def make_page(s: dict) -> Page:
    o = options_from_settings(s)
    return build_page(o, region_text=H.region_label(o.country, o.state, o.lang))


def default_filename(s: dict) -> str:
    st = s["state"] if s["country"] == "DE" and s["state"] else ""
    reg = s["country"] + (f"-{st}" if st else "")
    name = f"Kalender_{s['year']}_{reg}_{s['paper']}.pdf"
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)


def export_pdf(s: dict, path: str | None = None) -> str:
    page = make_page(s)
    if not path:
        os.makedirs(s["out_dir"], exist_ok=True)
        path = os.path.join(s["out_dir"], default_filename(s))
    return render_pdf(page, path, title=f"Jahreskalender {s['year']}", editable=bool(s.get("fields", True)))
