"""Constantes de reglas de negocio (sin textos de ayuda en UI)."""

# Métodos de pago que no exigen número de referencia manual
METODOS_SIN_REFERENCIA = frozenset({"Efectivo Bs", "Efectivo USD"})


def referencia_efectivo(metodo: str, despacho_id: int) -> str:
    """Genera referencia única para cobros en efectivo."""
    if metodo == "Efectivo USD":
        return f"EF-USD-{despacho_id:06d}"
    return f"EF-{despacho_id:06d}"


_AUTOGEN_MARCADORES = frozenset({
    "—", "Efectivo", "Se genera al registrar", "Se asigna al registrar el despacho",
})


def resolver_referencia_pago(metodo: str, referencia: str, despacho_id: int) -> str:
    """Valida o autogenera la referencia según el método de pago."""
    ref = (referencia or "").strip()
    if metodo in METODOS_SIN_REFERENCIA:
        return referencia_efectivo(metodo, despacho_id)
    if not ref or ref in _AUTOGEN_MARCADORES:
        raise ValueError(
            "Indique el número de referencia (transferencia, Biopago, etc.)."
        )
    return ref
