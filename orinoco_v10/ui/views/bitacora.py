"""Vista: Bitácora (admin)."""
from __future__ import annotations
from core.theme import ROWS_PER_PAGE
from ui.views.base import BaseView


class BitacoraView(BaseView):
    def _build(self):
        if not self._require_admin():
            return
        self.page_title("Bitácora de actividad")
        panel = self.page_list_panel()
        self._ptbl = self.page_paginated_table(panel, [
            ("fecha", "Fecha", 150), ("operador", "Operador", 150),
            ("modulo", "Módulo", 140), ("accion", "Acción", 150),
            ("detalle", "Detalle", 260),
        ], page_size=ROWS_PER_PAGE)

    def _refresh(self):
        self._ptbl.load([{
            "fecha": b["fecha"][:19], "operador": b["operador"] or "—",
            "modulo": b["modulo"] or "—", "accion": b["accion"] or "—",
            "detalle": b["detalle"] or "—",
        } for b in self.db.get_bitacora(limit=2000)])
