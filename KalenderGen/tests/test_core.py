import datetime as dt
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from kalender import holidays as H  # noqa: E402
from kalender import layout, service, settings  # noqa: E402
from kalender.render_pdf import render_pdf  # noqa: E402
from kalender.render_preview import render_preview  # noqa: E402

D = dt.date


def names(country, state, year, cats=(H.PUBLIC,)):
    return {h.date: h.de for h in H.compute_holidays(country, state, year) if h.cat in cats}


class Holidays(unittest.TestCase):
    def test_easter(self):
        for y, d in {2024: D(2024, 3, 31), 2025: D(2025, 4, 20), 2026: D(2026, 4, 5), 2027: D(2027, 3, 28),
                     2028: D(2028, 4, 16), 2038: D(2038, 4, 25)}.items():
            self.assertEqual(H.easter(y), d)
        self.assertEqual(H.orthodox_easter(2026), D(2026, 4, 12))
        self.assertEqual(H.orthodox_easter(2025), D(2025, 4, 20))

    def test_de_common_2028(self):   # entspricht der Vorlage (Neujahr, Karfreitag, ...)
        n = names("DE", "NW", 2028)
        for d in (D(2028, 1, 1), D(2028, 4, 14), D(2028, 4, 17), D(2028, 5, 1), D(2028, 5, 25), D(2028, 6, 5),
                  D(2028, 10, 3), D(2028, 11, 1), D(2028, 12, 25), D(2028, 12, 26)):
            self.assertIn(d, n, d)
        self.assertNotIn(D(2028, 10, 31), n)

    def test_de_states(self):
        self.assertIn(D(2028, 1, 6), names("DE", "BY", 2028))
        self.assertNotIn(D(2028, 1, 6), names("DE", "NW", 2028))
        self.assertIn(D(2028, 6, 15), names("DE", "BW", 2028))
        self.assertNotIn(D(2028, 6, 15), names("DE", "BE", 2028))
        self.assertIn(D(2025, 11, 19), names("DE", "SN", 2025))          # Buss- und Bettag
        self.assertIn(D(2028, 11, 22), names("DE", "SN", 2028))
        self.assertIn(D(2028, 3, 8), names("DE", "BE", 2028))
        self.assertIn(D(2023, 3, 8), names("DE", "MV", 2023))
        self.assertNotIn(D(2022, 3, 8), names("DE", "MV", 2022))
        self.assertIn(D(2028, 4, 16), names("DE", "BB", 2028))          # Ostersonntag BB
        self.assertIn(D(2028, 9, 20), names("DE", "TH", 2028))
        self.assertIn(D(2018, 10, 31), names("DE", "NI", 2018))
        self.assertNotIn(D(2017, 10, 31) if False else D(2016, 10, 31), names("DE", "NI", 2016))
        self.assertIn(D(2017, 10, 31), names("DE", "HH", 2017))         # 500 Jahre Reformation
        self.assertIn(D(2025, 5, 8), names("DE", "BE", 2025))
        self.assertNotIn(D(2026, 5, 8), names("DE", "BE", 2026))
        # Bundesweit: Regionales nur als 'regional'
        self.assertNotIn(D(2028, 1, 6), names("DE", "", 2028))
        self.assertIn(D(2028, 1, 6), names("DE", "", 2028, (H.PARTIAL,)))
        self.assertEqual(len([h for h in H.compute_holidays("DE", "", 2028) if h.cat == H.PUBLIC]), 9)

    def test_other_countries(self):
        self.assertIn(D(2026, 11, 26), names("US", "", 2026))
        self.assertIn(D(2026, 5, 25), names("US", "", 2026))
        self.assertIn(D(2026, 7, 3), names("US", "", 2026, (H.SUB,)))     # 4. Juli = Samstag
        self.assertIn(D(2025, 4, 26), names("NL", "", 2025))             # Koningsdag (27.4. = Sonntag)
        self.assertIn(D(2026, 4, 27), names("NL", "", 2026))
        self.assertIn(D(2026, 6, 20), names("SE", "", 2026))
        self.assertIn(D(2026, 10, 31), names("SE", "", 2026))
        self.assertIn(D(2026, 5, 25), names("GB-ENG", "", 2026))
        self.assertIn(D(2027, 12, 27), names("GB-ENG", "", 2027, (H.SUB,)))
        self.assertIn(D(2027, 2, 1), names("IE", "", 2027))
        self.assertIn(D(2028, 2, 7), names("IE", "", 2028))
        self.assertIn(D(2026, 4, 12), names("GR", "", 2026))
        self.assertIn(D(2028, 5, 17), names("NO", "", 2028))
        self.assertIn(D(2028, 7, 14), names("FR", "", 2028))
        self.assertIn(D(2028, 10, 26), names("AT", "", 2028))
        self.assertIn(D(2028, 8, 1), names("CH", "", 2028))

    def test_thailand(self):
        n = names("TH", "", 2026)
        self.assertIn(D(2026, 3, 3), n)
        self.assertIn(D(2026, 5, 31), n)
        self.assertIn(D(2026, 7, 29), n)
        self.assertIn(D(2026, 7, 30), n)       # Khao Phansa
        self.assertFalse(any(h.approx for h in H.compute_holidays("TH", "", 2026)))
        self.assertTrue(any(h.approx for h in H.compute_holidays("TH", "", 2027)))
        self.assertIn(D(2027, 2, 22), names("TH", "", 2027, (H.SUB,)))    # Makha am Sonntag
        # Naeherung liegt im plausiblen Bereich
        for y in range(2028, 2040):
            hs = {h.de: h.date for h in H.compute_holidays("TH", "", y) if h.cat == H.PUBLIC}
            self.assertTrue(D(y, 2, 5) <= hs["Makha Bucha"] <= D(y, 3, 10), (y, hs["Makha Bucha"]))
            self.assertTrue(D(y, 4, 28) <= hs["Visakha Bucha"] <= D(y, 6, 5), (y, hs["Visakha Bucha"]))
            self.assertTrue(D(y, 6, 25) <= hs["Asahna Bucha"] <= D(y, 8, 5), (y, hs["Asahna Bucha"]))

    def test_all_regions_all_years(self):
        for c in H.COUNTRY_ORDER:
            for y in (1999, 2024, 2027, 2028, 2050, 2099):
                for st in (list(H.DE_STATES) if c == "DE" else [""]):
                    lst = H.compute_holidays(c, st, y)
                    self.assertTrue(lst)
                    self.assertTrue(all(h.date.year == y for h in lst), (c, st, y))

    def test_filters(self):
        m = H.build_day_map("DE", "BY", 2028, (H.PUBLIC,), excluded=("Neujahr",), custom=[(7, 1, 0, "Feier")])
        self.assertNotIn(D(2028, 1, 1), m)
        self.assertIn(D(2028, 7, 1), m)
        m2 = H.build_day_map("DE", "BY", 2029, (H.PUBLIC,), custom=[(7, 1, 2028, "Nur 2028")])
        self.assertNotIn(D(2029, 7, 1), m2)


class Layout(unittest.TestCase):
    def test_vorlage_2028(self):
        """Fusszeile (Mo-Fr-Tage) und Grundstruktur wie in der Excel-Vorlage 2028."""
        p = layout.build_page(layout.Options(year=2028, paper="A4", country="DE", state="NW"))
        self.assertEqual(p.workdays, [21, 21, 23, 20, 23, 22, 21, 23, 21, 22, 22, 21])
        self.assertEqual(D(2028, 1, 3).isocalendar()[1], 1)
        self.assertEqual(D(2028, 12, 4).isocalendar()[1], 49)
        pal = layout.PALETTES[0]
        inv = [i for i in p.items if isinstance(i, layout.Rect) and i.fill == pal.invalid and abs(i.h - p.cell_h) < 1e-6]
        self.assertEqual(len(inv), 6)       # 2028 ist Schaltjahr: Feb 30,31 + 4x 31.
        p27 = layout.build_page(layout.Options(year=2027, paper="A4"))
        inv27 = [i for i in p27.items if isinstance(i, layout.Rect) and i.fill == pal.invalid and abs(i.h - p27.cell_h) < 1e-6]
        self.assertEqual(len(inv27), 7)
        leap = [i for i in p.items if isinstance(i, layout.Rect) and i.fill == pal.leap and abs(i.h - p.cell_h) < 1e-6]
        self.assertEqual(len(leap), 1)

    def test_workdays_deduct(self):
        a = layout.build_page(layout.Options(year=2028, workdays_deduct=True, country="DE", state="NW"))
        self.assertEqual(a.workdays[3], 18)    # April: Karfreitag + Ostermontag

    def test_text_inside_page(self):
        for paper in layout.PAPER_MM:
            for land in (True, False):
                for c in ("DE", "TH", "GB-ENG", "SE"):
                    o = layout.Options(year=2027, paper=paper, landscape=land, country=c, state="BY" if c == "DE" else "",
                                       show_cats=(H.PUBLIC, H.SUB, H.PARTIAL, H.OBS))
                    p = layout.build_page(o)
                    for it in p.items:
                        if isinstance(it, layout.Text):
                            w = layout.tw(it.s, it.pt, it.bold)
                            x0 = it.x - (w if it.align == "r" else w / 2 if it.align == "c" else 0)
                            self.assertGreaterEqual(x0, -0.01)
                            self.assertLessEqual(x0 + w, p.width + 0.01)
                            self.assertTrue(0 <= it.y <= p.height)


class Output(unittest.TestCase):
    def test_pdf_matrix(self):
        from pypdf import PdfReader
        tmp = tempfile.mkdtemp()
        for paper, (w, h) in layout.PAPER_MM.items():
            for land in (True, False):
                s = settings.defaults()
                s.update(year=2028, paper=paper, landscape=land, out_dir=tmp, state="BY",
                         cal_palette=layout.PALETTES[hash(paper) % len(layout.PALETTES)].name_de)
                path = service.export_pdf(s)
                r = PdfReader(path)
                self.assertEqual(len(r.pages), 1)
                mb = r.pages[0].mediabox
                self.assertAlmostEqual(float(mb.width) / 72 * 25.4, h if land else w, delta=0.5)
                self.assertGreater(len(r.get_fields()), 300)

    def test_no_fields_and_all_palettes(self):
        from pypdf import PdfReader
        tmp = tempfile.mkdtemp()
        for pal in layout.PALETTES:
            s = settings.defaults()
            s.update(year=2027, paper="A4", out_dir=tmp, cal_palette=pal.name_de, fields=False, country="US")
            r = PdfReader(service.export_pdf(s))
            self.assertFalse(r.get_fields())

    def test_logo(self):
        from PIL import Image
        tmp = tempfile.mkdtemp()
        logo = os.path.join(tmp, "logo.png")
        Image.new("RGBA", (300, 120), (200, 30, 30, 255)).save(logo)
        s = settings.defaults()
        s.update(year=2027, paper="A4", out_dir=tmp, logo=logo, title="Firma")
        service.export_pdf(s)
        img = render_preview(service.make_page(s), 800)
        self.assertGreater(img.width, 700)


if __name__ == "__main__":
    unittest.main(verbosity=1)
