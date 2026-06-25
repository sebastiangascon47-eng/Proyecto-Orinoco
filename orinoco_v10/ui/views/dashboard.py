"""Vista: Panel de control (inicio) — operación del día."""
from __future__ import annotations
from datetime import date

from core.theme import M, ROWS_PER_PAGE
from ui import modals
from ui.views.base import BaseView
from ui.views.utils import despacho_estado


class DashboardView(BaseView):
    def _build(self):
        self.page_title("Inicio", "Operación de hoy",
                        actions=[("Actualizar", "secondary", self._force_refresh)])
        self._cards = self.page_metrics([
            ("Inventario disponible", "0 L", M[0], self._go_inventario),
            ("Despachos hoy", "0", M[1], self._go_despacho),
            ("Litros despachados hoy", "0 L", M[2], None),
            ("Pagos pendientes", "0", M[3], self._go_pagos),
        ])
        self.section_title("Despachos de hoy")
        panel = self.page_list_panel()
        self._ptbl = self.page_paginated_table(panel, [
            ("id", "#", 40), ("fecha", "Fecha", 130), ("beneficiario", "Beneficiario", 180),
            ("litros", "Litros", 90), ("tipo", "Tipo", 110), ("estado", "Estado", 110),
        ], page_size=ROWS_PER_PAGE, row_actions=self._row_actions)

    def _go_inventario(self):
        if self.navigate:
            self.navigate("inventario")

    def _go_despacho(self):
        if self.navigate:
            self.navigate("despacho")

    def _go_pagos(self):
        if self.navigate:
            self.navigate("pagos")

    def _row_actions(self, row, _idx):
        r = row["_raw"]
        return [("Ver", lambda: self._ver(r), False)]

    def _ver(self, r):
        fields = [
            ("Despacho", f"#{r['id']}"), ("Fecha", r["fecha"][:16]),
            ("Beneficiario", f"{r['beneficiario']} ({r['cedula']})"),
            ("Combustible", r["tipo"]), ("Litros", f"{r['litros']:,.0f} L"),
            ("Estado", despacho_estado(r)), ("Operador", r["operador"]),
        ]
        modals.DetailModal(self.app, "Ver despacho", fields, [])

    def _force_refresh(self):
        self._refresh()

    def _refresh(self):
        s = self.db.stats()
        self._cards.update("Inventario disponible", f"{s['stock']:,.0f} L")
        self._cards.update("Despachos hoy", str(s["despachos_hoy"]))
        self._cards.update("Litros despachados hoy", f"{s['litros_hoy']:,.0f} L")
        self._cards.update("Pagos pendientes", str(s["pendientes"]))
        hoy = str(date.today())
        rows = self.db.get_despachos(limit=500, desde=hoy, hasta=hoy, incluir_anulados=False)
        self._ptbl.load([self._fmt(r) for r in rows])

    @staticmethod
    def _fmt(r):
        return {
            "id": r["id"], "fecha": r["fecha"][:16],
            "beneficiario": r["beneficiario"], "litros": f"{r['litros']:,.0f} L",
            "tipo": r["tipo"], "estado": despacho_estado(r), "_raw": r,
        }
