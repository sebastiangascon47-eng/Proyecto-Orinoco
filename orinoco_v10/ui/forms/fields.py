"""Campos reutilizables para modales (cortos) y vistas de formulario (amplios)."""
from __future__ import annotations
import customtkinter as ctk
from core.theme import C, FONT_LABEL
from ui.components.widgets import field, dropdown

_PHONE_CHARS = frozenset("0123456789+-() ")

CEDULA_MIN_LEN = 6
CEDULA_MAX_LEN = 8
PHONE_MAX_LEN = 15
PHONE_MIN_DIGITS = 10
PHONE_MAX_DIGITS = 11


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


def _digits_ok(proposed: str, max_len: int = CEDULA_MAX_LEN) -> bool:
    if len(proposed) > max_len:
        return False
    return proposed == "" or proposed.isdigit()


def _phone_ok(proposed: str, max_len: int = PHONE_MAX_LEN) -> bool:
    if len(proposed) > max_len:
        return False
    return proposed == "" or all(ch in _PHONE_CHARS for ch in proposed)


def validate_cedula(value: str, *, required: bool = True) -> str | None:
    ced = value.strip()
    if not ced:
        return "La cédula es obligatoria." if required else None
    if not ced.isdigit():
        return "La cédula solo debe contener números."
    if len(ced) < CEDULA_MIN_LEN or len(ced) > CEDULA_MAX_LEN:
        return f"La cédula debe tener entre {CEDULA_MIN_LEN} y {CEDULA_MAX_LEN} dígitos."
    return None


def validate_phone(value: str) -> str | None:
    tel = value.strip()
    if not tel:
        return None
    if len(tel) > PHONE_MAX_LEN:
        return f"El teléfono no puede superar {PHONE_MAX_LEN} caracteres."
    if any(ch.isalpha() for ch in tel):
        return "El teléfono no debe contener letras."
    if not all(ch in _PHONE_CHARS for ch in tel):
        return "El teléfono solo admite números y los símbolos + - ( )."
    digits = "".join(ch for ch in tel if ch.isdigit())
    if len(digits) < PHONE_MIN_DIGITS or len(digits) > PHONE_MAX_DIGITS:
        return (f"El teléfono debe tener entre {PHONE_MIN_DIGITS} y "
                f"{PHONE_MAX_DIGITS} dígitos.")
    return None


def entry(parent, value="", show="", ph="", width=410, height=40,
          numeric=False, decimal=True, digits_only=False, phone=False,
          max_length: int | None = None):
    e = field(parent, width=width, height=height, show=show, placeholder=ph)
    if digits_only:
        lim = max_length or CEDULA_MAX_LEN
        reg = parent.register(lambda p, m=lim: _digits_ok(p, m))
        e.configure(validate="key", validatecommand=(reg, "%P"))
    elif phone:
        lim = max_length or PHONE_MAX_LEN
        reg = parent.register(lambda p, m=lim: _phone_ok(p, m))
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
                numeric=False, decimal=True, digits_only=False, phone=False,
                max_length: int | None = None):
    lbl(parent, label)
    return entry(parent, value=value, show=show, width=width, ph=ph,
                 numeric=numeric, decimal=decimal, digits_only=digits_only,
                 phone=phone, max_length=max_length)


def label_combo(parent, label, values, value=None, state="normal", width=410,
                readonly=False):
    lbl(parent, label)
    return combo(parent, values, value=value, state=state, width=width, readonly=readonly)
