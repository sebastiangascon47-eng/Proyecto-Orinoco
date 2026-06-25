"""Campos reutilizables para modales (cortos) y vistas de formulario (amplios)."""
from __future__ import annotations
import customtkinter as ctk
from core.theme import C, FONT_LABEL
from ui.components.widgets import field, dropdown


def lbl(parent, text):
    ctk.CTkLabel(parent, text=text.upper(), font=(FONT_LABEL[0], 9, "bold"),
                 text_color=C["text3"]).pack(anchor="w", pady=(12, 3))


def entry(parent, value="", show="", ph="", width=410, height=40):
    e = field(parent, width=width, height=height, show=show, placeholder=ph)
    if value not in ("", None):
        e.insert(0, str(value))
    e.pack(fill="x")
    return e


def combo(parent, values, value=None, state="normal", width=410):
    d = dropdown(parent, values, width=width, state=state)
    if value is not None and value in values:
        d.set(value)
    elif values:
        d.set(values[0])
    d.pack(fill="x")
    return d


def label_entry(parent, label, value="", show="", width=410, ph=""):
    lbl(parent, label)
    return entry(parent, value=value, show=show, width=width, ph=ph)


def label_combo(parent, label, values, value=None, state="normal", width=410):
    lbl(parent, label)
    return combo(parent, values, value=value, state=state, width=width)
