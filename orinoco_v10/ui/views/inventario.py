"""Vista: Inventario."""
from __future__ import annotations
from core import permissions as perm
from core.theme import ROWS_PER_PAGE, ROWS_PER_PAGE_COMPACT
from ui import modals
from ui.views.base import BaseView
from ui.views.utils import movimiento_label, movimiento_tipo


class InventarioView(BaseView):
    def _build(self):
        self.page_title("Inventario")
        bar = self.page_toolbar()
        if perm.can_manage_fuel_types(self.user):
            self.toolbar_btn(bar.right, "Nuevo tipo", command=self._nuevo,
                             width=148).pack(side="right")
        panel = self.page_list_panel(expand=False)
        self._ptbl = self.page_paginated_table(panel, [
            ("tipo", "Tipo", 160), ("litros", "Disponible", 130),
            ("capacidad", "Capacidad", 130), ("minimo", "Mínimo alerta", 130),
            ("estado", "Estado", 120),
        ], page_size=ROWS_PER_PAGE_COMPACT, row_actions=self._row_actions, expand=False)
        self.section_title("Últimos movimientos (kardex)")
        mov_panel = self.page_list_panel()
        self._mov = self.page_paginated_table(mov_panel, [
            ("fecha", "Fecha", 130), ("tipo", "Tipo", 130), ("mov", "Movimiento", 110),
            ("litros", "Litros", 110), ("motivo", "Motivo", 200), ("operador", "Operador", 120),
        ], page_size=ROWS_PER_PAGE_COMPACT)

    def _refresh(self):
        self._ptbl.load([{
            "tipo": r["tipo"], "litros": f"{r['litros_actual']:,.0f} L",
            "capacidad": f"{r['capacidad']:,.0f} L", "minimo": f"{r['minimo_alerta']:,.0f} L",
            "estado": ("Activo" if r["activo"] else "Inactivo") +
                      (" · Bajo" if r["activo"] and r["litros_actual"] <= r["minimo_alerta"] else ""),
            "_raw": r,
        } for r in self.db.get_inventario()])
        self._mov.load([{
            "fecha": m["fecha"][:16], "tipo": m["tipo"],
            "mov": movimiento_tipo(m["tipo_movimiento"]),
            "litros": movimiento_label(m["tipo_movimiento"], m["litros"]),
            "motivo": m["motivo"] or "—",
            "operador": m["operador"] or "—",
        } for m in self.db.get_movimientos(limit=500)])

    def _row_actions(self, row, _idx):
        r = row["_raw"]
        items = [("Ver", lambda: self._ver(r), False)]
        if perm.can_adjust_inventory(self.user):
            items.append(("Corregir inventario", lambda: modals.AjusteModal(
                self.app, self.db, self.user, self._refresh, dict(r)), False))
        elif perm.can_restock(self.user):
            items.append(("Reabastecer", lambda: modals.ReabastecerModal(
                self.app, self.db, self.user, self._refresh, dict(r)), False))
        if perm.can_manage_fuel_types(self.user):
            items.append(("Editar", lambda: modals.TipoCombustibleModal(
                self.app, self.db, self.user, self._refresh, dict(r)), False))
            items.append(("Eliminar", lambda: self._eliminar(r), True))
        return items

    def _nuevo(self):
        modals.TipoCombustibleModal(self.app, self.db, self.user, self._refresh)

    def _ver(self, r):
        fields = [
            ("Tipo", r["tipo"]), ("Disponible", f"{r['litros_actual']:,.0f} L"),
            ("Capacidad", f"{r['capacidad']:,.0f} L"),
            ("Mínimo de alerta", f"{r['minimo_alerta']:,.0f} L"),
            ("Estado", "Activo" if r["activo"] else "Inactivo"),
            ("Actualizado", (r["actualizado_en"] or "")[:16]),
        ]
        modals.DetailModal(self.app, "Ver combustible", fields, [])

    def _eliminar(self, r):
        modals.ConfirmModal(
            self.app, "Eliminar tipo de combustible",
            f"¿Eliminar “{r['tipo']}”? Solo es posible si no tiene despachos asociados.",
            confirm_text="Eliminar", variant="danger",
            on_confirm=lambda _: self._do_eliminar(r))

    def _do_eliminar(self, r):
        if self.db.delete_tipo_combustible(r["id"]):
            self.db.log(self.user["id"], self.user["nombre"], "Inventario",
                        "Eliminar tipo", r["tipo"])
            self._refresh()
            self.app.toast("Tipo de combustible eliminado")
        else:
            self.app.toast("No se puede eliminar: tiene despachos asociados", "error")
