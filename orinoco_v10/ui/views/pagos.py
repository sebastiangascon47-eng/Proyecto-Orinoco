"""Vista: Pagos — cobros pendientes y registrados."""
from __future__ import annotations
import customtkinter as ctk
from core import permissions as perm
from core.theme import C, FONT_H1, M, PAD, ROWS_PER_PAGE_COMPACT
from ui import modals
from ui.views.base import BaseView
from ui.views.utils import pago_estado


class PagosView(BaseView):
    def _build(self):
        self._page.grid_columnconfigure(0, weight=1)
        self._page.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self._page, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=PAD, pady=(PAD, 6))
        ctk.CTkLabel(top, text="Control de pagos", font=FONT_H1,
                     text_color=C["text"]).pack(anchor="w")
        bar = self.page_toolbar(parent=top)
        self.toolbar_btn(bar.right, "Registrar pago", command=self._registrar_pago,
                         width=168).pack(side="right")

        body = ctk.CTkScrollableFrame(
            self._page, fg_color="transparent",
            scrollbar_button_color=C["elevated"],
            scrollbar_button_hover_color=C["border"],
        )
        body.grid(row=1, column=0, sticky="nsew")

        self._cards = self.page_metrics([
            ("Monto por cobrar", "0 Bs", M[0]),
            ("Cobrado hoy", "0 Bs", M[2]),
        ], parent=body)
        self.section_title("Despachos pendientes de pago", parent=body)
        pend = self.page_list_panel(expand=False, parent=body)
        self._pend = self.page_paginated_table(pend, [
            ("id", "#", 40), ("fecha", "Fecha", 120), ("cedula", "Cédula", 100),
            ("beneficiario", "Beneficiario", 180), ("litros", "Litros", 90),
            ("monto", "Monto Bs", 110),
        ], page_size=ROWS_PER_PAGE_COMPACT, row_actions=self._pend_actions, expand=False)
        self.section_title("Pagos registrados", parent=body)
        done = self.page_list_panel(expand=False, parent=body)
        self._done = self.page_paginated_table(done, [
            ("id", "#", 40), ("fecha", "Fecha", 120), ("beneficiario", "Beneficiario", 180),
            ("monto", "Monto Bs", 110), ("referencia", "Referencia", 130),
            ("metodo", "Método", 110), ("estado", "Estado", 100),
        ], page_size=ROWS_PER_PAGE_COMPACT, row_actions=self._done_actions, expand=False)
        ctk.CTkFrame(body, fg_color="transparent", height=24).pack()

    @staticmethod
    def _despacho_editable(r) -> bool:
        return r["estado"] == "registrado" and not r["pagado"]

    def _registrar_pago(self):
        pend = [dict(r) for r in self.db.get_despachos_pendientes()]
        if not pend:
            self.app.toast("No hay despachos pendientes de pago", "warning")
            return
        if len(pend) == 1:
            self._abrir_pago(pend[0])
            return
        modals.SeleccionDespachoPagoModal(self.app, pend, self._abrir_pago)

    def _abrir_pago(self, despacho: dict):
        modals.PagoModal(self.app, self.db, self.user, self._on_change, despacho)

    def _refresh(self):
        sc = self.db.stats_cobros()
        self._cards.update("Monto por cobrar", f"{sc['monto_pendiente']:,.2f} Bs")
        self._cards.update("Cobrado hoy", f"{sc['cobrado_hoy']:,.2f} Bs")
        self._pend.table._last_fp = None
        self._pend.set_hidden_columns({"id"})
        self._pend.load([{
            "id": r["id"], "fecha": r["fecha"][:16], "cedula": r["cedula"],
            "beneficiario": r["beneficiario"], "litros": f"{r['litros']:,.0f} L",
            "monto": f"{r['monto_bs']:,.2f}", "_raw": r,
        } for r in self.db.get_despachos_pendientes()])
        self._done.table._last_fp = None
        self._done.set_hidden_columns(set())
        self._done.load([{
            "id": p["id"], "fecha": p["fecha"][:16], "beneficiario": p["beneficiario"],
            "monto": f"{p['monto_bs']:,.2f}", "referencia": p["referencia"] or "—",
            "metodo": p["metodo"],
            "estado": pago_estado(p), "_raw": p,
        } for p in self.db.get_pagos(limit=500, incluir_anulados=False)])

    def _pend_actions(self, row, _idx):
        r = row["_raw"]
        items: list = []
        if perm.can_edit_despacho(self.user) and self._despacho_editable(r):
            items.append(("Editar", lambda: modals.DespachoEditModal(
                self.app, self.db, self.user, self._on_change, dict(r)), False))
        if self.can_delete:
            items.append(("Anular despacho", lambda: self._anular_despacho(r), True))
        return items

    def _on_change(self):
        self.mark_stale()
        self._refresh()
        if self.app and hasattr(self.app, "notify_data_changed"):
            self.app.notify_data_changed()

    def _done_actions(self, row, _idx):
        p = row["_raw"]
        items = [("Ver", lambda: self._ver(p), False)]
        if self.can_delete and p["estado"] != "anulado":
            items.append(("Anular pago", lambda: self._anular(p), True))
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

    def _anular_despacho(self, r):
        modals.ConfirmModal(
            self.app, "Anular despacho",
            f"¿Anular el despacho #{r['id']}? Se devolverán {r['litros']:,.0f} L al inventario. "
            "El registro quedará marcado como anulado.",
            need_reason=True, confirm_text="Anular", variant="danger",
            on_confirm=lambda motivo: self._do_anular_despacho(r, motivo))

    def _do_anular_despacho(self, r, motivo):
        if not self.db.anular_despacho(r["id"], motivo, self.user["nombre"]):
            self.app.toast("No se pudo anular el despacho", "error")
            return
        self.db.log(self.user["id"], self.user["nombre"], "Pagos",
                    "Anular despacho", f"#{r['id']} — {motivo}")
        self._on_change()
        self.app.toast("Despacho anulado")

    def _anular(self, p):
        modals.ConfirmModal(
            self.app, "Anular pago",
            f"¿Anular el pago #{p['id']}? El despacho asociado volverá a quedar pendiente.",
            need_reason=True, confirm_text="Anular", variant="danger",
            on_confirm=lambda motivo: self._do_anular(p, motivo))

    def _do_anular(self, p, motivo):
        if not self.db.anular_pago(p["id"], motivo, self.user["nombre"]):
            self.app.toast("No se pudo anular el pago", "error")
            return
        self.db.log(self.user["id"], self.user["nombre"], "Pagos",
                    "Anular", f"#{p['id']} — {motivo}")
        self._on_change()
        self.app.toast("Pago anulado y retirado de la lista")
