"""Erzeugt das PDF-Handbuch (mit Screenshots) aus help_content."""
from __future__ import annotations

import datetime as dt
import os

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer)

from . import service, settings
from .help_content import SECTIONS
from .layout import Options, build_page
from .render_preview import render_preview

DOCS = os.path.join(settings.BASE_DIR, "docs")
SCREENS = os.path.join(DOCS, "screens")
GUI_SHOTS = ["gui_01_kalender.png", "gui_02_feiertage.png", "gui_03_design.png", "gui_04_dunkel.png"]


def ensure_examples() -> None:
    """Zeichnet die Kalenderbeispiele fuer das Handbuch (unabhaengig von der GUI)."""
    os.makedirs(SCREENS, exist_ok=True)
    o = Options(year=2028, paper="A4", country="DE", state="BY", title="Mein Unternehmen")
    render_preview(build_page(o, region_text="Deutschland - Bayern"), 1500).save(os.path.join(SCREENS, "example_a4.png"))
    big = render_preview(build_page(o, region_text="Deutschland - Bayern"), 2600)
    big.crop((0, 0, int(big.width * 0.5), int(big.height * 0.42))).save(os.path.join(SCREENS, "example_detail.png"))
    o2 = Options(year=2027, paper="A3", country="TH", palette="Ozean", title="Bangkok Office",
                 show_cats=("public", "sub"))
    render_preview(build_page(o2, region_text="Thailand"), 1500).save(os.path.join(SCREENS, "example_th.png"))


def missing_gui_shots() -> list[str]:
    return [f for f in GUI_SHOTS if not os.path.exists(os.path.join(SCREENS, f))]


def _img(path: str, max_w: float) -> Image:
    with PILImage.open(path) as im:
        w, h = im.size
    k = min(max_w / w, 1.0) if False else max_w / w
    return Image(path, width=w * k, height=h * k)


def build_handbook(path: str) -> str:
    ensure_examples()
    ss = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=ss["BodyText"], fontName="Helvetica", fontSize=10, leading=14.5,
                          spaceAfter=7)
    h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=17, textColor=colors.HexColor("#11496B"),
                        spaceBefore=6, spaceAfter=10)
    cap = ParagraphStyle("cap", parent=body, fontSize=8.5, leading=11, textColor=colors.HexColor("#555555"), spaceAfter=12)
    title = ParagraphStyle("title", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=30, leading=36,
                           textColor=colors.HexColor("#11496B"))
    sub = ParagraphStyle("sub", parent=body, fontSize=13, leading=18, alignment=1)

    story = [Spacer(1, 70 * mm), Paragraph("KalenderGen", title),
             Paragraph("Jahreskalender als editierbares PDF", sub), Spacer(1, 8 * mm),
             Paragraph("Handbuch", sub), Spacer(1, 40 * mm),
             Paragraph(f"Stand: {dt.date.today():%d.%m.%Y}", sub), PageBreak()]
    story.append(Paragraph("Inhaltsverzeichnis", h1))
    for sec in SECTIONS:
        story.append(Paragraph(sec["title"], body))
    story.append(PageBreak())
    maxw = A4[0] - 40 * mm
    for i, sec in enumerate(SECTIONS):
        if i:
            story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(sec["title"], h1))
        for p in sec["paras"]:
            story.append(Paragraph(p.replace("&", "&amp;"), body))
        for fn, caption in sec["shots"]:
            fp = os.path.join(SCREENS, fn)
            if os.path.exists(fp):
                story.append(KeepTogether([_img(fp, maxw), Paragraph(caption, cap)]))
            else:
                story.append(Paragraph(f"[Screenshot {fn} noch nicht vorhanden - Hilfe > Screenshots neu aufnehmen]", cap))

    def footer(c, d):
        c.saveState()
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#777777"))
        c.drawCentredString(A4[0] / 2, 10 * mm, f"KalenderGen - Handbuch - Seite {d.page}")
        c.restoreState()

    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm,
                            bottomMargin=20 * mm, title="KalenderGen Handbuch", author="KalenderGen")
    doc.build(story, onFirstPage=lambda c, d: None, onLaterPages=footer)
    return path
