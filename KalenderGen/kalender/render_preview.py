"""Vorschau-Rendering mit PIL (nutzt dieselben Zeichenobjekte wie das PDF)."""
from __future__ import annotations

import os
import sys

from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont

from .layout import PT_PER_MM, Field, Image, Page, Rect, Text

_REG = ["LiberationSans-Regular.ttf", "Arial.ttf", "arial.ttf", "DejaVuSans.ttf", "Helvetica.ttc"]
_BOLD = ["LiberationSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"]
_DIRS = ["/usr/share/fonts/truetype/liberation", "/usr/share/fonts/truetype/dejavu",
         "/usr/share/fonts/liberation", "/usr/share/fonts/TTF", "/usr/share/fonts/truetype/ubuntu",
         "C:/Windows/Fonts", "/Library/Fonts", "/System/Library/Fonts/Supplemental"]


def find_font(bold: bool = False) -> str | None:
    for d in _DIRS:
        for n in (_BOLD if bold else _REG):
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None


_cache: dict = {}


def _font(bold: bool, px: int):
    key = (bold, px)
    if key not in _cache:
        p = find_font(bold)
        try:
            _cache[key] = ImageFont.truetype(p, px) if p else ImageFont.load_default(px)
        except Exception:
            _cache[key] = ImageFont.load_default()
    return _cache[key]


def render_preview(page: Page, px_long: int = 1100) -> PILImage.Image:
    scale = px_long / max(page.width, page.height)       # px je mm
    W, H = round(page.width * scale), round(page.height * scale)
    img = PILImage.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    for it in page.items:
        if isinstance(it, Rect):
            box = [it.x * scale, it.y * scale, (it.x + it.w) * scale - 1, (it.y + it.h) * scale - 1]
            d.rectangle(box, fill=it.fill, outline=it.stroke, width=max(1, round(it.lw * scale)) if it.stroke else 0)
        elif isinstance(it, Text):
            px = max(1, round(it.pt / PT_PER_MM * scale))
            anchor = {"l": "ls", "c": "ms", "r": "rs"}[it.align]
            d.text((it.x * scale, it.y * scale), it.s, fill=it.color, font=_font(it.bold, px), anchor=anchor)
        elif isinstance(it, Image):
            try:
                with PILImage.open(it.path) as im:
                    im = im.convert("RGBA")
                    w, h = round(it.w * scale), round(it.h * scale)
                    im = im.resize((max(w, 1), max(h, 1)))
                    img.paste(im, (round(it.x * scale), round(it.y * scale)), im)
            except Exception:
                pass
        elif isinstance(it, Field) and it.value:
            px = max(1, round(it.pt / PT_PER_MM * scale))
            d.text((it.x * scale, (it.y + it.h * 0.72) * scale), it.value, fill=it.color,
                   font=_font(it.bold, px), anchor="ls")
    return img
