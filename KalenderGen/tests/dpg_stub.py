"""Minimaler Stub der Dear-PyGui-API, um die GUI-Logik ohne dearpygui auszufuehren.

Prueft Aufbau, Callbacks und Datenfluss - NICHT die Gueltigkeit der echten dpg-Aufrufe.
"""
import itertools
import sys
import types

CONTEXTS = {"window", "menu_bar", "menu", "group", "child_window", "tab_bar", "tab", "collapsing_header",
            "file_dialog", "theme", "theme_component", "font_registry", "drawlist", "table", "texture_registry",
            "viewport_menu_bar", "popup", "tooltip", "handler_registry", "item_handler_registry"}


class _Ctx:
    def __init__(self, stub, tag):
        self.stub, self.tag = stub, tag

    def __enter__(self):
        return self.tag

    def __exit__(self, *a):
        return False


class Stub(types.ModuleType):
    def __init__(self):
        super().__init__("dearpygui.dearpygui")
        self._ids = itertools.count(100)
        self.items = {}          # tag -> kwargs
        self.values = {}
        self.calls = []
        self.frame_callbacks = {}
        self.frame = 0
        self.fb_files = []

    def _reg(self, kind, args, kw):
        tag = kw.get("tag") or next(self._ids)
        self.items[tag] = dict(kind=kind, args=args, **kw)
        if "default_value" in kw:
            self.values[tag] = kw["default_value"]
        if kind == "add_dynamic_texture" or kind == "add_static_texture":
            w, h, data = args[0], args[1], args[2]
            assert len(data) == w * h * 4, (len(data), w, h)
        return tag

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        if name.startswith("mv"):
            return abs(hash(name)) % 100000
        if name in CONTEXTS:
            return lambda *a, **k: _Ctx(self, self._reg(name, a, k))

        def fn(*a, **k):
            self.calls.append((name, a, k))
            if name.startswith("add_") or name.startswith("draw_"):
                return self._reg(name, a, k)
            return None
        return fn

    # echte Logik fuer ein paar Funktionen
    def get_value(self, tag):
        return self.values.get(tag)

    def set_value(self, tag, v):
        self.values[tag] = v

    def does_item_exist(self, tag):
        return tag in self.items

    def delete_item(self, tag, children_only=False):
        if not children_only:
            self.items.pop(tag, None)

    def get_item_rect_size(self, tag):
        return [900, 600]

    def get_frame_count(self):
        return self.frame

    def get_alias_id(self, tag):
        return tag

    def is_item_shown(self, tag):
        return False

    def set_frame_callback(self, frame, callback, user_data=None):
        self.frame_callbacks[frame] = (callback, user_data)

    def output_frame_buffer(self, file=None, **k):
        self.fb_files.append(file)
        from PIL import Image
        Image.new("RGB", (800, 500), "gray").save(file)

    def is_dearpygui_running(self):
        return False

    def add_font(self, *a, **k):
        return self._reg("add_font", a, k)

    def run_frame_callbacks(self):
        for f in sorted(self.frame_callbacks):
            cb, ud = self.frame_callbacks[f]
            self.frame = f
            cb(None, None, ud)
        self.frame_callbacks.clear()


def install():
    stub = Stub()
    pkg = types.ModuleType("dearpygui")
    pkg.dearpygui = stub
    sys.modules["dearpygui"] = pkg
    sys.modules["dearpygui.dearpygui"] = stub
    return stub
