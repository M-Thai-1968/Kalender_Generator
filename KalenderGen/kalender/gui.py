"""Dear-PyGui-Oberflaeche von KalenderGen."""
from __future__ import annotations

import datetime as dt
import os
import time
import traceback

import dearpygui.dearpygui as dpg
import numpy as np
from PIL import Image as PILImage

from . import handbook, osutil, service, settings
from . import holidays as H
from .help_content import SECTIONS
from .i18n import t
from .layout import PALETTES, PAPER_MM, palette_by_name
from .render_preview import find_font, render_preview
from .themes import THEME_ORDER, THEMES, hex_rgba, luminance, shade

LOGFILE = os.path.join(settings.CONFIG_DIR, "error.log")
LEFT_W = 480
WD_DE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
WD_EN = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def log_error(exc: BaseException) -> None:
    try:
        os.makedirs(settings.CONFIG_DIR, exist_ok=True)
        with open(LOGFILE, "a", encoding="utf-8") as f:
            f.write(f"--- {dt.datetime.now():%Y-%m-%d %H:%M:%S}\n{traceback.format_exc()}\n")
    except OSError:
        pass


class App:
    def __init__(self) -> None:
        self.s = settings.load()
        self.dirty_at: float | None = None
        self.theme_ids: dict[str, int] = {}
        self.preview_tex: int | None = None
        self.preview_size = (1, 1)
        self.last_pdf: str | None = None
        self.help_idx = 0
        self.help_tex: dict[str, tuple[int, int, int]] = {}
        self.shot_busy = False
        self.last_manual: str | None = None

    # ------------------------------------------------------------------ helpers
    def T(self, key: str) -> str:
        return t(key, self.s["ui_lang"])

    def lang(self) -> str:
        return self.s["ui_lang"]

    def country_items(self) -> dict[str, str]:
        return {H.region_label(c, "", self.lang()): c for c in H.COUNTRY_ORDER}

    def state_items(self) -> dict[str, str]:
        idx = 1 if self.lang() == "en" else 0
        items = {self.T("state_none"): ""}
        for code, names in sorted(H.DE_STATES.items(), key=lambda kv: kv[1][idx]):
            items[names[idx]] = code
        return items

    def paper_label(self, p: str) -> str:
        w, h = PAPER_MM[p]
        return f"{p} ({w} x {h} mm)"

    def changed(self) -> None:
        self.dirty_at = time.time() + 0.25

    def status(self, msg: str, error: bool = False) -> None:
        if dpg.does_item_exist("status"):
            dpg.set_value("status", msg)
            dpg.configure_item("status", color=(220, 70, 70, 255) if error else (90, 170, 90, 255))

    # --------------------------------------------------------------------- run
    def run(self) -> None:
        dpg.create_context()
        self.setup_fonts()
        dpg.add_texture_registry(tag="tex_reg")
        self.build_dialogs()
        self.build_main()
        self.build_help_window()
        dpg.create_viewport(title=self.T("app_title"), width=1500, height=900, min_width=1000, min_height=620)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main", True)
        dpg.set_viewport_resize_callback(lambda s, a: self.layout_preview())
        self.apply_theme()
        self.fill_holiday_list()
        self.refresh_preview()
        while dpg.is_dearpygui_running():
            self.tick()
            dpg.render_dearpygui_frame()
        settings.save(self.s)
        dpg.destroy_context()

    def select_tab(self, tag: str) -> None:
        dpg.set_value("tabs", dpg.get_alias_id(tag))

    def tick(self) -> None:
        if self.dirty_at is not None and time.time() >= self.dirty_at:
            self.dirty_at = None
            self.refresh_preview()
            settings.save(self.s)

    def setup_fonts(self) -> None:
        path = find_font(False)
        if not path:
            return
        try:
            with dpg.font_registry():
                f = dpg.add_font(path, 17)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default, parent=f)
            dpg.bind_font(f)
        except Exception as e:           # Schrift ist nur Komfort
            log_error(e)

    # ------------------------------------------------------------------ themes
    def make_theme(self, p: dict) -> int:
        def c(item, hexv, a=255):
            dpg.add_theme_color(item, hex_rgba(hexv, a), category=dpg.mvThemeCat_Core)

        acc, hov = p["accent"], p["hover"]
        with dpg.theme() as th:
            with dpg.theme_component(dpg.mvAll):
                c(dpg.mvThemeCol_WindowBg, p["bg"])
                c(dpg.mvThemeCol_ChildBg, p["panel"])
                c(dpg.mvThemeCol_PopupBg, p["panel"])
                c(dpg.mvThemeCol_MenuBarBg, p["panel"])
                c(dpg.mvThemeCol_TitleBg, p["panel"])
                c(dpg.mvThemeCol_TitleBgActive, acc)
                c(dpg.mvThemeCol_TitleBgCollapsed, p["panel"])
                c(dpg.mvThemeCol_Border, p["muted"], 110)
                c(dpg.mvThemeCol_Text, p["text"])
                c(dpg.mvThemeCol_TextDisabled, p["muted"])
                c(dpg.mvThemeCol_FrameBg, p["frame"])
                c(dpg.mvThemeCol_FrameBgHovered, shade(p["frame"], 0.12 if luminance(p["bg"]) < 0.5 else -0.06))
                c(dpg.mvThemeCol_FrameBgActive, acc, 160)
                c(dpg.mvThemeCol_Button, acc)
                c(dpg.mvThemeCol_ButtonHovered, hov)
                c(dpg.mvThemeCol_ButtonActive, shade(hov, -0.15))
                c(dpg.mvThemeCol_Header, acc, 120)
                c(dpg.mvThemeCol_HeaderHovered, hov, 170)
                c(dpg.mvThemeCol_HeaderActive, hov, 220)
                c(dpg.mvThemeCol_Tab, p["frame"])
                c(dpg.mvThemeCol_TabHovered, hov)
                c(dpg.mvThemeCol_TabActive, acc)
                c(dpg.mvThemeCol_CheckMark, hov)
                c(dpg.mvThemeCol_SliderGrab, acc)
                c(dpg.mvThemeCol_SliderGrabActive, hov)
                c(dpg.mvThemeCol_ScrollbarBg, p["bg"])
                c(dpg.mvThemeCol_ScrollbarGrab, p["muted"], 160)
                c(dpg.mvThemeCol_Separator, p["muted"], 120)
                for item, v in ((dpg.mvStyleVar_FrameRounding, 5), (dpg.mvStyleVar_WindowRounding, 6),
                                (dpg.mvStyleVar_ChildRounding, 6), (dpg.mvStyleVar_GrabRounding, 4),
                                (dpg.mvStyleVar_PopupRounding, 5), (dpg.mvStyleVar_TabRounding, 5)):
                    dpg.add_theme_style(item, v, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 7, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 7, category=dpg.mvThemeCat_Core)
        return th

    def apply_theme(self) -> None:
        name = self.s["ui_theme"] if self.s["ui_theme"] in THEMES else "Hell"
        if name not in self.theme_ids:
            self.theme_ids[name] = self.make_theme(THEMES[name])
        dpg.bind_theme(self.theme_ids[name])

    def set_ui_theme(self, name: str) -> None:
        self.s["ui_theme"] = name
        if dpg.does_item_exist("cmb_theme"):
            dpg.set_value("cmb_theme", name)
        self.apply_theme()
        settings.save(self.s)

    # ----------------------------------------------------------------- dialogs
    def build_dialogs(self) -> None:
        with dpg.file_dialog(directory_selector=False, show=False, callback=self.on_logo_chosen, tag="dlg_logo",
                             width=720, height=440, modal=True):
            dpg.add_file_extension(".*")
            dpg.add_file_extension(".png", color=(90, 200, 120, 255))
            dpg.add_file_extension(".jpg", color=(90, 200, 120, 255))
            dpg.add_file_extension(".jpeg", color=(90, 200, 120, 255))
        with dpg.file_dialog(directory_selector=True, show=False, callback=self.on_dir_chosen, tag="dlg_dir",
                             width=720, height=440, modal=True):
            pass

    def on_logo_chosen(self, sender, app_data) -> None:
        path = app_data.get("file_path_name", "")
        if path and os.path.isfile(path):
            self.s["logo"] = path
            dpg.set_value("txt_logo", os.path.basename(path))
            self.changed()

    def on_dir_chosen(self, sender, app_data) -> None:
        path = app_data.get("file_path_name", "")
        if path and os.path.isdir(path):
            self.s["out_dir"] = path
            dpg.set_value("txt_outdir", path)
            self.changed()

    # -------------------------------------------------------------- main window
    def build_main(self) -> None:
        T = self.T
        with dpg.window(tag="main", menubar=True):
            with dpg.menu_bar():
                with dpg.menu(label=T("menu_file")):
                    dpg.add_menu_item(label=T("menu_pdf"), callback=self.on_generate)
                    dpg.add_menu_item(label=T("menu_save"), callback=lambda: settings.save(self.s))
                    dpg.add_separator()
                    dpg.add_menu_item(label=T("menu_quit"), callback=lambda: dpg.stop_dearpygui())
                with dpg.menu(label=T("menu_view")):
                    with dpg.menu(label=T("menu_theme")):
                        for name in THEME_ORDER:
                            dpg.add_menu_item(label=name, callback=lambda s, a, u: self.set_ui_theme(u), user_data=name)
                with dpg.menu(label=T("menu_help")):
                    dpg.add_menu_item(label=T("help_manual"), callback=lambda: self.show_help())
                    dpg.add_menu_item(label=T("help_pdf"), callback=lambda: self.save_handbook())
                    dpg.add_menu_item(label=T("help_screens"), callback=lambda: self.take_screenshots())
                    dpg.add_separator()
                    dpg.add_menu_item(label=T("help_about"), callback=lambda: self.status(T("about_text").replace("\n", " - ")))

            with dpg.group(horizontal=True):
                with dpg.child_window(tag="left", width=LEFT_W, border=False):
                    with dpg.tab_bar(tag="tabs"):
                        with dpg.tab(label=T("tab_cal"), tag="tab_cal"):
                            self.build_tab_calendar()
                        with dpg.tab(label=T("tab_hol"), tag="tab_hol"):
                            self.build_tab_holidays()
                        with dpg.tab(label=T("tab_design"), tag="tab_design"):
                            self.build_tab_design()
                with dpg.child_window(tag="right", width=-1, border=False):
                    with dpg.group(horizontal=True):
                        dpg.add_button(label=T("btn_pdf"), width=170, height=34, callback=self.on_generate, tag="btn_pdf")
                        dpg.add_button(label=T("btn_open"), width=130, height=34, callback=self.on_open)
                        dpg.add_button(label=T("btn_print"), width=110, height=34, callback=self.on_print)
                    dpg.add_text(T("status_none"), tag="status", wrap=900, color=(140, 140, 140, 255))
                    dpg.add_text(T("preview_note"), color=(140, 140, 140, 255))
                    with dpg.child_window(tag="prev_scroll", width=-1, height=-1, border=True,
                                          horizontal_scrollbar=True):
                        dpg.add_group(tag="prev_group")

    # ----------------------------------------------------------------- tab: kalender
    def build_tab_calendar(self) -> None:
        T, s = self.T, self.s
        dpg.add_spacer(height=4)
        dpg.add_text(T("year"))
        dpg.add_input_int(tag="in_year", default_value=int(s["year"]), min_value=1900, max_value=2099,
                          min_clamped=True, max_clamped=True, width=160, callback=self.on_year)
        dpg.add_text(T("paper"))
        dpg.add_combo([self.paper_label(p) for p in PAPER_MM], tag="cmb_paper",
                      default_value=self.paper_label(s["paper"]), width=240, callback=self.on_paper)
        dpg.add_text("", tag="row_info", color=(140, 140, 140, 255))
        dpg.add_text(T("orientation"))
        dpg.add_radio_button([T("landscape"), T("portrait")], tag="rad_orient", horizontal=True,
                             default_value=T("landscape") if s["landscape"] else T("portrait"),
                             callback=self.on_orient)
        dpg.add_spacer(height=4)
        dpg.add_text(T("title"))
        dpg.add_input_text(tag="in_title", default_value=s["title"], width=-1, callback=self.on_title)
        dpg.add_text(T("logo"))
        with dpg.group(horizontal=True):
            dpg.add_button(label=T("logo_choose"), callback=lambda: dpg.show_item("dlg_logo"))
            dpg.add_button(label=T("logo_remove"), callback=self.on_logo_remove)
        dpg.add_text(os.path.basename(s["logo"]) if s["logo"] else T("no_logo"), tag="txt_logo",
                     color=(140, 140, 140, 255))
        dpg.add_spacer(height=4)
        with dpg.collapsing_header(label=T("options"), default_open=True):
            for key, label in (("week_numbers", "week_numbers"), ("workday_row", "workday_row"),
                               ("workdays_deduct", "workdays_deduct"), ("highlight_leap", "leap"),
                               ("weekend_wins", "weekend_wins"), ("show_bg", "bg"), ("fields", "fields"),
                               ("legend", "legend")):
                dpg.add_checkbox(label=T(label), default_value=bool(s[key]), user_data=key, callback=self.on_check)
        dpg.add_spacer(height=4)
        dpg.add_text(T("out_dir"))
        dpg.add_input_text(tag="txt_outdir", default_value=s["out_dir"], width=-1, readonly=True)
        dpg.add_button(label=T("choose_dir"), callback=lambda: dpg.show_item("dlg_dir"))
        dpg.add_text(T("filename"))
        dpg.add_input_text(tag="in_filename", default_value=s.get("filename", ""), width=-1,
                           callback=lambda s_, a: self.s.__setitem__("filename", a))

    def on_year(self, sender, value) -> None:
        self.s["year"] = int(value)
        self.fill_holiday_list()
        self.changed()

    def on_paper(self, sender, value) -> None:
        self.s["paper"] = value.split(" ")[0]
        self.changed()

    def on_orient(self, sender, value) -> None:
        self.s["landscape"] = value == self.T("landscape")
        self.changed()

    def on_title(self, sender, value) -> None:
        self.s["title"] = value
        self.changed()

    def on_logo_remove(self) -> None:
        self.s["logo"] = ""
        dpg.set_value("txt_logo", self.T("no_logo"))
        self.changed()

    def on_check(self, sender, value, key) -> None:
        self.s[key] = bool(value)
        if key.startswith("cat_"):
            self.fill_holiday_list()
        self.changed()

    # ---------------------------------------------------------------- tab: feiertage
    def build_tab_holidays(self) -> None:
        T, s = self.T, self.s
        dpg.add_spacer(height=4)
        dpg.add_text(T("country"))
        countries = self.country_items()
        cur = H.region_label(s["country"], "", self.lang())
        dpg.add_combo(list(countries), tag="cmb_country", default_value=cur, width=-1, callback=self.on_country)
        with dpg.group(tag="state_group", show=(s["country"] == "DE")):
            dpg.add_text(T("state"))
            states = self.state_items()
            cur_state = next((k for k, v in states.items() if v == s["state"]), T("state_none"))
            dpg.add_combo(list(states), tag="cmb_state", default_value=cur_state, width=-1, callback=self.on_state)
        dpg.add_text("", tag="region_note", wrap=LEFT_W - 40, color=(140, 140, 140, 255))
        dpg.add_text("", tag="approx_note", wrap=LEFT_W - 40, color=(220, 150, 40, 255))
        dpg.add_spacer(height=4)
        dpg.add_text(T("categories"))
        for key, label in (("cat_public", "cat_public"), ("cat_sub", "cat_sub"), ("cat_partial", "cat_partial"),
                           ("cat_obs", "cat_obs")):
            dpg.add_checkbox(label=T(label), default_value=bool(s[key]), user_data=key, callback=self.on_check)
        dpg.add_spacer(height=4)
        dpg.add_text(T("holiday_list"))
        with dpg.child_window(tag="hol_list", height=250, border=True):
            dpg.add_group(tag="hol_rows")
        dpg.add_spacer(height=6)
        with dpg.collapsing_header(label=T("custom_title"), default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_input_int(tag="cu_day", default_value=1, min_value=1, max_value=31, min_clamped=True,
                                  max_clamped=True, width=90)
                dpg.add_input_int(tag="cu_month", default_value=1, min_value=1, max_value=12, min_clamped=True,
                                  max_clamped=True, width=90)
                dpg.add_input_int(tag="cu_year", default_value=0, min_value=0, max_value=2099, min_clamped=True,
                                  max_clamped=True, width=110)
            dpg.add_text(f"{T('custom_day')} / {T('custom_month')} / {T('custom_year')}",
                         color=(140, 140, 140, 255))
            with dpg.group(horizontal=True):
                dpg.add_input_text(tag="cu_name", hint=T("custom_hint"), width=270)
                dpg.add_button(label=T("custom_add"), callback=self.on_custom_add)
            dpg.add_group(tag="custom_rows")
        self.fill_custom_list()

    def on_country(self, sender, value) -> None:
        self.s["country"] = self.country_items()[value]
        dpg.configure_item("state_group", show=(self.s["country"] == "DE"))
        self.fill_holiday_list()
        self.changed()

    def on_state(self, sender, value) -> None:
        self.s["state"] = self.state_items().get(value, "")
        self.fill_holiday_list()
        self.changed()

    def enabled_cats(self) -> tuple:
        s = self.s
        cats = []
        if s["cat_public"]:
            cats.append(H.PUBLIC)
        if s["cat_sub"]:
            cats.append(H.SUB)
        if s["cat_partial"]:
            cats.append(H.PARTIAL)
        if s["cat_obs"]:
            cats.append(H.OBS)
        return tuple(cats)

    def fill_holiday_list(self) -> None:
        if not dpg.does_item_exist("hol_rows"):
            return
        s = self.s
        dpg.delete_item("hol_rows", children_only=True)
        country = s["country"]
        state = s["state"] if country == "DE" else ""
        reg = H.COUNTRIES[country]
        note = reg.note_en if self.lang() == "en" else reg.note_de
        dpg.set_value("region_note", note)
        items = [h for h in H.compute_holidays(country, state, int(s["year"])) if h.cat in self.enabled_cats()]
        excl = set(s["excluded"].get(settings.region_key(s), []))
        wds = WD_EN if self.lang() == "en" else WD_DE
        tags = {H.PARTIAL: self.T("cat_tag_partial"), H.OBS: self.T("cat_tag_obs"), H.SUB: self.T("cat_tag_sub")}
        approx = False
        for h in items:
            approx = approx or h.approx
            with dpg.group(horizontal=True, parent="hol_rows"):
                dpg.add_checkbox(default_value=h.de not in excl, user_data=h.de, callback=self.on_hol_toggle)
                label = f"{h.date:%d.%m.} {wds[h.date.weekday()]}  {h.name(self.lang())}"
                if h.cat in tags:
                    label += f"  [{tags[h.cat]}]"
                if h.approx:
                    label += "  (~)"
                col = (140, 140, 140, 255) if h.cat in (H.OBS, H.PARTIAL) else None
                if col:
                    dpg.add_text(label, color=col)
                else:
                    dpg.add_text(label)
        dpg.set_value("approx_note", self.T("approx_warn") if approx else "")

    def on_hol_toggle(self, sender, value, name) -> None:
        key = settings.region_key(self.s)
        lst = set(self.s["excluded"].get(key, []))
        if value:
            lst.discard(name)
        else:
            lst.add(name)
        self.s["excluded"][key] = sorted(lst)
        self.changed()

    def on_custom_add(self) -> None:
        name = dpg.get_value("cu_name").strip()
        if not name:
            return
        d, m, y = dpg.get_value("cu_day"), dpg.get_value("cu_month"), dpg.get_value("cu_year")
        try:
            dt.date(y if y else 2000, m, d)
        except ValueError:
            self.status("Ungültiges Datum / invalid date", True)
            return
        self.s["custom"].append([m, d, y, name])
        dpg.set_value("cu_name", "")
        self.fill_custom_list()
        self.changed()

    def fill_custom_list(self) -> None:
        if not dpg.does_item_exist("custom_rows"):
            return
        dpg.delete_item("custom_rows", children_only=True)
        for i, (m, d, y, name) in enumerate(self.s["custom"]):
            with dpg.group(horizontal=True, parent="custom_rows"):
                dpg.add_button(label=self.T("delete"), user_data=i, callback=self.on_custom_del)
                dpg.add_text(f"{d:02d}.{m:02d}.{y if y else '----'}  {name}")

    def on_custom_del(self, sender, value, idx) -> None:
        if 0 <= idx < len(self.s["custom"]):
            self.s["custom"].pop(idx)
        self.fill_custom_list()
        self.changed()

    # ------------------------------------------------------------------ tab: design
    def build_tab_design(self) -> None:
        T, s = self.T, self.s
        dpg.add_spacer(height=4)
        dpg.add_text(T("ui_theme"))
        dpg.add_combo(THEME_ORDER, tag="cmb_theme", default_value=s["ui_theme"], width=-1,
                      callback=lambda sd, v: self.set_ui_theme(v))
        dpg.add_spacer(height=8)
        dpg.add_text(T("cal_palette"))
        names = [p.name_en if self.lang() == "en" else p.name_de for p in PALETTES]
        cur = palette_by_name(s["cal_palette"])
        dpg.add_combo(names, tag="cmb_palette", default_value=cur.name_en if self.lang() == "en" else cur.name_de,
                      width=-1, callback=self.on_palette)
        dpg.add_drawlist(tag="swatch", width=LEFT_W - 40, height=28)
        self.draw_swatch()
        dpg.add_spacer(height=8)
        dpg.add_text(T("language"))
        dpg.add_radio_button(["Deutsch", "English"], tag="rad_lang", horizontal=True,
                             default_value="English" if self.lang() == "en" else "Deutsch", callback=self.on_lang)

    def on_palette(self, sender, value) -> None:
        self.s["cal_palette"] = palette_by_name(value).name_de
        self.draw_swatch()
        self.changed()

    def draw_swatch(self) -> None:
        if not dpg.does_item_exist("swatch"):
            return
        dpg.delete_item("swatch", children_only=True)
        p = palette_by_name(self.s["cal_palette"])
        cols = [p.bg, p.head, p.cell, p.sat, p.sun, p.hol, p.part, p.title]
        w = (LEFT_W - 40) / len(cols)
        for i, c in enumerate(cols):
            dpg.draw_rectangle((i * w, 0), ((i + 1) * w - 2, 28), fill=hex_rgba(c), color=(120, 120, 120, 200),
                               parent="swatch")

    def on_lang(self, sender, value) -> None:
        self.s["ui_lang"] = "en" if value == "English" else "de"
        settings.save(self.s)
        self.rebuild_ui()

    def rebuild_ui(self) -> None:
        for tag in ("main", "help_win"):
            if dpg.does_item_exist(tag):
                dpg.delete_item(tag)
        self.build_main()
        self.build_help_window()
        dpg.set_primary_window("main", True)
        dpg.set_viewport_title(self.T("app_title"))
        self.fill_holiday_list()
        self.refresh_preview()

    # --------------------------------------------------------------- preview
    def refresh_preview(self) -> None:
        try:
            page = service.make_page(self.s)
            img = render_preview(page, int(self.s.get("preview_px", 1100)))
            rgba = np.asarray(img.convert("RGBA"), dtype=np.float32) / 255.0
            self._set_preview_texture(img.width, img.height, rgba.ravel().tolist())
            info = self.T("row_info").format(page.cell_h)
            if page.cell_h < 3.2:
                info += self.T("row_small")
            if dpg.does_item_exist("row_info"):
                dpg.set_value("row_info", info)
        except Exception as e:
            log_error(e)
            self.status(self.T("status_err").format(e), True)

    def _set_preview_texture(self, w: int, h: int, data: list) -> None:
        old = self.preview_tex
        dpg.delete_item("prev_group", children_only=True)
        if old is not None and dpg.does_item_exist(old):
            dpg.delete_item(old)
        self.preview_tex = dpg.add_dynamic_texture(w, h, data, parent="tex_reg")
        self.preview_size = (w, h)
        self.layout_preview()

    def layout_preview(self) -> None:
        if self.preview_tex is None or not dpg.does_item_exist("prev_group"):
            return
        w, h = self.preview_size
        try:
            avail = dpg.get_item_rect_size("prev_scroll")[0] - 24
        except Exception:
            avail = 900
        if avail < 200:
            avail = 900
        k = avail / w
        dpg.delete_item("prev_group", children_only=True)
        dpg.add_image(self.preview_tex, width=int(w * k), height=int(h * k), parent="prev_group")

    # -------------------------------------------------------------- PDF actions
    def on_generate(self) -> None:
        try:
            path = None
            fn = (self.s.get("filename") or "").strip()
            if fn:
                if not fn.lower().endswith(".pdf"):
                    fn += ".pdf"
                os.makedirs(self.s["out_dir"], exist_ok=True)
                path = os.path.join(self.s["out_dir"], os.path.basename(fn))
            self.last_pdf = service.export_pdf(self.s, path)
            self.status(self.T("status_ok").format(self.last_pdf))
            settings.save(self.s)
        except Exception as e:
            log_error(e)
            self.status(self.T("status_err").format(e), True)

    def _ensure_pdf(self) -> str | None:
        if not self.last_pdf or not os.path.exists(self.last_pdf):
            self.on_generate()
        return self.last_pdf if self.last_pdf and os.path.exists(self.last_pdf) else None

    def on_open(self) -> None:
        path = self._ensure_pdf()
        if path:
            try:
                osutil.open_file(path)
            except Exception as e:
                log_error(e)
                self.status(self.T("status_err").format(e), True)

    def on_print(self) -> None:
        path = self._ensure_pdf()
        if path:
            try:
                res = osutil.print_file(path)
                self.status(self.T("print_sent").format(os.path.basename(path)) if res == "print"
                            else self.T("print_open"))
            except Exception as e:
                log_error(e)
                self.status(self.T("status_err").format(e), True)

    # ------------------------------------------------------------------- Hilfe
    def build_help_window(self) -> None:
        T = self.T
        with dpg.window(tag="help_win", label=T("help_title"), width=1000, height=720, pos=(140, 50), show=False):
            with dpg.group(horizontal=True):
                dpg.add_button(label=T("help_save_btn"), callback=lambda: self.save_handbook())
                dpg.add_button(label=T("close"), callback=lambda: dpg.configure_item("help_win", show=False))
            dpg.add_text("", tag="help_status", color=(90, 170, 90, 255))
            with dpg.group(horizontal=True):
                with dpg.child_window(tag="help_toc", width=250, height=-1):
                    for i, sec in enumerate(SECTIONS):
                        dpg.add_selectable(label=sec["title"], user_data=i, callback=self.on_help_pick,
                                           tag=f"help_sel_{i}", default_value=(i == self.help_idx))
                dpg.add_child_window(tag="help_body", width=-1, height=-1)
        self.show_help_section(self.help_idx)

    def show_help(self) -> None:
        self.show_help_section(self.help_idx)
        dpg.configure_item("help_win", show=True)
        dpg.focus_item("help_win")

    def on_help_pick(self, sender, value, idx) -> None:
        self.show_help_section(idx)

    def _help_texture(self, path: str, max_w: int) -> tuple[int, int, int] | None:
        key = f"{path}|{max_w}|{os.path.getmtime(path)}"
        if key in self.help_tex:
            return self.help_tex[key]
        try:
            with PILImage.open(path) as im:
                im = im.convert("RGBA")
                k = min(1.0, max_w / im.width)
                im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), PILImage.LANCZOS)
            data = (np.asarray(im, dtype=np.float32) / 255.0).ravel().tolist()
            tex = dpg.add_static_texture(im.width, im.height, data, parent="tex_reg")
            self.help_tex[key] = (tex, im.width, im.height)
            return self.help_tex[key]
        except Exception as e:
            log_error(e)
            return None

    def show_help_section(self, idx: int) -> None:
        self.help_idx = idx
        for i in range(len(SECTIONS)):
            tag = f"help_sel_{i}"
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, i == idx)
        if not dpg.does_item_exist("help_body"):
            return
        dpg.delete_item("help_body", children_only=True)
        sec = SECTIONS[idx]
        if not os.path.exists(os.path.join(handbook.SCREENS, "example_a4.png")):
            handbook.ensure_examples()
        dpg.add_text(sec["title"], parent="help_body", color=(110, 160, 230, 255))
        dpg.add_spacer(height=4, parent="help_body")
        for para in sec["paras"]:
            dpg.add_text(para, wrap=660, parent="help_body")
            dpg.add_spacer(height=6, parent="help_body")
        for fn, caption in sec["shots"]:
            path = os.path.join(handbook.SCREENS, fn)
            if os.path.exists(path):
                tex = self._help_texture(path, 660)
                if tex:
                    dpg.add_image(tex[0], width=tex[1], height=tex[2], parent="help_body")
                dpg.add_text(caption, wrap=660, color=(140, 140, 140, 255), parent="help_body")
            else:
                dpg.add_text(f"[{fn}: {self.T('help_shots')}]", wrap=660, color=(140, 140, 140, 255),
                             parent="help_body")
            dpg.add_spacer(height=8, parent="help_body")

    # ------------------------------------------------------- Screenshots / Handbuch
    def take_screenshots(self, on_done=None) -> None:
        """Nimmt die GUI-Screenshots fuers Handbuch automatisch auf (Frame-Buffer)."""
        if self.shot_busy:
            return
        self.shot_busy = True
        os.makedirs(handbook.SCREENS, exist_ok=True)
        self.status(self.T("help_shots"))
        old_theme = self.s["ui_theme"]
        prev_help = dpg.is_item_shown("help_win") if dpg.does_item_exist("help_win") else False
        dpg.configure_item("help_win", show=False)
        seq = [
            (lambda: (self.set_ui_theme("Hell"), self.select_tab("tab_cal")), "gui_01_kalender.png"),
            (lambda: self.select_tab("tab_hol"), "gui_02_feiertage.png"),
            (lambda: self.select_tab("tab_design"), "gui_03_design.png"),
            (lambda: (self.set_ui_theme("Dunkel"), self.select_tab("tab_cal")), "gui_04_dunkel.png"),
        ]
        f = dpg.get_frame_count() + 8
        for action, fname in seq:
            dpg.set_frame_callback(f, lambda s, a, u: u[0](), user_data=(action,))
            path = os.path.join(handbook.SCREENS, fname)
            dpg.set_frame_callback(f + 8, lambda s, a, u: dpg.output_frame_buffer(file=u), user_data=path)
            f += 18

        def finish(s, a, u):
            try:
                self.set_ui_theme(old_theme)
                self.select_tab("tab_cal")
                self.help_tex.clear()
                if prev_help:
                    dpg.configure_item("help_win", show=True)
                self.show_help_section(self.help_idx)
            finally:
                self.shot_busy = False
                self.status(self.T("help_screens") + ": OK")
                if on_done:
                    on_done()

        dpg.set_frame_callback(f + 6, finish)

    def save_handbook(self) -> None:
        def build():
            try:
                os.makedirs(handbook.DOCS, exist_ok=True)
                path = handbook.build_handbook(os.path.join(handbook.DOCS, "Handbuch_KalenderGen.pdf"))
                msg = self.T("help_saved").format(path)
                self.status(msg)
                if dpg.does_item_exist("help_status"):
                    dpg.set_value("help_status", msg)
                self.last_manual = path
            except Exception as e:
                log_error(e)
                self.status(self.T("status_err").format(e), True)

        if handbook.missing_gui_shots():
            self.take_screenshots(on_done=build)
        else:
            build()


def run() -> None:
    App().run()
