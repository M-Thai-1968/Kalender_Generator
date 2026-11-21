"""Feiertags-Berechnung (komplett offline).

Alle Feiertage werden aus Regeln berechnet (feste Daten, Ostern-abhaengig,
n-ter Wochentag, ...). Es wird keine Internetverbindung benoetigt.

Kategorien:
  public   gesetzlicher Feiertag
  sub      Ersatzfeiertag (Feiertag faellt aufs Wochenende)
  partial  nur regional / in Teilen des Landes
  obs      Gedenk- und Brauchtumstag (kein freier Tag)
"""
from __future__ import annotations

import calendar
import datetime as dt
import math
from dataclasses import dataclass, field

PUBLIC, SUB, PARTIAL, OBS = "public", "sub", "partial", "obs"
PRIORITY = {PUBLIC: 0, SUB: 1, PARTIAL: 2, OBS: 3}


# --------------------------------------------------------------------------
# Datenmodell
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Rule:
    kind: str
    args: tuple
    de: str
    en: str
    cat: str = PUBLIC
    y0: int = 0
    y1: int = 9999
    regions: frozenset | None = None      # nur Deutschland: Bundeslaender mit Feiertag
    partial: frozenset = frozenset()      # Bundeslaender, in denen nur teilweise
    obs_elsewhere: bool = True            # sonst als Brauchtumstag anzeigen


@dataclass(frozen=True)
class Holiday:
    date: dt.date
    de: str
    en: str
    cat: str
    approx: bool = False
    custom: bool = False

    def name(self, lang: str = "de") -> str:
        return self.en if lang == "en" else self.de


def _R(kind, args, de, en, **k):
    return Rule(kind, tuple(args), de, en, **k)


def F(m, d, de, en, **k):
    return _R("F", (m, d), de, en, **k)


def E(o, de, en, **k):
    return _R("E", (o,), de, en, **k)


def O(o, de, en, **k):
    return _R("O", (o,), de, en, **k)


def N(m, wd, n, de, en, **k):
    return _R("N", (m, wd, n), de, en, **k)


def L(m, wd, de, en, **k):
    return _R("L", (m, wd), de, en, **k)


def W(m, d, wd, de, en, **k):
    """Erster Wochentag am oder nach dem Datum."""
    return _R("W", (m, d, wd), de, en, **k)


def B(m, d, wd, de, en, weeks=0, **k):
    """Letzter Wochentag strikt vor dem Datum (minus weitere Wochen)."""
    return _R("B", (m, d, wd, weeks), de, en, **k)


def X(kind, de, en, *args, **k):
    return _R(kind, args, de, en, **k)


# --------------------------------------------------------------------------
# Kalender-Mathematik
# --------------------------------------------------------------------------
def easter(y: int) -> dt.date:
    """Westliches Ostersonntag-Datum (gregorianisch)."""
    a = y % 19
    b, c = divmod(y, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return dt.date(y, month, day)


def orthodox_easter(y: int) -> dt.date:
    """Orthodoxer Ostersonntag, umgerechnet ins gregorianische Datum (1900-2099)."""
    a, b, c = y % 4, y % 7, y % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    month = (d + e + 114) // 31
    day = (d + e + 114) % 31 + 1
    return dt.date(y, month, day) + dt.timedelta(days=13)


def _full_moons_utc(year: int) -> list[dt.datetime]:
    """Vollmondzeitpunkte (UTC) nach Meeus, Kap. 49 (Genauigkeit ca. 10 Minuten)."""
    out = []
    k0 = round((year - 2000) * 12.3685) - 2
    rad = math.radians
    for n in range(0, 18):
        k = k0 + n + 0.5
        T = k / 1236.85
        jde = (2451550.09766 + 29.530588861 * k + 0.00015437 * T * T
               - 0.000000150 * T ** 3 + 0.00000000073 * T ** 4)
        E_ = 1 - 0.002516 * T - 0.0000074 * T * T
        M = rad((2.5534 + 29.10535670 * k - 0.0000014 * T * T) % 360)
        Mp = rad((201.5643 + 385.81693528 * k + 0.0107582 * T * T) % 360)
        Fm = rad((160.7108 + 390.67050284 * k - 0.0016118 * T * T) % 360)
        corr = (-0.40614 * math.sin(Mp) + 0.17302 * E_ * math.sin(M)
                + 0.01614 * math.sin(2 * Mp) + 0.01043 * math.sin(2 * Fm)
                + 0.00734 * E_ * math.sin(Mp - M) - 0.00515 * E_ * math.sin(Mp + M)
                + 0.00209 * E_ * E_ * math.sin(2 * M) - 0.00111 * math.sin(Mp - 2 * Fm)
                - 0.00057 * math.sin(Mp + 2 * Fm) + 0.00056 * E_ * math.sin(2 * Mp + M)
                - 0.00042 * math.sin(3 * Mp) + 0.00042 * E_ * math.sin(M + 2 * Fm))
        jd = jde + corr - 69.0 / 86400.0
        out.append(dt.datetime(1970, 1, 1) + dt.timedelta(days=jd - 2440587.5))
    return out


# Buddhistische Feiertage (Thailand) richten sich nach dem Mondkalender.
# Fuer diese Jahre sind die offiziellen Daten hinterlegt; sonst Naeherung (+-1 Tag).
TH_LUNAR_TABLE = {
    2024: {"makha": (2, 24), "visakha": (5, 22), "asahna": (7, 20)},
    2025: {"makha": (2, 12), "visakha": (5, 11), "asahna": (7, 10)},
    2026: {"makha": (3, 3), "visakha": (5, 31), "asahna": (7, 29)},
}


def thai_lunar(year: int, which: str) -> tuple[dt.date, bool]:
    """Liefert (Datum, ist_naeherung) fuer makha/visakha/asahna/khao."""
    if which == "khao":
        d, approx = thai_lunar(year, "asahna")
        return d + dt.timedelta(days=1), approx
    if year in TH_LUNAR_TABLE:
        m, d = TH_LUNAR_TABLE[year][which]
        return dt.date(year, m, d), False
    moons = [(x + dt.timedelta(hours=7)).date() for x in _full_moons_utc(year)]
    moons = [d for d in moons if d.year == year]

    def first_in(m0, d0, m1, d1):
        for i, d in enumerate(moons):
            if dt.date(year, m0, d0) <= d <= dt.date(year, m1, d1):
                return i
        return 0

    if which == "makha":
        return moons[first_in(2, 8, 3, 9)], True
    vi = first_in(5, 3, 6, 2)
    if which == "visakha":
        return moons[vi], True
    return moons[min(vi + 2, len(moons) - 1)], True


def _eval(rule: Rule, y: int) -> tuple[dt.date | None, bool]:
    k, a = rule.kind, rule.args
    td = dt.timedelta
    try:
        if k == "F":
            return dt.date(y, a[0], a[1]), False
        if k == "F5":
            return (dt.date(y, a[0], a[1]) if y % 5 == 0 else None), False
        if k == "E":
            return easter(y) + td(days=a[0]), False
        if k == "O":
            return orthodox_easter(y) + td(days=a[0]), False
        if k == "N":
            m, wd, n = a
            first = dt.date(y, m, 1)
            return dt.date(y, m, 1 + (wd - first.weekday()) % 7 + 7 * (n - 1)), False
        if k == "L":
            m, wd = a
            last = dt.date(y, m, calendar.monthrange(y, m)[1])
            return last - td(days=(last.weekday() - wd) % 7), False
        if k == "W":
            m, d, wd = a
            base = dt.date(y, m, d)
            return base + td(days=(wd - base.weekday()) % 7), False
        if k == "B":
            m, d, wd, wk = a
            base = dt.date(y, m, d)
            delta = (base.weekday() - wd) % 7 or 7
            return base - td(days=delta + 7 * wk), False
        if k == "KD":      # Koningsdag (NL)
            d = dt.date(y, 4, 27)
            return (d - td(days=1) if d.weekday() == 6 else d), False
        if k == "BR":      # St. Brigid's Day (IE)
            feb1 = dt.date(y, 2, 1)
            return (feb1 if feb1.weekday() == 4 else feb1 + td(days=(0 - feb1.weekday()) % 7)), False
        if k == "EL":      # US Election Day (gerade Jahre)
            if y % 2:
                return None, False
            first = dt.date(y, 11, 1)
            return first + td(days=(0 - first.weekday()) % 7 + 1), False
        if k == "TH":
            return thai_lunar(y, a[0])
    except ValueError:
        return None, False
    raise ValueError(f"Unbekannte Regelart {k}")


# --------------------------------------------------------------------------
# Regeldaten
# --------------------------------------------------------------------------
def _fs(*codes):
    return frozenset(codes)


DE_STATES = {
    "BW": ("Baden-Württemberg", "Baden-Wuerttemberg"),
    "BY": ("Bayern", "Bavaria"),
    "BE": ("Berlin", "Berlin"),
    "BB": ("Brandenburg", "Brandenburg"),
    "HB": ("Bremen", "Bremen"),
    "HH": ("Hamburg", "Hamburg"),
    "HE": ("Hessen", "Hesse"),
    "MV": ("Mecklenburg-Vorpommern", "Mecklenburg-Western Pomerania"),
    "NI": ("Niedersachsen", "Lower Saxony"),
    "NW": ("Nordrhein-Westfalen", "North Rhine-Westphalia"),
    "RP": ("Rheinland-Pfalz", "Rhineland-Palatinate"),
    "SL": ("Saarland", "Saarland"),
    "SN": ("Sachsen", "Saxony"),
    "ST": ("Sachsen-Anhalt", "Saxony-Anhalt"),
    "SH": ("Schleswig-Holstein", "Schleswig-Holstein"),
    "TH": ("Thüringen", "Thuringia"),
}
_ALL_DE = frozenset(DE_STATES)

NEUJAHR = ("Neujahr", "New Year's Day")
WEIH1 = ("1. Weihnachtstag", "Christmas Day")
WEIH2 = ("2. Weihnachtstag", "Boxing Day")

DE_COMMON = [
    F(1, 1, *NEUJAHR),
    E(-2, "Karfreitag", "Good Friday"),
    E(1, "Ostermontag", "Easter Monday"),
    F(5, 1, "Tag der Arbeit", "Labour Day"),
    E(39, "Christi Himmelfahrt", "Ascension Day"),
    E(50, "Pfingstmontag", "Whit Monday"),
    F(10, 3, "Tag der Deutschen Einheit", "German Unity Day"),
    F(12, 25, *WEIH1),
    F(12, 26, *WEIH2),
]

DE_REGIONAL = [
    F(1, 6, "Heilige Drei Könige", "Epiphany", regions=_fs("BW", "BY", "ST")),
    F(3, 8, "Internationaler Frauentag", "International Women's Day", regions=_fs("BE"), y0=2019),
    F(3, 8, "Internationaler Frauentag", "International Women's Day", regions=_fs("MV"), y0=2023),
    E(0, "Ostersonntag", "Easter Sunday", regions=_fs("BB")),
    F(5, 8, "Tag der Befreiung", "Liberation Day", regions=_fs("BE"), y0=2020, y1=2020, obs_elsewhere=False),
    F(5, 8, "Tag der Befreiung", "Liberation Day", regions=_fs("BE"), y0=2025, y1=2025, obs_elsewhere=False),
    E(49, "Pfingstsonntag", "Whit Sunday", regions=_fs("BB")),
    E(60, "Fronleichnam", "Corpus Christi", regions=_fs("BW", "BY", "HE", "NW", "RP", "SL"),
      partial=_fs("SN", "TH")),
    F(8, 15, "Mariä Himmelfahrt", "Assumption Day", regions=_fs("SL"), partial=_fs("BY")),
    F(9, 20, "Weltkindertag", "World Children's Day", regions=_fs("TH"), y0=2019),
    F(10, 31, "Reformationstag", "Reformation Day", regions=_fs("BB", "MV", "SN", "ST", "TH")),
    F(10, 31, "Reformationstag", "Reformation Day", regions=_fs("HB", "HH", "NI", "SH"), y0=2018),
    F(10, 31, "Reformationstag", "Reformation Day", regions=_ALL_DE, y0=2017, y1=2017),
    F(11, 1, "Allerheiligen", "All Saints' Day", regions=_fs("BW", "BY", "NW", "RP", "SL")),
    B(11, 23, 2, "Buß- und Bettag", "Repentance and Prayer Day", regions=_fs("SN")),
]

DE_EXTRAS = [   # Gedenk- und Brauchtumstage
    E(-52, "Weiberfastnacht", "Fat Thursday", cat=OBS),
    E(-48, "Rosenmontag", "Rose Monday", cat=OBS),
    E(-47, "Faschingsdienstag", "Shrove Tuesday", cat=OBS),
    E(-46, "Aschermittwoch", "Ash Wednesday", cat=OBS),
    N(5, 6, 2, "Muttertag", "Mother's Day", cat=OBS),
    F(11, 11, "Martinstag", "St. Martin's Day", cat=OBS),
    B(12, 25, 6, "Volkstrauertag", "National Day of Mourning", weeks=5, cat=OBS),
    B(12, 25, 6, "Totensonntag", "Sunday of the Dead", weeks=4, cat=OBS),
    B(12, 25, 6, "1. Advent", "1st Advent", weeks=3, cat=OBS),
    B(12, 25, 6, "2. Advent", "2nd Advent", weeks=2, cat=OBS),
    B(12, 25, 6, "3. Advent", "3rd Advent", weeks=1, cat=OBS),
    B(12, 25, 6, "4. Advent", "4th Advent", cat=OBS),
    F(12, 6, "Nikolaus", "St. Nicholas Day", cat=OBS),
]


def pack(easter_days: bool = True, extra=()):
    r = [
        F(2, 14, "Valentinstag", "Valentine's Day", cat=OBS),
        F(12, 24, "Heiligabend", "Christmas Eve", cat=OBS),
        F(12, 31, "Silvester", "New Year's Eve", cat=OBS),
        L(3, 6, "Beginn der Sommerzeit", "Daylight saving time starts", cat=OBS),
        L(10, 6, "Ende der Sommerzeit", "Daylight saving time ends", cat=OBS),
    ]
    if easter_days:
        r += [
            E(-7, "Palmsonntag", "Palm Sunday", cat=OBS),
            E(-3, "Gründonnerstag", "Maundy Thursday", cat=OBS),
            E(-2, "Karfreitag", "Good Friday", cat=OBS),
            E(-1, "Karsamstag", "Holy Saturday", cat=OBS),
            E(0, "Ostersonntag", "Easter Sunday", cat=OBS),
            E(49, "Pfingstsonntag", "Whit Sunday", cat=OBS),
        ]
    return r + list(extra)


XMAS1 = F(12, 25, "1. Weihnachtstag", "Christmas Day")
XMAS2 = F(12, 26, "2. Weihnachtstag", "Boxing Day")
ASC = E(39, "Christi Himmelfahrt", "Ascension Day")
WHITM = E(50, "Pfingstmontag", "Whit Monday")
EASTM = E(1, "Ostermontag", "Easter Monday")
GOODF = E(-2, "Karfreitag", "Good Friday")
EASTS = E(0, "Ostersonntag", "Easter Sunday")
WHITS = E(49, "Pfingstsonntag", "Whit Sunday")
MAY1 = F(5, 1, "Tag der Arbeit", "Labour Day")
ALLSAINTS = F(11, 1, "Allerheiligen", "All Saints' Day")
ASSUMP = F(8, 15, "Mariä Himmelfahrt", "Assumption Day")
IMMAC = F(12, 8, "Mariä Empfängnis", "Immaculate Conception")
EPIPH = F(1, 6, "Heilige Drei Könige", "Epiphany")
CORPUS = E(60, "Fronleichnam", "Corpus Christi")


@dataclass
class Region:
    code: str
    de: str
    en: str
    rules: list
    sub: str = ""      # Ersatztage: "", "uk", "us", "th"
    note_de: str = ""
    note_en: str = ""


COUNTRIES: dict[str, Region] = {}


def _reg(code, de, en, rules, sub="", note_de="", note_en=""):
    COUNTRIES[code] = Region(code, de, en, rules, sub, note_de, note_en)


_reg("DE", "Deutschland", "Germany", DE_COMMON + DE_REGIONAL + pack(extra=DE_EXTRAS),
     note_de="Bundesland waehlbar. Ohne Bundesland werden nur die bundesweiten Feiertage als gesetzlich markiert.",
     note_en="Federal state selectable. Without a state only nationwide holidays count as public.")

_reg("AT", "Österreich", "Austria", [
    F(1, 1, *NEUJAHR), EPIPH, EASTM, F(5, 1, "Staatsfeiertag", "National Holiday"), ASC, WHITM, CORPUS,
    ASSUMP, F(10, 26, "Nationalfeiertag", "Austrian National Day"), ALLSAINTS, IMMAC,
    F(12, 25, "Christtag", "Christmas Day"), F(12, 26, "Stefanitag", "St. Stephen's Day"),
] + pack(extra=DE_EXTRAS))

_reg("CH", "Schweiz", "Switzerland", [
    F(1, 1, *NEUJAHR), GOODF, EASTM, ASC, WHITM, F(8, 1, "Bundesfeier", "Swiss National Day"), XMAS1,
    F(12, 26, "Stephanstag", "St. Stephen's Day"),
    F(1, 2, "Berchtoldstag", "Berchtold's Day", cat=PARTIAL),
    F(1, 6, "Heilige Drei Könige", "Epiphany", cat=PARTIAL),
    F(3, 19, "Josefstag", "St. Joseph's Day", cat=PARTIAL),
    E(60, "Fronleichnam", "Corpus Christi", cat=PARTIAL),
    F(8, 15, "Mariä Himmelfahrt", "Assumption Day", cat=PARTIAL),
    F(11, 1, "Allerheiligen", "All Saints' Day", cat=PARTIAL),
    F(12, 8, "Mariä Empfängnis", "Immaculate Conception", cat=PARTIAL),
] + pack(extra=DE_EXTRAS),
     note_de="Kantonale Feiertage sind unterschiedlich: Karfreitag, Ostermontag, Pfingstmontag und Stephanstag gelten in den meisten Kantonen; weitere als 'regional' markiert.",
     note_en="Cantonal holidays differ; regional ones are marked 'regional'.")

_reg("FR", "Frankreich", "France", [
    F(1, 1, *NEUJAHR), EASTM, MAY1, F(5, 8, "Tag des Sieges 1945", "Victory in Europe Day"), ASC, WHITM,
    F(7, 14, "Nationalfeiertag", "Bastille Day"), ASSUMP, ALLSAINTS,
    F(11, 11, "Waffenstillstand 1918", "Armistice Day"), F(12, 25, "Weihnachten", "Christmas Day"),
    E(-2, "Karfreitag (Elsass-Moselle)", "Good Friday (Alsace-Moselle)", cat=PARTIAL),
    F(12, 26, "2. Weihnachtstag (Elsass-Moselle)", "St. Stephen's Day (Alsace-Moselle)", cat=PARTIAL),
] + pack())

_reg("IT", "Italien", "Italy", [
    F(1, 1, *NEUJAHR), EPIPH, E(0, "Ostersonntag (Pasqua)", "Easter Sunday"),
    E(1, "Ostermontag (Pasquetta)", "Easter Monday"),
    F(4, 25, "Tag der Befreiung", "Liberation Day"), MAY1, F(6, 2, "Tag der Republik", "Republic Day"),
    F(8, 15, "Mariä Himmelfahrt (Ferragosto)", "Assumption Day"), ALLSAINTS, IMMAC,
    F(12, 25, "Weihnachten", "Christmas Day"), F(12, 26, "Stephanstag", "St. Stephen's Day"),
] + pack())

_reg("ES", "Spanien", "Spain", [
    F(1, 1, *NEUJAHR), EPIPH, GOODF, MAY1, ASSUMP,
    F(10, 12, "Nationalfeiertag (Hispanidad)", "National Day of Spain"), ALLSAINTS,
    F(12, 6, "Verfassungstag", "Constitution Day"), IMMAC, F(12, 25, "Weihnachten", "Christmas Day"),
    E(-3, "Gründonnerstag", "Maundy Thursday", cat=PARTIAL),
    E(1, "Ostermontag", "Easter Monday", cat=PARTIAL),
    F(7, 25, "Jakobstag", "St. James' Day", cat=PARTIAL),
] + pack(), note_de="Weitere Feiertage unterscheiden sich je Autonomer Gemeinschaft (als 'regional' markiert).",
     note_en="Further holidays differ per autonomous community.")

_reg("NL", "Niederlande", "Netherlands", [
    F(1, 1, *NEUJAHR), EASTS, EASTM, X("KD", "Königstag (Koningsdag)", "King's Day", y0=2014),
    ASC, WHITS, WHITM, XMAS1, XMAS2,
    X("F5", "Befreiungstag", "Liberation Day", 5, 5),
    F(5, 4, "Totengedenken", "Remembrance of the Dead", cat=OBS),
    F(5, 5, "Befreiungstag", "Liberation Day", cat=OBS),
    F(12, 5, "Sinterklaas", "Sinterklaas", cat=OBS),
    N(9, 1, 3, "Prinsjesdag", "Prinsjesdag", cat=OBS),
] + pack())

_reg("BE", "Belgien", "Belgium", [
    F(1, 1, *NEUJAHR), EASTS, EASTM, MAY1, ASC, WHITS, WHITM,
    F(7, 21, "Nationalfeiertag", "Belgian National Day"), ASSUMP, ALLSAINTS,
    F(11, 11, "Waffenstillstand", "Armistice Day"), F(12, 25, "Weihnachten", "Christmas Day"),
] + pack())

_reg("LU", "Luxemburg", "Luxembourg", [
    F(1, 1, *NEUJAHR), EASTM, MAY1, F(5, 9, "Europatag", "Europe Day", y0=2019), ASC, WHITM,
    F(6, 23, "Nationalfeiertag", "National Day"), ASSUMP, ALLSAINTS, F(12, 25, "Weihnachten", "Christmas Day"),
    F(12, 26, "Stephanstag", "St. Stephen's Day"),
] + pack())

_UK_OBS = [
    E(-21, "Muttertag (Mothering Sunday)", "Mothering Sunday", cat=OBS),
    F(4, 23, "St. George's Day", "St George's Day", cat=OBS),
    F(10, 31, "Halloween", "Halloween", cat=OBS),
    F(11, 5, "Bonfire Night", "Bonfire Night", cat=OBS),
    N(11, 6, 2, "Remembrance Sunday", "Remembrance Sunday", cat=OBS),
]
_reg("GB-ENG", "Vereinigtes Königreich - England & Wales", "United Kingdom - England & Wales", [
    F(1, 1, *NEUJAHR), GOODF, EASTM,
    N(5, 0, 1, "Bank Holiday (Anfang Mai)", "Early May Bank Holiday"),
    L(5, 0, "Bank Holiday (Ende Mai)", "Spring Bank Holiday"),
    L(8, 0, "Bank Holiday (Ende August)", "Summer Bank Holiday"),
    F(12, 25, *WEIH1), F(12, 26, "Boxing Day (2. Weihnachtstag)", "Boxing Day"),
] + pack(extra=_UK_OBS), sub="uk",
     note_de="Einmalige Sonderfeiertage (z. B. Krönung 2023) sind nicht enthalten; bitte unter 'Eigene Feiertage' ergaenzen.",
     note_en="One-off special bank holidays are not included; add them as custom holidays.")
_reg("GB-SCT", "Vereinigtes Königreich - Schottland", "United Kingdom - Scotland", [
    F(1, 1, *NEUJAHR), F(1, 2, "2. Januar", "2nd January"), GOODF,
    N(5, 0, 1, "Bank Holiday (Anfang Mai)", "Early May Bank Holiday"),
    L(5, 0, "Bank Holiday (Ende Mai)", "Spring Bank Holiday"),
    N(8, 0, 1, "Bank Holiday (Anfang August)", "Summer Bank Holiday"),
    F(11, 30, "St. Andrew's Day", "St Andrew's Day"),
    F(12, 25, *WEIH1), F(12, 26, "Boxing Day (2. Weihnachtstag)", "Boxing Day"),
] + pack(extra=_UK_OBS), sub="uk")

_reg("IE", "Irland", "Ireland", [
    F(1, 1, *NEUJAHR), X("BR", "St. Brigid's Day", "St Brigid's Day", y0=2023),
    F(3, 17, "St. Patrick's Day", "St Patrick's Day"), EASTM,
    N(5, 0, 1, "May Bank Holiday", "May Bank Holiday"), N(6, 0, 1, "June Bank Holiday", "June Bank Holiday"),
    N(8, 0, 1, "August Bank Holiday", "August Bank Holiday"), L(10, 0, "October Bank Holiday", "October Bank Holiday"),
    F(12, 25, *WEIH1), F(12, 26, "St. Stephen's Day", "St Stephen's Day"),
] + pack())

_reg("PL", "Polen", "Poland", [
    F(1, 1, *NEUJAHR), F(1, 6, "Heilige Drei Könige", "Epiphany", y0=2011), EASTS, EASTM, MAY1,
    F(5, 3, "Verfassungstag", "Constitution Day"), WHITS, CORPUS, ASSUMP, ALLSAINTS,
    F(11, 11, "Unabhängigkeitstag", "Independence Day"), F(12, 24, "Heiligabend", "Christmas Eve", y0=2025),
    XMAS1, XMAS2,
] + pack())

_reg("CZ", "Tschechien", "Czechia", [
    F(1, 1, "Neujahr", "New Year's Day"), E(-2, "Karfreitag", "Good Friday", y0=2016), EASTM, MAY1,
    F(5, 8, "Tag des Sieges", "Victory Day"), F(7, 5, "Kyrill und Method", "Saints Cyril and Methodius"),
    F(7, 6, "Jan Hus", "Jan Hus Day"), F(9, 28, "Tag der Staatlichkeit", "Statehood Day"),
    F(10, 28, "Gründung der Tschechoslowakei", "Independence Day"),
    F(11, 17, "Tag des Kampfes für Freiheit", "Struggle for Freedom Day"),
    F(12, 24, "Heiligabend", "Christmas Eve"), XMAS1, XMAS2,
] + pack())

_reg("DK", "Dänemark", "Denmark", [
    F(1, 1, *NEUJAHR), E(-3, "Gründonnerstag", "Maundy Thursday"), GOODF, EASTS, EASTM,
    E(26, "Großer Bettag", "Great Prayer Day", y1=2023), ASC, WHITS, WHITM, XMAS1, XMAS2,
    F(6, 5, "Grundlovsdag (Verfassungstag)", "Constitution Day", cat=OBS),
] + pack())

_reg("SE", "Schweden", "Sweden", [
    F(1, 1, *NEUJAHR), F(1, 6, "Heilige Drei Könige", "Epiphany"), GOODF, EASTS, EASTM, MAY1, ASC, WHITS,
    F(6, 6, "Nationalfeiertag", "National Day"),
    W(6, 20, 5, "Mittsommertag", "Midsummer Day"), W(10, 31, 5, "Allerheiligen", "All Saints' Day"),
    XMAS1, F(12, 26, "Annandag jul (2. Weihnachtstag)", "Boxing Day"),
    W(6, 19, 4, "Mittsommerabend", "Midsummer Eve", cat=OBS),
] + pack())

_reg("NO", "Norwegen", "Norway", [
    F(1, 1, *NEUJAHR), E(-3, "Gründonnerstag", "Maundy Thursday"), GOODF, EASTS, EASTM, MAY1,
    F(5, 17, "Verfassungstag", "Constitution Day"), ASC, WHITS, WHITM, XMAS1, XMAS2,
] + pack())

_reg("FI", "Finnland", "Finland", [
    F(1, 1, *NEUJAHR), F(1, 6, "Heilige Drei Könige", "Epiphany"), GOODF, EASTS, EASTM,
    F(5, 1, "Maifeiertag (Vappu)", "May Day"), ASC, WHITS,
    W(6, 20, 5, "Mittsommertag", "Midsummer Day"), W(10, 31, 5, "Allerheiligen", "All Saints' Day"),
    F(12, 6, "Unabhängigkeitstag", "Independence Day"), F(12, 24, "Heiligabend", "Christmas Eve"),
    XMAS1, F(12, 26, "Tapaninpäivä (2. Weihnachtstag)", "Boxing Day"),
    W(6, 19, 4, "Mittsommerabend", "Midsummer Eve", cat=OBS),
] + pack())

_reg("PT", "Portugal", "Portugal", [
    F(1, 1, *NEUJAHR), GOODF, EASTS, F(4, 25, "Tag der Freiheit", "Freedom Day"), MAY1,
    E(60, "Fronleichnam", "Corpus Christi", y1=2012), E(60, "Fronleichnam", "Corpus Christi", y0=2016),
    F(6, 10, "Nationalfeiertag (Dia de Portugal)", "Portugal Day"), ASSUMP,
    F(10, 5, "Tag der Republik", "Republic Day"),
    F(11, 1, "Allerheiligen", "All Saints' Day", y1=2012), F(11, 1, "Allerheiligen", "All Saints' Day", y0=2016),
    F(12, 1, "Tag der Unabhängigkeit", "Restoration of Independence", y1=2012),
    F(12, 1, "Tag der Unabhängigkeit", "Restoration of Independence", y0=2016),
    IMMAC, F(12, 25, "Weihnachten", "Christmas Day"),
] + pack())

_reg("GR", "Griechenland", "Greece", [
    F(1, 1, *NEUJAHR), F(1, 6, "Epiphanie", "Epiphany"),
    O(-48, "Rosenmontag (Kathara Deftera)", "Clean Monday"),
    F(3, 25, "Unabhängigkeitstag", "Independence Day"),
    O(-2, "Orthodoxer Karfreitag", "Orthodox Good Friday"),
    O(0, "Orthodoxer Ostersonntag", "Orthodox Easter Sunday"),
    O(1, "Orthodoxer Ostermontag", "Orthodox Easter Monday"), MAY1,
    O(50, "Pfingstmontag (Agiou Pnevmatos)", "Orthodox Whit Monday"), ASSUMP,
    F(10, 28, "Ochi-Tag", "Ohi Day"), F(12, 25, "Weihnachten", "Christmas Day"),
    F(12, 26, "Synaxis der Gottesmutter", "Glorifying of the Mother of God"),
] + pack(easter_days=False), note_de="Orthodoxe Osterdaten (gregorianisch umgerechnet).",
     note_en="Orthodox Easter dates (converted to the Gregorian calendar).")

_reg("HU", "Ungarn", "Hungary", [
    F(1, 1, *NEUJAHR), F(3, 15, "Nationalfeiertag 1848", "National Day"), GOODF, EASTS, EASTM, MAY1,
    WHITS, WHITM, F(8, 20, "Staatsgründung (St. Stephan)", "State Foundation Day"),
    F(10, 23, "Gedenktag 1956", "1956 Revolution Day"), ALLSAINTS,
    F(12, 24, "Heiligabend", "Christmas Eve", y0=2024), XMAS1, XMAS2,
] + pack())

_reg("TH", "Thailand", "Thailand", [
    F(1, 1, "Neujahr", "New Year's Day"),
    X("TH", "Makha Bucha", "Makha Bucha Day", "makha"),
    F(4, 6, "Chakri-Tag", "Chakri Memorial Day"),
    F(4, 13, "Songkran (1. Tag)", "Songkran (day 1)"), F(4, 14, "Songkran (2. Tag)", "Songkran (day 2)"),
    F(4, 15, "Songkran (3. Tag)", "Songkran (day 3)"),
    F(5, 1, "Tag der Arbeit", "Labour Day"), F(5, 4, "Krönungstag", "Coronation Day"),
    X("TH", "Visakha Bucha", "Visakha Bucha Day", "visakha"),
    F(6, 3, "Geburtstag Königin Suthida", "Queen Suthida's Birthday"),
    X("TH", "Asahna Bucha", "Asahna Bucha Day", "asahna"),
    X("TH", "Khao Phansa", "Buddhist Lent Day", "khao"),
    F(7, 28, "Geburtstag König Vajiralongkorn", "King Vajiralongkorn's Birthday"),
    F(8, 12, "Muttertag (Geb. Königinmutter)", "Mother's Day (Queen Mother's Birthday)"),
    F(10, 13, "Gedenktag König Bhumibol", "King Bhumibol Memorial Day"),
    F(10, 23, "Chulalongkorn-Tag", "Chulalongkorn Day"),
    F(12, 5, "Vatertag (Geb. König Bhumibol)", "Father's Day (King Bhumibol's Birthday)"),
    F(12, 10, "Verfassungstag", "Constitution Day"),
    F(12, 31, "Silvester", "New Year's Eve"),
], sub="th",
     note_de="Buddhistische Feiertage folgen dem Mondkalender: 2024-2026 sind die offiziellen Daten hinterlegt, sonst Naeherung (+-1 Tag) - bitte pruefen. Zusaetzliche Regierungs-Feiertage je Jahr sind nicht enthalten.",
     note_en="Buddhist holidays follow the lunar calendar: official dates stored for 2024-2026, otherwise approximate (+-1 day). Extra government holidays per year are not included.")

_reg("US", "USA", "United States", [
    F(1, 1, *NEUJAHR), N(1, 0, 3, "Martin-Luther-King-Tag", "Martin Luther King Jr. Day"),
    N(2, 0, 3, "Presidents' Day", "Washington's Birthday"), L(5, 0, "Memorial Day", "Memorial Day"),
    F(6, 19, "Juneteenth", "Juneteenth", y0=2021), F(7, 4, "Unabhängigkeitstag", "Independence Day"),
    N(9, 0, 1, "Labor Day", "Labor Day"), N(10, 0, 2, "Columbus Day", "Columbus Day"),
    F(11, 11, "Veterans Day", "Veterans Day"), N(11, 3, 4, "Thanksgiving", "Thanksgiving Day"),
    F(12, 25, "Weihnachten", "Christmas Day"),
    F(2, 14, "Valentinstag", "Valentine's Day", cat=OBS),
    F(3, 17, "St. Patrick's Day", "St. Patrick's Day", cat=OBS),
    N(3, 6, 2, "Beginn der Sommerzeit", "Daylight saving time starts", cat=OBS),
    E(-2, "Karfreitag", "Good Friday", cat=OBS),
    E(0, "Ostersonntag", "Easter Sunday", cat=OBS),
    N(5, 6, 2, "Muttertag", "Mother's Day", cat=OBS), N(6, 6, 3, "Vatertag", "Father's Day", cat=OBS),
    F(10, 31, "Halloween", "Halloween", cat=OBS),
    N(11, 6, 1, "Ende der Sommerzeit", "Daylight saving time ends", cat=OBS),
    X("EL", "Wahltag (Election Day)", "Election Day", cat=OBS),
    F(12, 24, "Heiligabend", "Christmas Eve", cat=OBS), F(12, 31, "Silvester", "New Year's Eve", cat=OBS),
], sub="us", note_de="Bundesweite (federal) Feiertage; Bundesstaaten haben teils weitere.",
     note_en="Federal holidays; individual states may have more.")

COUNTRY_ORDER = ["DE", "AT", "CH", "FR", "IT", "ES", "NL", "BE", "LU", "GB-ENG", "GB-SCT", "IE", "PL",
                 "CZ", "DK", "SE", "NO", "FI", "PT", "GR", "HU", "TH", "US"]


# --------------------------------------------------------------------------
# Berechnung
# --------------------------------------------------------------------------
def _compute_raw(country: str, state: str, year: int) -> list[Holiday]:
    reg = COUNTRIES[country]
    out: list[Holiday] = []
    for r in reg.rules:
        if not (r.y0 <= year <= r.y1):
            continue
        cat = r.cat
        if r.regions is not None:                       # deutsche Landesregeln
            if state and state in r.regions:
                cat = PUBLIC
            elif state and state in r.partial:
                cat = PARTIAL
            elif not state:
                cat = PARTIAL
            else:
                if not r.obs_elsewhere:
                    continue
                cat = OBS
            if not state and not r.obs_elsewhere:
                continue
        d, approx = _eval(r, year)
        if d is None:
            continue
        out.append(Holiday(d, r.de, r.en, cat, approx))
    return out


def _dedupe(items: list[Holiday]) -> list[Holiday]:
    seen, res = set(), []
    for h in sorted(items, key=lambda h: (h.date, PRIORITY[h.cat])):
        key = (h.date, h.de)
        if key in seen:
            continue
        seen.add(key)
        res.append(h)
    # Brauchtumstage entfallen, wenn der Tag bereits ein Feiertag ist
    strong = {h.date for h in res if h.cat != OBS}
    return [h for h in res if not (h.cat == OBS and h.date in strong)]


def _add_substitutes(items: list[Holiday], sub: str, year: int) -> list[Holiday]:
    if not sub:
        return items
    occupied = {h.date for h in items if h.cat in (PUBLIC, SUB)}
    rules_fixed = {(r.de) for r in _all_rules_of_kind_F(sub)}
    extra = []
    for h in sorted(items, key=lambda h: h.date):
        if h.cat != PUBLIC or h.date.weekday() < 5:
            continue
        if sub == "uk" and h.de not in rules_fixed:
            continue
        if sub == "us":
            if h.de not in rules_fixed:
                continue
            nd = h.date - dt.timedelta(days=1) if h.date.weekday() == 5 else h.date + dt.timedelta(days=1)
            if nd in occupied or nd.year != year:
                continue
        else:
            nd = h.date
            while nd.weekday() >= 5 or nd in occupied:
                nd += dt.timedelta(days=1)
            if nd.year != year:
                continue
        occupied.add(nd)
        extra.append(Holiday(nd, f"Ersatztag: {h.de}", f"Observed: {h.en}", SUB, h.approx))
    return items + extra


_FIXED_CACHE: dict[str, list] = {}


def _all_rules_of_kind_F(sub: str):
    if sub not in _FIXED_CACHE:
        code = {"uk": ("GB-ENG", "GB-SCT"), "us": ("US",), "th": ("TH",)}[sub]
        _FIXED_CACHE[sub] = [r for c in code for r in COUNTRIES[c].rules if r.kind == "F" and r.cat == PUBLIC]
    return _FIXED_CACHE[sub]


def compute_holidays(country: str, state: str, year: int) -> list[Holiday]:
    """Alle Feiertage/Gedenktage eines Jahres, sortiert (ohne Filter)."""
    reg = COUNTRIES[country]
    items = _dedupe(_compute_raw(country, state if country == "DE" else "", year))
    items = _add_substitutes(items, reg.sub, year)
    return sorted(items, key=lambda h: (h.date, PRIORITY[h.cat]))


def region_label(country: str, state: str = "", lang: str = "de") -> str:
    reg = COUNTRIES[country]
    base = reg.en if lang == "en" else reg.de
    if country == "DE" and state in DE_STATES:
        base += " - " + DE_STATES[state][1 if lang == "en" else 0]
    return base


def build_day_map(country: str, state: str, year: int, cats=(PUBLIC, SUB), excluded=(), custom=(),
                  lang: str = "de") -> dict[dt.date, list[Holiday]]:
    """Datum -> Liste von Feiertagen (nach Prioritaet sortiert) fuer den Kalender.

    cats      anzuzeigende Kategorien
    excluded  deutsche Namen, die abgewaehlt wurden
    custom    Eintraege [monat, tag, jahr(0=jedes Jahr), name]
    """
    excluded = set(excluded)
    res: dict[dt.date, list[Holiday]] = {}
    for h in compute_holidays(country, state, year):
        if h.cat in cats and h.de not in excluded:
            res.setdefault(h.date, []).append(h)
    for c in custom:
        try:
            m, d, y, name = int(c[0]), int(c[1]), int(c[2]), str(c[3])
            if y and y != year:
                continue
            day = dt.date(year, m, d)
        except (ValueError, IndexError, TypeError):
            continue
        res.setdefault(day, []).append(Holiday(day, name, name, PUBLIC, custom=True))
    for lst in res.values():
        lst.sort(key=lambda h: PRIORITY[h.cat])
    return res
