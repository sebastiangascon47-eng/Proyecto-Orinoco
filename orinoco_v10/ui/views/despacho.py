"""Vista: Despachos."""
from __future__ import annotations
from core.theme import ROWS_PER_PAGE
from ui import forms
from ui import modals
from ui.views.base import BaseView, ListFormMixin
from ui.views.utils import despacho_estado


class DespachoView(ListFormMixin, BaseView):
    def _build(self):
        self._init_list_form_hosts()
        self.page_title("Despacho de combustible", parent=self._list_host)
        bar = self.page_toolbar(parent=self._list_host)
        self.toolbar_btn(bar.right, "Nuevo despacho", command=self._nuevo,
                         width=168).pack(side="right")
        panel = self.page_list_panel(parent=self._list_host)
        self._ptbl = self.page_paginated_table(panel, [
            ("id", "#", 40), ("fecha", "Fecha", 120), ("cedula", "Cédula", 100),
            ("beneficiario", "Beneficiario", 160), ("litros", "Litros", 90),
            ("tipo", "Tipo", 100), ("monto", "Monto Bs", 100), ("estado", "Estado", 110),
        ], page_size=ROWS_PER_PAGE, row_actions=self._row_actions)

    def _refresh(self):
        rows = self.db.get_despachos(limit=2000)
        self._ptbl.load([self._fmt(r) for r in rows])

    @staticmethod
    def _fmt(r):
        return {
            "id": r["id"], "fecha": r["fecha"][:16], "cedula": r["cedula"],
            "beneficiario": r["beneficiario"], "litros": f"{r['litros']:,.0f} L",
            "tipo": r["tipo"], "monto": f"{r['monto_bs']:,.2f}",
            "estado": despacho_estado(r), "_raw": r,
        }

    def _row_actions(self, row, _idx):
        r = row["_raw"]
        items = [("Ver", lambda: self._ver(r), False)]
        if self.can_delete and r["estado"] != "anulado":
            items.append(("Anular", lambda: self._anular(r), True))
        return items

    def _nuevo(self):
        self._open_form(forms.DespachoFormPage, on_new_beneficiario=self._nuevo_beneficiario)

    def _nuevo_beneficiario(self):
        def _volver():
            self._close_form()
            self.mark_stale()
            if self.app:
                self.app.notify_data_changed()
            self._open_form(forms.DespachoFormPage, on_new_beneficiario=self._nuevo_beneficiario)
        self._open_form(forms.BeneficiarioFormPage, on_done=_volver)

    def _ver(self, r):
        estado = despacho_estado(r)
        fields = [
            ("Despacho", f"#{r['id']}"), ("Fecha", r["fecha"][:16]),
            ("Beneficiario", f"{r['beneficiario']} ({r['cedula']})"),
            ("Combustible", r["tipo"]), ("Litros", f"{r['litros']:,.0f} L"),
            ("Monto", f"{r['monto_bs']:,.2f} Bs"), ("Estado", estado),
            ("Operador", r["operador"]), ("Observaciones", r["observaciones"] or "—"),
        ]
        if r["estado"] == "anulado":
            fields.append(("Motivo de anulación", r["motivo_anulacion"] or "—"))
        modals.DetailModal(self.app, "Ver despacho", fields, [])

    def _anular(self, r):
        modals.ConfirmModal(
            self.app, "Anular despacho",
            f"¿Anular el despacho #{r['id']}? Se devolverán {r['litros']:,.0f} L al inventario.",
            need_reason=True, confirm_text="Anular", variant="danger",
            on_confirm=lambda motivo: self._do_anular(r, motivo))

    def _do_anular(self, r, motivo):
        self.db.anular_despacho(r["id"], motivo, self.user["nombre"])
        self.db.log(self.user["id"], self.user["nombre"], "Despachos",
                    "Anular", f"#{r['id']} — {motivo}")
        self._refresh()
        self.app.toast("Despacho anulado")
