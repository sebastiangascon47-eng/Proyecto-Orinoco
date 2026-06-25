"""Verificación integral de módulos críticos (sin UI visual)."""
from __future__ import annotations
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FAILURES: list[str] = []


def ok(msg: str):
    print(f"  OK  {msg}")


def fail(msg: str):
    print(f"  FAIL {msg}")
    FAILURES.append(msg)


def section(title: str):
    print(f"\n=== {title} ===")


def main() -> int:
    section("Imports")
    try:
        from core.database import DB
        from core import permissions as perm
        from ui.views import VIEW_MAP
        from ui.forms.despacho import DespachoFormPage
        from ui.modals.forms import (
            TipoCombustibleModal, DespachoEditModal, PagoModal,
            SeleccionDespachoPagoModal, ReabastecerModal, AjusteModal,
        )
        from ui.forms import fields as F
        ok(f"Vistas registradas: {', '.join(sorted(VIEW_MAP))}")
    except Exception as e:
        fail(f"Imports: {e}")
        traceback.print_exc()
        return 1

    section("Base de datos")
    db = DB()
    admin = db.auth("admin", "admin123")
    oper = db.auth("operador", "operador123")
    if admin:
        ok("Login admin")
    else:
        fail("Login admin")
    if oper:
        ok("Login operador")
    else:
        fail("Login operador")

    inv = db.get_inventario(solo_activos=True)
    bens = db.get_beneficiarios(solo_activos=True)
    if inv and bens:
        ok(f"Inventario ({len(inv)}) y beneficiarios ({len(bens)})")
    else:
        fail("Sin inventario o beneficiarios activos")

    pend = db.get_despachos_pendientes()
    ok(f"Despachos pendientes: {len(pend)}")

    todos = db.get_despachos(limit=50, incluir_anulados=True)
    activos = db.get_despachos(limit=50, incluir_anulados=False)
    anulados = [d for d in todos if d["estado"] == "anulado"]
    ok(f"Despachos activos={len(activos)} total_con_anulados={len(todos)} anulados={len(anulados)}")

    pagos = db.get_pagos(limit=20, incluir_anulados=True)
    pagos_act = db.get_pagos(limit=20, incluir_anulados=False)
    ok(f"Pagos activos={len(pagos_act)} total_con_anulados={len(pagos)}")

    section("Permisos")
    u_admin = {"rol": "administrador", "nombre": "Admin"}
    u_op = {"rol": "operador", "nombre": "Op"}
    if perm.can_edit_despacho(u_op) and perm.can_delete(u_admin) and not perm.can_delete(u_op):
        ok("Permisos despacho/anular por rol")
    else:
        fail("Permisos inconsistentes")
    if perm.can_restock(u_op) and perm.can_adjust_inventory(u_admin) and not perm.can_adjust_inventory(u_op):
        ok("Reabastecer (operador) vs corregir (admin)")
    else:
        fail("Permisos inventario inconsistentes")

    section("Edición despacho pendiente")
    editable = next(
        (d for d in pend if d["estado"] == "registrado" and not d["pagado"]), None
    )
    if editable:
        eid = editable["id"]
        lit_orig = float(editable["litros"])
        mon_orig = float(editable["monto_bs"])
        try:
            db.update_despacho_pendiente(
                eid, lit_orig, mon_orig, "test verificación", "Sistema"
            )
            ok(f"update_despacho_pendiente #{eid}")
        except Exception as e:
            fail(f"update_despacho_pendiente: {e}")
    else:
        ok("Sin despacho editable para probar (omitido)")

    section("Validación numérica")
    if F._numeric_ok("123.45") and F._numeric_ok("1000") and not F._numeric_ok("abc"):
        ok("Filtro numérico en campos")
    else:
        fail("Filtro numérico")

    section("UI — instanciación mínima (sin mostrar)")
    try:
        import customtkinter as ctk
        root = ctk.CTk()
        root.withdraw()

        user = dict(db.auth("admin", "admin123"))
        host = ctk.CTkFrame(root)

        closed = {"n": 0}

        def on_done():
            closed["n"] += 1

        # Formulario despacho: debe tener hijos en _body tras init
        form = DespachoFormPage(
            host, db=db, user=user, app=None,
            on_done=on_done, on_cancel=lambda: None,
        )
        form.pack()
        root.update_idletasks()
        body_children = form._body.winfo_children() if hasattr(form, "_body") else []
        step_children = form._step_bar.winfo_children() if hasattr(form, "_step_bar") else []
        if body_children and step_children:
            ok(f"DespachoFormPage: {len(step_children)} pasos, {len(body_children)} widgets en cuerpo")
        else:
            fail(f"DespachoFormPage vacío (pasos={len(step_children)}, cuerpo={len(body_children)})")

        # Vista Pagos: estructura grid + scroll
        from ui.views.pagos import PagosView
        pv = PagosView(host, db, user, app=None)
        pv.pack()
        root.update_idletasks()
        if hasattr(pv, "_pend") and hasattr(pv, "_done"):
            pv._refresh()
            ok(f"PagosView: pendientes={len(pv._pend._all_rows)} pagos={len(pv._done._all_rows)}")
        else:
            fail("PagosView sin tablas")

        from ui.views.despacho import DespachoView
        dv = DespachoView(host, db, user, app=None)
        dv.pack()
        root.update_idletasks()
        dv._refresh()
        estados = {r["estado"] for r in dv._ptbl._all_rows}
        ok(f"DespachoView: {len(dv._ptbl._all_rows)} filas, estados={estados}")

        from ui.views.inventario import InventarioView
        iv = InventarioView(host, db, user, app=None)
        iv.pack()
        root.update_idletasks()
        iv._refresh()
        ok(f"InventarioView: {len(iv._ptbl._all_rows)} tipos combustible")

        # Comprobar lógica de anulación sin modificar datos
        if not db.anular_despacho(-1, "test", "Sistema"):
            ok("anular_despacho rechaza ID inválido")
        else:
            fail("anular_despacho aceptó ID inválido")

        root.destroy()
    except Exception as e:
        fail(f"UI smoke test: {e}")
        traceback.print_exc()

    section("Resultado")
    if FAILURES:
        print(f"\n{len(FAILURES)} fallo(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nTodas las verificaciones pasaron.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
