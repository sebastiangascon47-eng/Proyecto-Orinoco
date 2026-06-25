"""Vista: Despachos."""
from __future__ import annotations
import customtkinter as ctk
from core.theme import C, FONT_SM, CTRL_H, ROWS_PER_PAGE
from ui import forms
from ui import modals
from ui.components.widgets import dropdown
from ui.views.base import BaseView, ListFormMixin
from ui.views.utils import despacho_estado

_FILTROS = ("Pendientes de pago", "Todos", "Pagados")


class DespachoView(ListFormMixin, BaseView):
    def _build(self):
        self._init_list_form_hosts()
        self.page_title("Despacho de combustible", parent=self._list_host)
        bar = self.page_toolbar(parent=self._list_host)
        ctk.CTkLabel(bar.left, text="Ver:", font=FONT_SM,
                     text_color=C["text2"]).pack(side="left", padx=(0, 8))
        self._fil = dropdown(bar.left, list(_FILTROS), width=200, height=CTRL_H)
        self._fil.set(_FILTROS[0])
        self._fil.configure(command=self._on_filtro)
        self._fil.pack(side="left")
        self.toolbar_btn(bar.right, "Editar despacho", command=self._editar_despacho,
                         variant="secondary", width=168).pack(side="right", padx=(0, 8))
        self.toolbar_btn(bar.right, "Nuevo despacho", command=self._nuevo,
                         width=168).pack(side="right")
        panel = self.page_list_panel(parent=self._list_host)
        self._ptbl = self.page_paginated_table(panel, [
            ("id", "#", 40), ("fecha", "Fecha", 120), ("cedula", "Cédula", 100),
            ("beneficiario", "Beneficiario", 160), ("litros", "Litros", 90),
            ("tipo", "Tipo", 100), ("monto", "Monto Bs", 100), ("estado", "Estado", 110),
        ], page_size=ROWS_PER_PAGE, row_actions=self._row_actions)

    def _on_filtro(self, _choice=None):
        self._refresh()

    def _pendientes(self) -> list[dict]:
        return [dict(r) for r in self.db.get_despachos_pendientes()]

    def _filtered_rows(self):
        rows = self.db.get_despachos(limit=2000, incluir_anulados=True)
        f = self._fil.get() if hasattr(self, "_fil") else _FILTROS[0]
        if f == "Pendientes de pago":
            return [r for r in rows if r["estado"] == "registrado" and not int(r["pagado"])]
        if f == "Pagados":
            return [r for r in rows if r["estado"] == "registrado" and int(r["pagado"])]
        return rows

    def _refresh(self):
        rows = self._filtered_rows()
        self._ptbl.set_hidden_columns(set())
        self._ptbl.table._last_fp = None
        self._ptbl.load([self._fmt(r) for r in rows])

    @staticmethod
    def _fmt(r):
        rd = dict(r)
        return {
            "id": rd["id"], "fecha": rd["fecha"][:16], "cedula": rd["cedula"],
            "beneficiario": rd["beneficiario"], "litros": f"{rd['litros']:,.0f} L",
            "tipo": rd["tipo"], "monto": f"{rd['monto_bs']:,.2f}",
            "estado": despacho_estado(rd), "_raw": rd,
        }

    @staticmethod
    def _editable(r) -> bool:
        return r["estado"] == "registrado" and int(r["pagado"]) == 0

    def _abrir_editar(self, despacho: dict):
        modals.DespachoEditModal(
            self.app, self.db, self.user, self._on_change, despacho)

    def _editar_despacho(self):
        pend = self._pendientes()
        if not pend:
            self.app.toast("No hay despachos pendientes de pago para editar", "warning")
            return
        if len(pend) == 1:
            self._abrir_editar(pend[0])
            return
        modals.SeleccionDespachoModal(
            self.app, pend, self._abrir_editar,
            title="Editar despacho",
            message="Elija el despacho pendiente que desea modificar.",
            btn_text="Editar",
        )

    def _row_actions(self, row, _idx):
        r = row["_raw"]
        items = [("Ver", lambda rd=r: self._ver(rd), False)]
        if self.can_delete and r["estado"] == "registrado":
            items.append(("Anular", lambda rd=r: self._anular(rd), True))
        return items

    def _on_change(self):
        self.mark_stale()
        self._refresh()
        if self.app and hasattr(self.app, "notify_data_changed"):
            self.app.notify_data_changed()

    def _nuevo(self):
        self._open_form(forms.DespachoFormPage)

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
            f"¿Anular el despacho #{r['id']}? Se devolverán {r['litros']:,.0f} L al inventario. "
            "El registro permanecerá en la lista como anulado.",
            need_reason=True, confirm_text="Anular", variant="danger",
            on_confirm=lambda motivo, rd=r: self._do_anular(rd, motivo))

    def _do_anular(self, r, motivo):
        if not self.db.anular_despacho(r["id"], motivo, self.user["nombre"]):
            self.app.toast("No se pudo anular el despacho", "error")
            return
        self.db.log(self.user["id"], self.user["nombre"], "Despachos",
                    "Anular", f"#{r['id']} — {motivo}")
        self._on_change()
        self.app.toast("Despacho anulado")
