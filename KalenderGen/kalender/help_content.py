"""Inhalt von Hilfe-Fenster und PDF-Handbuch (Deutsch).

Jeder Abschnitt: Titel, Absaetze, Bilder [(Dateiname, Bildunterschrift)].
Bilder liegen in docs/screens/. GUI-Screenshots (gui_*.png) entstehen
automatisch im Programm (Hilfe > Screenshots neu aufnehmen); die
Kalenderbeispiele (example_*.png) werden vom Programm selbst gezeichnet.
"""

SECTIONS = [
    {
        "title": "1. Überblick",
        "paras": [
            "KalenderGen erzeugt einen Jahresplaner im Stil einer Excel-Vorlage: zwölf Monatsspalten mit je 31 Zeilen. "
            "Jede Zelle zeigt Tageszahl und Wochentag; Samstage und Sonntage sind farbig, Feiertage werden "
            "hervorgehoben und mit Namen beschriftet. Montage tragen die ISO-Kalenderwoche. Nicht vorhandene Tage "
            "(z. B. 31. April) sind grau, der Schalttag ist markiert. Die Fußzeile zählt die Mo-Fr-Tage je Monat.",
            "Das Ergebnis ist ein PDF in einem der Formate A6, A5, A4, A3, A2 oder A1 (quer oder hoch). Jeder Tag hat "
            "ein eigenes Notizfeld, das im PDF-Viewer direkt ausgefüllt werden kann (editierbares PDF). Das PDF "
            "kann ohne Änderung gedruckt werden.",
            "Das Programm arbeitet vollständig offline: Alle Feiertage werden aus Regeln berechnet (Ostern, "
            "feste Daten, n-ter Wochentag usw.). Eine Internetverbindung wird nur für die Ersteinrichtung "
            "(Installation der Python-Pakete) benötigt.",
        ],
        "shots": [("example_a4.png", "Beispiel: Kalender 2028 (A4 quer, Bayern) - die Vorschau im Programm zeigt genau dieses Bild.")],
    },
    {
        "title": "2. Installation und Start",
        "paras": [
            "Windows: Doppelklick auf Windows_starter.bat. Ist auf dem PC kein Python installiert, lädt das Skript "
            "beim ersten Start ein portables Python (embeddable) von python.org in den Ordner .venv und installiert "
            "dort die benötigten Pakete. Eine Python-Installation im System ist nicht nötig. Weitere Starts "
            "benötigen kein Internet mehr. Für eine komplett Offline-Installation können Sie die Pakete "
            "(reportlab, dearpygui, Pillow, numpy) als .whl-Dateien in den Ordner wheels/ legen - dann wird "
            "ohne Internet installiert.",
            "Linux (z. B. Linux Mint): Im Terminal ./Linux_starter.sh ausführen (einmalig chmod +x Linux_starter.sh). "
            "Das Skript legt .venv an, installiert die Pakete und startet das Programm. Fehlt das Modul venv, "
            "installieren Sie es mit: sudo apt install python3-venv.",
            "Ohne Oberfläche (Kommandozeile) erzeugen Sie ein PDF z. B. mit: python main.py --cli --year 2028 "
            "--paper A3 --country DE --state BY. Alle Optionen zeigt python main.py --help.",
        ],
        "shots": [],
    },
    {
        "title": "3. Reiter Kalender",
        "paras": [
            "Jahr: Die Jahreszahl (1900-2099) bestimmt Wochentage, Kalenderwochen, Schaltjahr und alle Feiertage. "
            "Papierformat und Ausrichtung: A6 bis A1, quer (wie Vorlage) oder hoch. Unter dem Papierformat steht die "
            "Zeilenhöhe in Millimetern; bei A6 ist sie sehr klein - für Notizen empfiehlt sich mindestens A4.",
            "Titel: erscheint oben links (z. B. Firmenname) und ist im PDF später noch änderbar. Logo: Ein PNG oder "
            "JPG wird links oben eingefügt; Seitenverhältnis bleibt erhalten.",
            "Darstellung: Kalenderwochen, Arbeitstage-Fußzeile (Mo-Fr, optional ohne Feiertage), Schalttag, "
            "Hintergrundfarbe der Seite (für sparsamen Druck ausschalten), Legende und die editierbaren Notizfelder. "
            "'Wochenende behält seine Farbe' entspricht der Excel-Vorlage: Fällt ein Feiertag auf einen "
            "Samstag oder Sonntag, bleibt die Wochenendfarbe, der Name wird trotzdem angezeigt.",
            "Mit PDF erstellen wird die Datei im Ausgabeordner gespeichert (Name automatisch, z. B. "
            "Kalender_2028_DE-BY_A3.pdf, oder frei wählbar). PDF öffnen startet den Standard-PDF-Viewer, "
            "Drucken sendet die Datei an den Standarddrucker (Windows: Druckverb, Linux: lp; sonst Viewer mit Strg+P).",
        ],
        "shots": [("gui_01_kalender.png", "Reiter Kalender mit Live-Vorschau rechts.")],
    },
    {
        "title": "4. Reiter Feiertage",
        "paras": [
            "Land: Deutschland (mit Auswahl des Bundeslandes), Österreich, Schweiz, Frankreich, Italien, Spanien, "
            "Niederlande, Belgien, Luxemburg, Vereinigtes Königreich (England/Wales, Schottland), Irland, Polen, "
            "Tschechien, Dänemark, Schweden, Norwegen, Finnland, Portugal, Griechenland, Ungarn, Thailand und USA.",
            "Anzuzeigende Arten: Gesetzliche Feiertage (farbig), Ersatzfeiertage (z. B. USA/UK/Thailand, wenn der "
            "Feiertag auf das Wochenende fällt), Regionale Feiertage (nur in Teilen des Landes, helle Farbe) sowie "
            "Gedenk- und Brauchtumstage (nur Text, z. B. Muttertag, Rosenmontag, Advent, Sommerzeit).",
            "Die Liste zeigt alle Tage des gewählten Jahres. Mit dem Haken können einzelne Feiertage ausgeblendet "
            "werden (wird pro Land/Bundesland gespeichert). Unter 'Eigene Feiertage' lassen sich eigene Termine "
            "ergänzen - mit Jahr 0 gelten sie jedes Jahr (z. B. Betriebsfeier am 1.7.), sonst nur im angegebenen Jahr.",
            "Hinweis Thailand: Die buddhistischen Feiertage (Makha, Visakha, Asahna Bucha, Khao Phansa) richten sich "
            "nach dem Mondkalender. Für 2024-2026 sind die offiziellen Daten hinterlegt, für andere Jahre "
            "wird berechnet (Näherung, bis zu einen Tag Abweichung) und im Programm gewarnt. "
            "Zusätzliche, von der Regierung kurzfristig verfügte Brückentage sind nicht enthalten - "
            "bitte als eigenen Feiertag ergänzen.",
        ],
        "shots": [("gui_02_feiertage.png", "Reiter Feiertage: Land, Bundesland, Arten, Liste und eigene Termine.")],
    },
    {
        "title": "5. Reiter Design",
        "paras": [
            "Farbschema der Oberfläche: Hell, Dunkel und zwölf weitere Schemata (Ozean, Wald, Sonnenuntergang, "
            "Lavendel, Kaffee, Nordlicht, Rosé, Mitternachtsblau, Sand, Mint, Cyberpunk, Graphit-Orange). "
            "Die Umschaltung wirkt sofort und wird gespeichert.",
            "Farbschema des Kalenders: zwölf Paletten, von 'Klassisch (wie Vorlage)' über Pastell und Ozean bis "
            "'Schwarz/Weiß (druckfreundlich)'. Die Vorschau färbt sich sofort um. Die Palette 'Mitternacht' "
            "ist dunkel - für den Druck besser den Hintergrund ausschalten oder ein helles Schema nutzen.",
            "Sprache: Deutsch oder Englisch (Oberfläche, Monats- und Wochentage, Feiertagsnamen).",
        ],
        "shots": [("gui_03_design.png", "Reiter Design."), ("gui_04_dunkel.png", "Dasselbe Programm im dunklen Schema.")],
    },
    {
        "title": "6. Das PDF: Ausfüllen und Drucken",
        "paras": [
            "Jeder Tag besitzt ein Textfeld rechts neben dem Wochentag (bzw. neben dem Feiertagsnamen). Öffnen Sie das "
            "PDF in einem Programm mit Formularunterstützung (Adobe Acrobat Reader, Firefox, Chrome, Edge, "
            "Okular, Evince, LibreOffice Draw) und klicken Sie in das Feld, um zu schreiben. "
            "Speichern Sie das PDF anschließend mit Ihren Einträgen.",
            "Oben links gibt es ein weiteres Feld für Titel/Firmenname. Zum Drucken gilt: Papierformat und "
            "Skalierung 'Tatsächliche Größe' wählen, sonst wird verkleinert. A3 bis A1 lassen sich bei "
            "Copyshops/Plotter drucken; für A4-Drucker empfiehlt sich A4 oder das 'Poster'-Verfahren des "
            "Druckertreibers.",
            "Mit ausgeschalteten Notizfeldern entsteht ein reines Druck-PDF ohne Formularelemente.",
        ],
        "shots": [("example_detail.png", "Ausschnitt: Monatskopf, Kalenderwochen (rechts an Montagen), Feiertage und Notizfelder.")],
    },
    {
        "title": "7. Weitere Beispiele",
        "paras": [
            "Die Beispiele im Ordner beispiele/ zeigen verschiedene Länder, Formate und Farbschemata. "
            "Thailand 2027 im Schema 'Ozean' mit Ersatzfeiertagen:",
        ],
        "shots": [("example_th.png", "Thailand 2027, A3 quer, Schema Ozean (Ersatztage für Feiertage am Wochenende).")],
    },
    {
        "title": "8. Fehlersuche",
        "paras": [
            "Das Programm startet nicht (Windows): Prüfen Sie, ob beim ersten Start Internet verfügbar war "
            "(Download von Python/Paketen), und starten Sie Windows_starter.bat erneut. Meldungen stehen im "
            "Konsolenfenster und in config/error.log.",
            "Die Oberfläche flackert/ist leer (Linux, ältere Grafik): Starten Sie mit der Umgebungsvariable "
            "LIBGL_ALWAYS_SOFTWARE=1 (./Linux_starter.sh).",
            "Felder sind im PDF nicht editierbar: Öffnen Sie das PDF nicht im Browser-Vorschaufenster eines "
            "E-Mail-Programms, sondern in einem echten PDF-Viewer.",
            "Ein Feiertag stimmt nicht: Er lässt sich in der Liste abwählen oder als eigener Feiertag "
            "ergänzen. Hinweise zur Datenbasis stehen im Reiter Feiertage unter dem Land.",
        ],
        "shots": [],
    },
]
