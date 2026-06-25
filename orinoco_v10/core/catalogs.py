"""
catalogs.py — Valores predefinidos para selects (evita errores de tipeo).
"""

# Combustibles estándar en estaciones fluviales / PDV Venezuela
TIPOS_COMBUSTIBLE = (
    "Gasoil",
    "Gasolina 91",
    "Gasolina 95",
)

# Opción del select para registrar un tipo fuera del catálogo estándar
TIPO_COMBUSTIBLE_OTRO = "— Otro (especificar nombre) —"

METODOS_PAGO = (
    "Biopago",
    "Transferencia",
    "Efectivo Bs",
    "Efectivo USD",
)

ROLES_OPERADOR = (
    ("Operador", "operador"),
    ("Administrador", "administrador"),
)

MONEDAS = (
    "Bs",
    "USD",
)

MOTIVOS_REABASTECIMIENTO = (
    "Reabastecimiento",
    "Compra a proveedor",
    "Recepción de carga",
)

MOTIVOS_AJUSTE = (
    "Ajuste manual",
    "Corrección de inventario",
    "Pérdida / merma",
)

ROLE_LABEL_BY_VALUE = {v: lbl for lbl, v in ROLES_OPERADOR}
ROLE_VALUE_BY_LABEL = {lbl: v for lbl, v in ROLES_OPERADOR}
