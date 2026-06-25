"""Campos reutilizables para modales (cortos) y vistas de formulario (amplios)."""
from __future__ import annotations
import customtkinter as ctk
from core.theme import C, FONT_LABEL
from ui.components.widgets import field, dropdown


def lbl(parent, text):
    ctk.CTkLabel(parent, text=text.upper(), font=(FONT_LABEL[0], 9, "bold"),
                 text_color=C["text3"]).pack(anchor="w", pady=(12, 3))


def _numeric_ok(proposed: str, decimal: bool = True) -> bool:
    if proposed == "":
        return True
    allowed = "0123456789"
    if decimal:
        allowed += ".,"
    if any(ch not in allowed for ch in proposed):
        return False
    sep = proposed.replace(",", ".").count(".")
    return sep <= 1


def entry(parent, value="", show="", ph="", width=410, height=40,
          numeric=False, decimal=True):
    e = field(parent, width=width, height=height, show=show, placeholder=ph)
    if numeric:
        reg = parent.register(lambda p: _numeric_ok(p, decimal))
        e.configure(validate="key", validatecommand=(reg, "%P"))
    if value not in ("", None):
        e.insert(0, str(value))
    e.pack(fill="x")
    return e


def combo(parent, values, value=None, state="normal", width=410, readonly=False):
    st = "readonly" if readonly else state
    d = dropdown(parent, values, width=width, state=st)
    if value is not None and value in values:
        d.set(value)
    elif values:
        d.set(values[0])
    d.pack(fill="x")
    return d


def label_entry(parent, label, value="", show="", width=410, ph="",
                numeric=False, decimal=True):
    lbl(parent, label)
    return entry(parent, value=value, show=show, width=width, ph=ph,
                 numeric=numeric, decimal=decimal)


def label_combo(parent, label, values, value=None, state="normal", width=410,
                readonly=False):
    lbl(parent, label)
    return combo(parent, values, value=value, state=state, width=width, readonly=readonly)
