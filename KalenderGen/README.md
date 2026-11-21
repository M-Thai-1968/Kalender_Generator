# KalenderGen - Jahreskalender als editierbares PDF

Jahresplaner mit 12 Monatsspalten x 31 Zeilen (Layout nach Excel-Vorlage): Wochentage, Kalenderwochen,
Feiertage, Schalttag, Arbeitstage je Monat. Ausgabe als PDF in A6 / A5 / A4 / A3 / A2 / A1 (quer oder hoch)
mit editierbaren Notizfeldern je Tag. Python + Dear PyGui + ReportLab, Windows und Linux.

## Start
- Windows: `Windows_starter.bat` doppelklicken (auch ohne Python-Installation; beim ersten Start wird
  Python portabel in `.venv` geladen, Internet nötig).
- Linux: `./Linux_starter.sh` (einmalig `chmod +x Linux_starter.sh`).
- Ohne Oberfläche: `python main.py --cli --year 2028 --paper A3 --country DE --state BY`
  (`python main.py --help`, `--list-regions`).
- Handbuch als PDF: in der Oberfläche *Hilfe > Handbuch als PDF speichern* (nimmt die GUI-Screenshots
  automatisch auf) oder `python main.py --handbook`.
- Offline-Installation: `.whl`-Dateien von reportlab, dearpygui, Pillow, numpy in `wheels/` legen.

## Aufbau
- `kalender/holidays.py` - Feiertage aus Regeln berechnet (offline): DE (16 Länder), AT, CH, FR, IT, ES, NL, BE,
  LU, GB (England/Wales, Schottland), IE, PL, CZ, DK, SE, NO, FI, PT, GR, HU, TH, US
- `kalender/layout.py` - Seitenlayout + 12 Kalender-Farbschemata (identisch für PDF und Vorschau)
- `kalender/render_pdf.py`, `render_preview.py` - PDF (reportlab, AcroForm-Felder) und Vorschau (PIL)
- `kalender/gui.py`, `themes.py`, `i18n.py` - Oberfläche, 14 Farbschemata (Hell, Dunkel + 12), de/en
- `kalender/help_content.py`, `handbook.py` - Hilfe und PDF-Handbuch
- `tests/` - `python tests/test_core.py` (Feiertage, Layout, PDF), `python tests/test_gui_stub.py` (GUI-Logik mit Stub)
- `beispiele/` - fertige Beispiel-PDFs

## Hinweise zu den Feiertagen
Thailand: buddhistische Feiertage folgen dem Mondkalender; 2024-2026 offizielle Daten, sonst Näherung (±1 Tag).
Regierungs-Sondertage, einmalige Bank Holidays (UK) und kantonale/regionale Besonderheiten (CH, ES, US-Staaten)
sind nicht enthalten, lassen sich aber als *Eigene Feiertage* ergänzen. Bitte vor dem Druck prüfen.
