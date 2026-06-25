"""Vista: Pagos — cobros pendientes y registrados."""
from __future__ import annotations
from core.theme import M, ROWS_PER_PAGE_COMPACT
from ui import modals
from ui.views.base import BaseView
from ui.views.utils import pago_estado


class PagosView(BaseView):
    def _build(self):
        self.page_title("Control de pagos")
        self._cards = self.page_metrics([
            ("Monto por cobrar", "0 Bs", M[0]),
            ("Cobrado hoy", "0 Bs", M[2]),
        ])
        self.section_title("Despachos pendientes de pago")
        pend = self.page_list_panel(expand=False)
        self._pend = self.page_paginated_table(pend, [
            ("id", "#", 40), ("fecha", "Fecha", 120), ("cedula", "Cédula", 100),
            ("beneficiario", "Beneficiario", 180), ("litros", "Litros", 90),
            ("monto", "Monto Bs", 110),
        ], page_size=ROWS_PER_PAGE_COMPACT, row_actions=self._pend_actions, expand=False)
        self.section_title("Pagos registrados")
        done = self.page_list_panel()
        self._done = self.page_paginated_table(done, [
            ("id", "#", 40), ("fecha", "Fecha", 120), ("beneficiario", "Beneficiario", 180),
            ("monto", "Monto Bs", 110), ("referencia", "Referencia", 130),
            ("metodo", "Método", 110), ("estado", "Estado", 100),
        ], page_size=ROWS_PER_PAGE_COMPACT, row_actions=self._done_actions)

    def _refresh(self):
        sc = self.db.stats_cobros()
        self._cards.update("Monto por cobrar", f"{sc['monto_pendiente']:,.2f} Bs")
        self._cards.update("Cobrado hoy", f"{sc['cobrado_hoy']:,.2f} Bs")
        self._pend.load([{
            "id": r["id"], "fecha": r["fecha"][:16], "cedula": r["cedula"],
            "beneficiario": r["beneficiario"], "litros": f"{r['litros']:,.0f} L",
            "monto": f"{r['monto_bs']:,.2f}", "_raw": r,
        } for r in self.db.get_despachos_pendientes()])
        self._done.load([{
            "id": p["id"], "fecha": p["fecha"][:16], "beneficiario": p["beneficiario"],
            "monto": f"{p['monto_bs']:,.2f}", "referencia": p["referencia"] or "—",
            "metodo": p["metodo"],
            "estado": pago_estado(p), "_raw": p,
        } for p in self.db.get_pagos(limit=500)])

    def _pend_actions(self, row, _idx):
        r = row["_raw"]
        return [("Registrar pago", lambda: modals.PagoModal(
            self.app, self.db, self.user, self._on_change, dict(r)), False)]

    def _on_change(self):
        self._refresh()
        if self.app and hasattr(self.app, "notify_data_changed"):
            self.app.notify_data_changed()

    def _done_actions(self, row, _idx):
        p = row["_raw"]
        items = [("Ver", lambda: self._ver(p), False)]
        if self.can_delete and p["estado"] != "anulado":
            items.append(("Anular", lambda: self._anular(p), True))
        return items

    def _ver(self, p):
        estado = pago_estado(p)
        fields = [
            ("Pago", f"#{p['id']}"), ("Despacho", f"#{p['despacho_id']}"),
            ("Beneficiario", f"{p['beneficiario']} ({p['cedula']})"),
            ("Monto", f"{p['monto_bs']:,.2f} Bs"), ("Referencia", p["referencia"] or "—"),
            ("Método", p["metodo"]), ("Estado", estado),
            ("Fecha", p["fecha"][:16]), ("Operador", p["operador"]),
        ]
        if p["estado"] == "anulado":
            fields.append(("Motivo de anulación", p["motivo_anulacion"] or "—"))
        modals.DetailModal(self.app, "Ver pago", fields, [])

    def _anular(self, p):
        modals.ConfirmModal(
            self.app, "Anular pago",
            f"¿Anular el pago #{p['id']}? El despacho asociado volverá a quedar pendiente.",
            need_reason=True, confirm_text="Anular", variant="danger",
            on_confirm=lambda motivo: self._do_anular(p, motivo))

    def _do_anular(self, p, motivo):
        self.db.anular_pago(p["id"], motivo, self.user["nombre"])
        self.db.log(self.user["id"], self.user["nombre"], "Pagos",
                    "Anular", f"#{p['id']} — {motivo}")
        self._refresh()
        self.app.toast("Pago anulado")
