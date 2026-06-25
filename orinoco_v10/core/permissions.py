"""Permisos por rol — Administrador vs Operador."""

from __future__ import annotations

ROL_ADMIN = "administrador"
ROL_OPERADOR = "operador"

# Módulos visibles solo para administrador
ADMIN_MODULES = frozenset({"operadores", "configuracion", "bitacora"})


def is_admin(user: dict) -> bool:
    return user.get("rol") == ROL_ADMIN


def can_access_module(user: dict, module_key: str) -> bool:
    if module_key in ADMIN_MODULES:
        return is_admin(user)
    return True


def can_register(user: dict) -> bool:
    """Registrar nuevos registros operativos (despachos, pagos, beneficiarios, etc.)."""
    return True


def can_view(user: dict) -> bool:
    return True


def can_edit(user: dict) -> bool:
    """Editar registros existentes — solo administrador."""
    return is_admin(user)


def can_delete(user: dict) -> bool:
    """Anular, dar de baja o eliminar — solo administrador."""
    return is_admin(user)


def can_manage_operators(user: dict) -> bool:
    return is_admin(user)


def can_report(user: dict) -> bool:
    """Generar y exportar reportes — ambos roles."""
    return True


def can_adjust_inventory(user: dict) -> bool:
    """Ajustes manuales de inventario — solo administrador."""
    return is_admin(user)


def can_manage_fuel_types(user: dict) -> bool:
    """Crear, editar o eliminar tipos de combustible — solo administrador."""
    return is_admin(user)


def can_restock(user: dict) -> bool:
    """Reabastecer inventario — operación diaria permitida al operador."""
    return True
