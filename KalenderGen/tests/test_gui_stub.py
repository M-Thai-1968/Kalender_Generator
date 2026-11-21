import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dpg_stub

stub = dpg_stub.install()

from kalender import gui, handbook, settings  # noqa: E402

tmp = tempfile.mkdtemp()
settings.CONFIG_FILE = os.path.join(tmp, "settings.json")
gui.settings.CONFIG_FILE = settings.CONFIG_FILE
handbook.SCREENS = os.path.join(tmp, "screens")
handbook.DOCS = tmp

app = gui.App()
app.s["out_dir"] = tmp
app.s["year"] = 2028
# Aufbau wie in App.run()
app.setup_fonts()
stub.add_texture_registry(tag="tex_reg")
app.build_dialogs()
app.build_main()
app.build_help_window()
app.apply_theme()
app.fill_holiday_list()
app.refresh_preview()
assert app.preview_tex is not None
print("aufbau ok, row_info:", stub.values.get("row_info"))

# Callbacks
app.on_year(None, 2030)
app.on_paper(None, "A4 (210 x 297 mm)")
app.on_orient(None, "Hoch")
assert app.s["paper"] == "A4" and not app.s["landscape"]
app.on_country(None, "Österreich")
assert app.s["country"] == "AT"
app.on_country(None, "Deutschland")
app.on_state(None, "Bayern")
assert app.s["state"] == "BY"
app.on_check(None, True, "cat_obs")
app.on_check(None, True, "cat_partial")
app.on_hol_toggle(None, False, "Neujahr")
assert "Neujahr" in app.s["excluded"]["DE|BY"]
stub.values["cu_name"] = "Betriebsfeier"; stub.values.update(cu_day=1, cu_month=7, cu_year=0)
app.on_custom_add()
assert app.s["custom"] == [[7, 1, 0, "Betriebsfeier"]]
app.on_palette(None, "Ozean")
app.on_title(None, "Firma")
app.on_custom_del(None, None, 0)
app.on_check(None, False, "fields")
for th in ["Dunkel", "Cyberpunk", "Mint"]:
    app.set_ui_theme(th)
app.refresh_preview()

# PDF
app.on_generate()
assert app.last_pdf and os.path.exists(app.last_pdf), stub.values.get("status")
print("pdf:", os.path.basename(app.last_pdf))
app.s["filename"] = "mein"
app.on_generate()
assert app.last_pdf.endswith("mein.pdf")

# Sprache
app.on_lang(None, "English")
assert app.lang() == "en"
app.on_lang(None, "Deutsch")

# Hilfe + Screenshots + Handbuch
for i in range(len(gui.SECTIONS)):
    app.show_help_section(i)
app.save_handbook()
stub.run_frame_callbacks()
hb = os.path.join(tmp, "Handbuch_KalenderGen.pdf")
assert os.path.exists(hb), os.listdir(tmp)
assert len(stub.fb_files) == 4
print("handbuch ok", os.path.getsize(hb), "Screenshots:", [os.path.basename(f) for f in stub.fb_files])
errs = os.path.join(tmp, "error.log")
print("error.log:", os.path.exists(gui.LOGFILE) and open(gui.LOGFILE).read()[-500:])
print("ALLES OK")
