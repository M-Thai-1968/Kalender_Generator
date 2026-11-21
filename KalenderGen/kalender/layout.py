"""Layout des Jahresplaners (12 Monatsspalten x 31 Zeilen) in Millimetern.

Das Layout erzeugt nur einfache Zeichenobjekte (Rechtecke, Texte, Bilder,
Formularfelder). Daraus entstehen identisch die PDF-Datei (reportlab) und
die Vorschau (PIL) - die Vorschau zeigt also exakt das spaetere PDF.
"""
from __future__ import annotations

import calendar
import datetime as dt
from dataclasses import dataclass, field

from reportlab.pdfbase.pdfmetrics import stringWidth

from . import holidays as H

PT_PER_MM = 72.0 / 25.4

PAPER_MM = {"A6": (105, 148), "A5": (148, 210), "A4": (210, 297),
            "A3": (297, 420), "A2": (420, 594), "A1": (594, 841)}

WD = {"de": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
      "en": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]}
MONTHS = {"de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September",
                 "Oktober", "November", "Dezember"],
          "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                 "October", "November", "December"]}

# Kurzformen, falls ein Feiertagsname nicht in die Zelle passt
SHORT_NAMES = {
    "Tag der Deutschen Einheit": "Tag der Einheit",
    "Christi Himmelfahrt": "Himmelfahrt",
    "Internationaler Frauentag": "Frauentag",
    "Mariä Himmelfahrt": "Mariä Himmelf.",
    "Heilige Drei Könige": "Hl. 3 Könige",
    "Ersatztag: ": "Ersatz: ",
    "Observed: ": "Obs.: ",
    "Gedenktag König Bhumibol": "Bhumibol-Gedenktag",
}


# --------------------------------------------------------------------------
# Farbschemata des Kalenders
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Palette:
    name_de: str
    name_en: str
    bg: str        # Seitenhintergrund
    title: str     # Jahreszahl / Titel
    head: str      # Monatskopf
    head_fg: str
    cell: str      # normaler Tag
    sat: str
    sun: str
    hol: str       # Feiertag
    part: str      # regionaler Feiertag
    leap: str      # Schalttag
    invalid: str   # nicht vorhandener Tag
    foot: str      # Fusszeile
    line: str
    text: str
    muted: str     # Brauchtumstage / Wochennummern


PALETTES = [
    Palette("Klassisch (wie Vorlage)", "Classic (like template)", "#C2E4F5", "#11496B", "#BFBFBF", "#000000",
            "#FFFFFF", "#DAF0CF", "#8CD672", "#E8A2DB", "#F1CCEA", "#F5D0EF", "#BFBFBF", "#D9D9D9",
            "#000000", "#000000", "#555555"),
    Palette("Schwarz/Weiß (druckfreundlich)", "Black & white (print friendly)", "#FFFFFF", "#000000", "#CFCFCF",
            "#000000", "#FFFFFF", "#EFEFEF", "#D2D2D2", "#A9A9A9", "#D9D9D9", "#EDEDED", "#B8B8B8", "#E2E2E2",
            "#000000", "#000000", "#555555"),
    Palette("Pastell", "Pastel", "#FFF6EF", "#B5566B", "#F4D6DF", "#5B2A36", "#FFFFFF", "#E6F2E8", "#C9E4D0",
            "#F7C6D0", "#FBE3E8", "#FCEFF2", "#E5DEDB", "#F4E9E2", "#B9A9A4", "#3D2B2F", "#8A7378"),
    Palette("Ozean", "Ocean", "#E3F2FA", "#0B3C5D", "#9CC9E4", "#082A40", "#FFFFFF", "#D7ECF7", "#A6D4EC",
            "#F6B26B", "#FAD7AE", "#FDEBD6", "#C5D5DE", "#BBDCEE", "#5E8CA8", "#0B2A3C", "#4E6F84"),
    Palette("Wald", "Forest", "#EAF1E4", "#24512A", "#A9C79A", "#17361C", "#FFFFFF", "#DCEBD2", "#B3D6A3",
            "#E9B872", "#F3D8AF", "#F7E8CF", "#C9D4C1", "#C4DAB8", "#6F8F66", "#1B2E1D", "#52694F"),
    Palette("Sonnenuntergang", "Sunset", "#FFF1E0", "#B23A1E", "#F6B98F", "#5A1E0F", "#FFFFFF", "#FDE4CF",
            "#F9C49C", "#E86F5B", "#F4A99C", "#FBD3CB", "#E2D2C6", "#F3D2B6", "#C28B6B", "#3E1D12", "#8A5B48"),
    Palette("Lavendel", "Lavender", "#F1ECFA", "#4B3A8C", "#C9BDEA", "#2B2056", "#FFFFFF", "#E8E1F7", "#CFC2EE",
            "#F2A1C8", "#F8CEE2", "#FBE5F0", "#D3CDE0", "#DCD3F2", "#8C7FB8", "#241C45", "#6A6190"),
    Palette("Kaffee", "Coffee", "#F3EAE0", "#4E342E", "#CDB6A0", "#2E1C17", "#FFFCF8", "#EADCCB", "#D3B99D",
            "#C97B63", "#E3B4A5", "#F0D6CC", "#D8CCBF", "#DDCBB8", "#8B6B58", "#2B1D18", "#775F51"),
    Palette("Nordlicht", "Northern lights", "#E7F5F1", "#1B5E5A", "#9ED4CB", "#0E3836", "#FFFFFF", "#D8EFEA",
            "#A9DDD3", "#B39DDB", "#D6CBEE", "#E9E2F6", "#C6D9D5", "#BCE2DB", "#5E9A93", "#102D2B", "#4B7570"),
    Palette("Rosé", "Rose", "#FDEEF2", "#A12850", "#F3B6C8", "#5E1330", "#FFFFFF", "#FBE0E8", "#F5BFD0",
            "#E5719A", "#F1B1C8", "#F9D8E4", "#E6D3DA", "#F6C9D7", "#B77890", "#45121F", "#8C5468"),
    Palette("Sand & Terrakotta", "Sand & terracotta", "#FAF3E3", "#9A4A22", "#E8CFA0", "#4A2A12", "#FFFFFF",
            "#F3E7C9", "#E5CE97", "#D98763", "#EDBBA4", "#F5DCCF", "#DDD2BA", "#EBD9AE", "#A98B5B", "#3B2A16", "#7D6845"),
    Palette("Mitternacht (dunkel)", "Midnight (dark)", "#14213D", "#FCA311", "#2E4272", "#FFFFFF", "#1F3057",
            "#27407A", "#3A5CA6", "#D1495B", "#8C3A53", "#2D3E6B", "#0F1A31", "#2E4272", "#6E83B7", "#F2F4F8",
            "#AEB9D6"),
]


def palette_by_name(name: str) -> Palette:
    for p in PALETTES:
        if name in (p.name_de, p.name_en):
            return p
    return PALETTES[0]


# --------------------------------------------------------------------------
# Zeichenobjekte
# --------------------------------------------------------------------------
@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float
    fill: str | None = None
    stroke: str | None = None
    lw: float = 0.2


@dataclass
class Text:
    x: float
    y: float            # Grundlinie
    s: str
    pt: float
    bold: bool = False
    color: str = "#000000"
    align: str = "l"    # l / c / r


@dataclass
class Image:
    path: str
    x: float
    y: float
    w: float
    h: float


@dataclass
class Field:
    name: str
    x: float
    y: float
    w: float
    h: float
    pt: float
    value: str = ""
    color: str = "#000000"
    tooltip: str = ""
    bold: bool = False


@dataclass
class Page:
    width: float
    height: float
    items: list = field(default_factory=list)
    title: str = ""
    cell_h: float = 0.0
    year: int = 0
    workdays: list = field(default_factory=list)


@dataclass
class Options:
    year: int = 2027
    paper: str = "A3"
    landscape: bool = True
    country: str = "DE"
    state: str = ""
    lang: str = "de"
    title: str = ""
    logo: str = ""
    palette: str = "Klassisch (wie Vorlage)"
    show_cats: tuple = (H.PUBLIC, H.SUB)
    excluded: tuple = ()
    custom: tuple = ()
    week_numbers: bool = True
    workday_row: bool = True
    workdays_deduct: bool = False
    highlight_leap: bool = True
    weekend_wins: bool = True      # Wochenendfarbe hat Vorrang vor Feiertagsfarbe (wie Vorlage)
    show_bg: bool = True
    fields: bool = True
    legend: bool = True


# --------------------------------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------------------------------
def tw(s: str, pt: float, bold: bool = False) -> float:
    """Textbreite in mm (Helvetica)."""
    return stringWidth(s, "Helvetica-Bold" if bold else "Helvetica", pt) / PT_PER_MM


def page_size(paper: str, landscape: bool) -> tuple[float, float]:
    w, h = PAPER_MM[paper]
    return (h, w) if landscape else (w, h)


def _shorten(name: str) -> list[str]:
    cands = [name]
    s = name
    for k, v in SHORT_NAMES.items():
        s = s.replace(k, v)
    if s != name:
        cands.append(s)
    return cands


def _single(cands, max_w, pt_max, pt_min):
    for cand in cands:
        pt = pt_max
        while pt >= pt_min - 1e-6:
            if tw(cand, pt) <= max_w:
                return [cand], pt
            pt -= max(pt * 0.05, 0.1)
    return None


def _double(cands, max_w, max_h, pt_max, pt_min):
    best = None
    for cand in cands:
        words = cand.split()
        splits = [(" ".join(words[:i]), " ".join(words[i:])) for i in range(1, len(words))]
        for j, w in enumerate(words):                      # Silbentrennung als Rueckfall
            if len(w) >= 7:
                for k in range(3, len(w) - 2):
                    splits.append((" ".join(words[:j] + [w[:k] + "-"]), " ".join([w[k:]] + words[j + 1:])))
        for a, b in splits:
            pt = min(pt_max, max_h / 2.1 * PT_PER_MM)
            while pt >= pt_min * 0.8:
                if max(tw(a, pt), tw(b, pt)) <= max_w:
                    if best is None or pt > best[1]:
                        best = ([a, b], pt)
                    break
                pt -= max(pt * 0.05, 0.1)
    return best


def fit_name(name: str, max_w: float, max_h: float, pt_max: float, pt_min: float):
    """Passt einen Namen in die Flaeche: ein- oder zweizeilig, ggf. gekuerzt.

    Rueckgabe: (zeilen, pt) oder None, wenn gar nichts passt.
    """
    cands = _shorten(name)
    one = _single(cands, max_w, pt_max, pt_min)
    if one and one[1] >= pt_max * 0.8:
        return one
    two = _double(cands, max_w, max_h, pt_max, pt_min)
    if one and two:
        return two if two[1] > one[1] * 1.2 else one
    if one or two:
        return one or two
    cand = cands[-1]                         # abschneiden
    while cand and tw(cand + ".", pt_min) > max_w:
        cand = cand[:-1]
    if len(cand) >= 3:
        return [cand.rstrip() + "."], pt_min
    return None


# --------------------------------------------------------------------------
# Hauptfunktion
# --------------------------------------------------------------------------
def build_page(o: Options, day_map: dict[dt.date, list[H.Holiday]] | None = None, region_text: str = "") -> Page:
    lang = o.lang if o.lang in WD else "de"
    pal = palette_by_name(o.palette)
    W, Hh = page_size(o.paper, o.landscape)
    if day_map is None:
        day_map = H.build_day_map(o.country, o.state, o.year, o.show_cats, o.excluded, o.custom, lang)
    page = Page(W, Hh, year=o.year)
    it = page.items
    s = min(W, Hh) / 210.0                     # Skalierung gegenueber A4-Kurzseite
    m = 6.0 * s
    page.title = o.title

    # Hintergrund
    it.append(Rect(0, 0, W, Hh, fill=pal.bg if o.show_bg else "#FFFFFF"))

    # Kopfbereich
    head_h = 0.085 * Hh if o.landscape else 0.06 * Hh
    gx, gy0 = m, m
    gw = W - 2 * m
    caption_h = 4.2 * s if o.legend else 0
    gy = gy0 + head_h + 1.5 * s
    rows = 1.25 + 31 + (1.05 if o.workday_row else 0)
    gh = Hh - gy - m - caption_h
    rh = gh / rows
    cw = gw / 12
    page.cell_h = rh

    # Jahreszahl rechts
    ypt = head_h * 0.78 * PT_PER_MM
    it.append(Text(W - m, gy0 + head_h * 0.80, str(o.year), ypt, True, pal.title, "r"))
    year_w = tw(str(o.year), ypt, True)

    # Logo links
    left = gx
    if o.logo:
        try:
            from PIL import Image as PILImage
            with PILImage.open(o.logo) as im:
                iw, ih = im.size
            bh = head_h * 0.95
            bw = min(bh * iw / ih, gw * 0.25)
            bh = bw * ih / iw
            it.append(Image(o.logo, gx, gy0 + (head_h - bh) / 2, bw, bh))
            left = gx + bw + 4 * s
        except Exception:
            pass

    # Titel (im PDF editierbar)
    title_pt = head_h * 0.34 * PT_PER_MM
    tx_w = max(W - m - year_w - 6 * s - left, 10 * s)
    if o.title or o.fields:
        while tw(o.title or "", title_pt, True) > tx_w and title_pt > 4:
            title_pt -= 0.5
        if o.fields:
            it.append(Field("titel", left, gy0 + head_h * 0.18, tx_w, head_h * 0.62, title_pt, o.title, pal.title,
                            "Titel / Firmenname (im PDF editierbar)", False))
        if o.title and not o.fields:
            it.append(Text(left, gy0 + head_h * 0.62, o.title, title_pt, True, pal.title, "l"))

    # Gitter-Geometrie
    head_row = 1.25 * rh
    foot_row = 1.05 * rh if o.workday_row else 0
    u = min(rh, 0.40 * cw)                    # Bezugsgroesse fuer Schrift (Zeile ODER Spalte begrenzt)
    day_pt = u * 0.60 * PT_PER_MM
    num_w = max(0.145 * cw, tw("00", day_pt) + 0.09 * cw)
    wd_w = 0.205 * cw
    wk_w = 0.16 * cw if o.week_numbers else 0
    pad = 0.04 * cw
    wd_pt = u * 0.56 * PT_PER_MM
    wk_pt = u * 0.34 * PT_PER_MM
    base = lambda cy, pt: cy + pt / PT_PER_MM * 0.35      # Grundlinie aus Mittelpunkt

    leap_day = dt.date(o.year, 2, 29) if calendar.isleap(o.year) else None
    tall = rh >= 1.08 * u                     # Hochformat: Name in eigener unterer Zeile
    hp = min(head_row * 0.52, u * 0.72) * PT_PER_MM
    hnw = min(num_w, tw("00", hp, True) + 0.10 * cw) if tall else num_w    # Breite der Monatsnummer
    mp = hp                                   # einheitliche Schrift fuer alle Monatsnamen
    for mname in MONTHS[lang]:
        while tw(mname, mp, True) > (cw - hnw) * 0.92 and mp > 3:
            mp -= 0.3

    for mi in range(12):
        x = gx + mi * cw
        month = mi + 1
        # Monatskopf
        it.append(Rect(x, gy, cw, head_row, pal.head, pal.line, 0.2 * s + 0.1))
        it.append(Rect(x, gy, hnw, head_row, None, pal.line, 0.2 * s + 0.1))
        it.append(Text(x + hnw / 2, base(gy + head_row / 2, hp), str(month), hp, True, pal.head_fg, "c"))
        mname = MONTHS[lang][mi]
        it.append(Text(x + hnw + (cw - hnw) / 2, base(gy + head_row / 2, mp), mname, mp, True, pal.head_fg, "c"))

        ndays = calendar.monthrange(o.year, month)[1]
        workdays = 0
        for d in range(1, 32):
            y = gy + head_row + (d - 1) * rh
            if d > ndays:
                it.append(Rect(x, y, cw, rh, pal.invalid, pal.line, 0.15 * s + 0.08))
                continue
            date = dt.date(o.year, month, d)
            wdi = date.weekday()
            hols = day_map.get(date, [])
            top = hols[0] if hols else None
            is_hol = top is not None and top.cat in (H.PUBLIC, H.SUB)
            is_part = top is not None and top.cat == H.PARTIAL
            if wdi < 5:
                if not (is_hol and o.workdays_deduct):
                    workdays += 1
            # Fuellfarbe
            fill = pal.cell
            if is_hol and not (o.weekend_wins and wdi >= 5):
                fill = pal.hol
            elif is_part and wdi < 5:
                fill = pal.part
            elif wdi == 6:
                fill = pal.sun
            elif wdi == 5:
                fill = pal.sat
            elif leap_day is not None and date == leap_day and o.highlight_leap:
                fill = pal.leap
            it.append(Rect(x, y, cw, rh, fill, pal.line, 0.15 * s + 0.08))
            cy = y + rh * 0.30 if tall else y + rh / 2
            it.append(Text(x + num_w - pad * 0.6, base(cy, day_pt), str(d), day_pt, False, pal.text, "r"))
            it.append(Text(x + num_w + pad * 0.7, base(cy, wd_pt), WD[lang][wdi], wd_pt, False, pal.text, "l"))
            # Kalenderwoche an Montagen
            right = x + cw - pad
            has_wk = o.week_numbers and wdi == 0
            if has_wk:
                wk = date.isocalendar()[1]
                it.append(Text(right, base(cy + u * 0.12, wk_pt), str(wk), wk_pt, False, pal.text, "r"))
            if tall:       # Name/Notiz in der unteren Zellhaelfte ueber die volle Breite
                nx0, nx1 = x + pad, x + cw - pad
                ncy, nh = y + rh * 0.76, rh * 0.44
            else:
                nx0, nx1 = x + num_w + wd_w + pad * 0.4, x + cw - pad - (wk_w if has_wk else 0)
                ncy, nh = cy, rh * 0.92
            name_right = nx0
            if hols:
                label = top.name(lang)
                if len(hols) > 1 and hols[1].cat == top.cat and hols[1].name(lang) != label:
                    label += " / " + hols[1].name(lang)
                is_strong = top.cat != H.OBS
                pt_max = u * (0.42 if is_strong else 0.38) * PT_PER_MM
                pt_min = u * 0.24 * PT_PER_MM
                res = fit_name(label, nx1 - nx0, nh, pt_max, pt_min)
                if res:
                    lines, pt = res
                    col = pal.text if is_strong else pal.muted
                    if len(lines) == 1:
                        it.append(Text(nx0, base(ncy, pt), lines[0], pt, False, col, "l"))
                        name_right = nx0 + tw(lines[0], pt) + pad
                    else:
                        lh = pt / PT_PER_MM * 1.02
                        it.append(Text(nx0, ncy - lh * 0.12, lines[0], pt, False, col, "l"))
                        it.append(Text(nx0, ncy + lh * 0.88, lines[1], pt, False, col, "l"))
                        name_right = nx0 + max(tw(lines[0], pt), tw(lines[1], pt)) + pad
            if o.fields:
                fx = max(name_right, nx0)
                fw = nx1 - fx
                if fw >= 0.2 * cw:
                    fpt = min(u * 0.5 * PT_PER_MM, 14)
                    if tall:
                        fy, fh = y + rh * 0.54, rh * 0.42
                    else:
                        fy, fh = y + rh * 0.06, rh * 0.88
                    it.append(Field(f"n_{month:02d}_{d:02d}", fx, fy, fw, fh, fpt, "", pal.text,
                                    f"{d}.{month}.{o.year}"))
        page.workdays.append(workdays)
        # Fusszeile
        if o.workday_row:
            fy = gy + head_row + 31 * rh
            it.append(Rect(x, fy, cw, foot_row, pal.foot, pal.line, 0.2 * s + 0.1))
            fp = foot_row * 0.55 * PT_PER_MM
            it.append(Text(x + cw / 2, base(fy + foot_row / 2, fp), str(workdays), fp, False, pal.text, "c"))

    # Aussenrahmen
    it.append(Rect(gx, gy, gw, head_row + 31 * rh + foot_row, None, pal.line, 0.45 * s + 0.2))

    # Legende / Hinweiszeile
    if o.legend:
        cap_pt = max(caption_h * 0.55 * PT_PER_MM, 3.0)
        cy = Hh - m - caption_h * 0.35
        sq = caption_h * 0.55
        xx = gx
        entries = [(pal.sat, "Samstag" if lang == "de" else "Saturday"),
                   (pal.sun, "Sonntag" if lang == "de" else "Sunday"),
                   (pal.hol, "Feiertag" if lang == "de" else "Public holiday")]
        if H.PARTIAL in o.show_cats:
            entries.append((pal.part, "regional" if lang == "de" else "regional"))
        if leap_day is not None and o.highlight_leap:
            entries.append((pal.leap, "Schalttag" if lang == "de" else "Leap day"))
        for col, lab in entries:
            it.append(Rect(xx, cy - sq * 0.8, sq, sq, col, pal.line, 0.12 * s + 0.05))
            it.append(Text(xx + sq + 1.2 * s, cy, lab, cap_pt, False, pal.text, "l"))
            xx += sq + 1.2 * s + tw(lab, cap_pt) + 4 * s
        info = []
        if o.week_numbers:
            info.append("Zahl rechts = Kalenderwoche (ISO)" if lang == "de" else "Number on right = ISO week")
        if o.workday_row:
            info.append("Fusszeile = Mo-Fr-Tage" + (" ohne Feiertage" if o.workdays_deduct else "")
                        if lang == "de" else "Footer = Mon-Fri days" + (" excl. holidays" if o.workdays_deduct else ""))
        if region_text:
            info.append(("Feiertage: " if lang == "de" else "Holidays: ") + region_text)
        txt = "  |  ".join(info)
        while tw(txt, cap_pt) > gx + gw - xx and cap_pt > 2.2:
            cap_pt -= 0.2
        it.append(Text(gx + gw, cy, txt, cap_pt, False, pal.muted, "r"))
    return page
