"""Farbschemata der Programmoberflaeche (Hell, Dunkel + 12 weitere)."""
from __future__ import annotations

# Schluessel: bg, panel, frame, text, muted, accent, hover
# Alle Werte als Hex; die GUI rechnet sie in RGBA um.
THEMES = {
    "Hell": dict(bg="#F3F4F6", panel="#FFFFFF", frame="#E4E7EB", text="#1F2933", muted="#7B8794",
                 accent="#8EB8F5", hover="#6FA2F0"),
    "Dunkel": dict(bg="#16181D", panel="#1F2229", frame="#2B2F38", text="#E6E8EB", muted="#8A92A0",
                   accent="#3B6FC4", hover="#4C82DB"),
    "Ozean": dict(bg="#0E2433", panel="#143349", frame="#1C455F", text="#E3F2FA", muted="#7FA6BF",
                  accent="#1F8FBF", hover="#2BA9DE"),
    "Wald": dict(bg="#142319", panel="#1B3022", frame="#26422F", text="#E5F0E3", muted="#86A68C",
                 accent="#3F9A5A", hover="#52B870"),
    "Sonnenuntergang": dict(bg="#2A1613", panel="#3A1F1A", frame="#4D2A22", text="#FBE9DC", muted="#C79A86",
                            accent="#D9583B", hover="#F0704F"),
    "Lavendel": dict(bg="#F1ECFA", panel="#FBF9FF", frame="#E3DAF4", text="#2B2056", muted="#8479AD",
                     accent="#B9A5EC", hover="#A28CE0"),
    "Kaffee": dict(bg="#2B1F1A", panel="#392A23", frame="#4A382F", text="#F3E6D8", muted="#B39A86",
                   accent="#A8704E", hover="#C0865F"),
    "Nordlicht": dict(bg="#0F2A2B", panel="#153738", frame="#1E4A4B", text="#E3F6F1", muted="#7FB2AA",
                      accent="#2FA39A", hover="#41C0B6"),
    "Rosé": dict(bg="#FDEEF2", panel="#FFFFFF", frame="#F8DCE5", text="#4A1426", muted="#B07890",
                 accent="#F29BB8", hover="#E97FA3"),
    "Mitternachtsblau": dict(bg="#0B1226", panel="#121C38", frame="#1B2A52", text="#E6ECFB", muted="#7F8FBC",
                             accent="#4A63D6", hover="#6079EE"),
    "Sand": dict(bg="#F6EFE0", panel="#FFFBF1", frame="#EADFC6", text="#3B2A16", muted="#9A8564",
                 accent="#E0B26B", hover="#D29C4A"),
    "Mint": dict(bg="#E8F6F0", panel="#FAFFFC", frame="#D4EDE2", text="#133B2C", muted="#6F9E8A",
                 accent="#7FD1AE", hover="#5CC096"),
    "Cyberpunk": dict(bg="#120B1F", panel="#1B1030", frame="#2A1A48", text="#F2E9FF", muted="#9A86C4",
                      accent="#D6279B", hover="#F23BB5"),
    "Graphit-Orange": dict(bg="#222222", panel="#2C2C2C", frame="#3A3A3A", text="#F0F0F0", muted="#9C9C9C",
                           accent="#E8751A", hover="#FF8C33"),
}
THEME_ORDER = list(THEMES)


def hex_rgba(h: str, a: int = 255) -> tuple[int, int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a


def shade(h: str, f: float) -> str:
    """f>0 heller, f<0 dunkler."""
    r, g, b, _ = hex_rgba(h)
    if f >= 0:
        r, g, b = (round(c + (255 - c) * f) for c in (r, g, b))
    else:
        r, g, b = (round(c * (1 + f)) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def luminance(h: str) -> float:
    r, g, b, _ = hex_rgba(h)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255
