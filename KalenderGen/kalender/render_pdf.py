"""PDF-Ausgabe (reportlab) mit editierbaren Formularfeldern."""
from __future__ import annotations

from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .layout import Field, Image, Page, Rect, Text


def render_pdf(page: Page, path: str, title: str = "Jahreskalender", editable: bool = True) -> str:
    c = canvas.Canvas(path, pagesize=(page.width * mm, page.height * mm))
    c.setTitle(title)
    c.setAuthor("KalenderGen")
    c.setSubject(f"Jahreskalender {page.year}")
    H = page.height

    def Y(y):          # Layout-Y (oben) -> PDF-Y (unten)
        return (H - y) * mm

    fields: list[Field] = []
    for it in page.items:
        if isinstance(it, Rect):
            if it.fill is None and it.stroke is None:
                continue
            if it.fill:
                c.setFillColor(HexColor(it.fill))
            if it.stroke:
                c.setStrokeColor(HexColor(it.stroke))
                c.setLineWidth(it.lw * mm)
            c.rect(it.x * mm, Y(it.y + it.h), it.w * mm, it.h * mm, stroke=1 if it.stroke else 0,
                   fill=1 if it.fill else 0)
        elif isinstance(it, Text):
            c.setFillColor(HexColor(it.color))
            c.setFont("Helvetica-Bold" if it.bold else "Helvetica", it.pt)
            if it.align == "r":
                c.drawRightString(it.x * mm, Y(it.y), it.s)
            elif it.align == "c":
                c.drawCentredString(it.x * mm, Y(it.y), it.s)
            else:
                c.drawString(it.x * mm, Y(it.y), it.s)
        elif isinstance(it, Image):
            c.drawImage(it.path, it.x * mm, Y(it.y + it.h), it.w * mm, it.h * mm, mask="auto",
                        preserveAspectRatio=True)
        elif isinstance(it, Field):
            fields.append(it)
    if editable:
        form = c.acroForm
        for f in fields:
            form.textfield(name=f.name, tooltip=f.tooltip or f.name, value=f.value,
                           x=f.x * mm, y=Y(f.y + f.h), width=f.w * mm, height=f.h * mm,
                           borderWidth=0, borderColor=None, fillColor=None,
                           textColor=HexColor(f.color), forceBorder=False,
                           fontName="Helvetica", fontSize=f.pt,
                           maxlen=200)
    c.showPage()
    c.save()
    return path
