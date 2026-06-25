"""Utilidades compartidas entre vistas."""

from __future__ import annotations

from core.theme import C





def money(v) -> str:

    try:

        return f"{float(v):,.2f}"

    except Exception:

        return str(v)





def stock_color(litros, minimo=2000) -> str:

    if litros <= minimo:

        return C["red"]

    if litros <= minimo * 2:

        return C["warning"]

    return C["neutral"]





def despacho_estado(r) -> str:

    if r["estado"] == "anulado":

        return "Anulado"

    if r["pagado"]:

        return "Pagado"

    return "Pendiente"





def pago_estado(r) -> str:
    if r["estado"] == "anulado":
        return "Anulado"
    return "Registrado"





def movimiento_label(tipo: str, litros: float) -> str:

    t = (tipo or "").lower()

    if t == "entrada":

        return f"+{litros:,.0f} L"

    if t == "salida":

        return f"−{litros:,.0f} L"

    if t == "ajuste":

        sign = "+" if litros >= 0 else "−"

        return f"{sign}{abs(litros):,.0f} L"

    return f"{litros:,.0f} L"





def movimiento_tipo(tipo: str) -> str:

    return {

        "entrada": "Entrada",

        "salida": "Salida",

        "ajuste": "Ajuste",

    }.get((tipo or "").lower(), tipo.capitalize() if tipo else "—")

