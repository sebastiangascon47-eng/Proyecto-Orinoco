"""Campos reutilizables para modales (cortos) y vistas de formulario (amplios)."""
from __future__ import annotations
import customtkinter as ctk
from core.theme import C, FONT_LABEL
from ui.components.widgets import field, dropdown

_PHONE_CHARS = frozenset("0123456789+-() ")


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


def _digits_ok(proposed: str) -> bool:
    return proposed == "" or proposed.isdigit()


def _phone_ok(proposed: str) -> bool:
    return proposed == "" or all(ch in _PHONE_CHARS for ch in proposed)


def validate_cedula(value: str) -> str | None:
    ced = value.strip()
    if not ced:
        return "La cédula es obligatoria."
    if not ced.isdigit():
        return "La cédula solo debe contener números."
    return None


def validate_phone(value: str) -> str | None:
    tel = value.strip()
    if not tel:
        return None
    if any(ch.isalpha() for ch in tel):
        return "El teléfono no debe contener letras."
    if not all(ch in _PHONE_CHARS for ch in tel):
        return "El teléfono solo admite números y los símbolos + - ( )."
    return None


def entry(parent, value="", show="", ph="", width=410, height=40,
          numeric=False, decimal=True, digits_only=False, phone=False):
    e = field(parent, width=width, height=height, show=show, placeholder=ph)
    if digits_only:
        reg = parent.register(_digits_ok)
        e.configure(validate="key", validatecommand=(reg, "%P"))
    elif phone:
        reg = parent.register(_phone_ok)
        e.configure(validate="key", validatecommand=(reg, "%P"))
    elif numeric:
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
                numeric=False, decimal=True, digits_only=False, phone=False):
    lbl(parent, label)
    return entry(parent, value=value, show=show, width=width, ph=ph,
                 numeric=numeric, decimal=decimal, digits_only=digits_only, phone=phone)


def label_combo(parent, label, values, value=None, state="normal", width=410,
                readonly=False):
    lbl(parent, label)
    return combo(parent, values, value=value, state=state, width=width, readonly=readonly)
