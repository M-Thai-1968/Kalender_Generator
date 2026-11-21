#!/usr/bin/env python3
"""KalenderGen - Jahreskalender als editierbares PDF.

Start der Oberflaeche:   python main.py
PDF ohne Oberflaeche:    python main.py --cli --year 2028 --paper A3 --country DE --state BY
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kalender import holidays as H          # noqa: E402
from kalender import service, settings      # noqa: E402
from kalender.layout import PALETTES, PAPER_MM  # noqa: E402


def cli(argv) -> int:
    ap = argparse.ArgumentParser(description="KalenderGen: Jahreskalender als PDF erzeugen")
    ap.add_argument("--cli", action="store_true", help="ohne Oberflaeche ein PDF erzeugen")
    ap.add_argument("--year", type=int, default=settings.defaults()["year"])
    ap.add_argument("--paper", default="A3", choices=list(PAPER_MM))
    ap.add_argument("--portrait", action="store_true", help="Hochformat (Standard: quer)")
    ap.add_argument("--country", default="DE", choices=H.COUNTRY_ORDER)
    ap.add_argument("--state", default="", help="Bundesland-Kuerzel (nur DE), z. B. BY, NW, BE")
    ap.add_argument("--lang", default="de", choices=["de", "en"])
    ap.add_argument("--title", default="")
    ap.add_argument("--logo", default="")
    ap.add_argument("--palette", default=PALETTES[0].name_de, help="Name des Kalender-Farbschemas")
    ap.add_argument("--with-partial", action="store_true", help="regionale Feiertage anzeigen")
    ap.add_argument("--with-obs", action="store_true", help="Gedenk-/Brauchtumstage anzeigen")
    ap.add_argument("--no-fields", action="store_true", help="keine editierbaren Felder")
    ap.add_argument("--no-bg", action="store_true", help="ohne Seitenhintergrund")
    ap.add_argument("--out", default="", help="Zieldatei (Standard: output/Kalender_...pdf)")
    ap.add_argument("--handbook", action="store_true", help="PDF-Handbuch erzeugen (docs/Handbuch_KalenderGen.pdf)")
    ap.add_argument("--list-regions", action="store_true", help="verfuegbare Laender/Bundeslaender auflisten")
    a = ap.parse_args(argv)
    if a.list_regions:
        for c in H.COUNTRY_ORDER:
            print(c, "-", H.COUNTRIES[c].de)
        print("Bundeslaender:", ", ".join(f"{k}={v[0]}" for k, v in H.DE_STATES.items()))
        return 0
    if a.handbook:
        from kalender import handbook
        os.makedirs(handbook.DOCS, exist_ok=True)
        print(handbook.build_handbook(os.path.join(handbook.DOCS, "Handbuch_KalenderGen.pdf")))
        return 0
    s = settings.defaults()
    s.update(year=a.year, paper=a.paper, landscape=not a.portrait, country=a.country, state=a.state,
             ui_lang=a.lang, title=a.title, logo=a.logo, cal_palette=a.palette, cat_partial=a.with_partial,
             cat_obs=a.with_obs, fields=not a.no_fields, show_bg=not a.no_bg, excluded={}, custom=[])
    path = service.export_pdf(s, a.out or None)
    print(path)
    return 0


def main() -> int:
    if any(x in sys.argv for x in ("--cli", "--list-regions", "--handbook")):
        return cli(sys.argv[1:])
    try:
        from kalender import gui
    except ImportError as e:
        print("Die Oberflaeche benoetigt dearpygui (pip install -r requirements.txt):", e)
        return 1
    gui.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
