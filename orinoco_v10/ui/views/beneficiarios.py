"""Vista: Beneficiarios."""
from __future__ import annotations
import customtkinter as ctk
from core.theme import C, FONT_SM, CTRL_H, ROWS_PER_PAGE
from ui import modals
from ui import forms
from ui.components.widgets import field
from ui.views.base import BaseView, ListFormMixin


class BeneficiariosView(ListFormMixin, BaseView):
    def _build(self):
        self._init_list_form_hosts()
        self.page_title("Beneficiarios", parent=self._list_host)
        bar = self.page_toolbar(parent=self._list_host)
        self._search = field(bar.left, placeholder="Buscar por cédula, nombre o embarcación…",
                             width=380, height=CTRL_H)
        self._search.pack(side="left")
        self._search.bind("<KeyRelease>", self._schedule_search)
        self._search_job = None
        self._ver_inact = ctk.BooleanVar(value=False)
        if self.is_admin:
            ctk.CTkCheckBox(bar.left, text="Ver inactivos", variable=self._ver_inact,
                            command=self._refresh, font=FONT_SM, text_color=C["text2"],
                            fg_color=C["red"], hover_color=C["red_hover"]).pack(
                side="left", padx=(14, 0))
        self.toolbar_btn(bar.right, "Nuevo beneficiario", command=self._nuevo,
                         width=180).pack(side="right")
        panel = self.page_list_panel(parent=self._list_host)
        self._ptbl = self.page_paginated_table(panel, [
            ("cedula", "Cédula", 110), ("nombre", "Nombre", 130),
            ("apellido", "Apellido", 130), ("embarcacion", "Embarcación", 150),
            ("telefono", "Teléfono", 130), ("estado", "Estado", 90),
        ], page_size=ROWS_PER_PAGE, row_actions=self._row_actions)

    def _schedule_search(self, _event=None):
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(280, self._run_search)

    def _run_search(self):
        self._search_job = None
        self._refresh()

    def _refresh(self):
        solo = not self._ver_inact.get()
        term = self._search.get().strip()
        rows = (self.db.search_beneficiarios(term, solo) if term
                else self.db.get_beneficiarios(solo))
        self._ptbl.load([{
            "cedula": r["cedula"], "nombre": r["nombre"], "apellido": r["apellido"],
            "embarcacion": r["embarcacion"] or "—", "telefono": r["telefono"] or "—",
            "estado": "Activo" if r["activo"] else "Inactivo", "_raw": r,
        } for r in rows])

    def _row_actions(self, row, _idx):
        r = row["_raw"]
        items = [
            ("Ver", lambda: self._ver(r), False),
        ]
        if self.can_edit:
            items.append(("Editar", lambda: self._editar(r), False))
        if self.can_delete:
            if r["activo"]:
                items.append(("Dar de baja", lambda: self._baja(r, 0), True))
            else:
                items.append(("Reactivar", lambda: self._baja(r, 1), False))
        return items

    def _nuevo(self):
        self._open_form(forms.BeneficiarioFormPage)

    def _ver(self, r):
        fields = [
            ("Cédula", r["cedula"]), ("Nombre", f"{r['nombre']} {r['apellido']}"),
            ("Teléfono", r["telefono"] or "—"), ("Correo", r["correo"] or "—"),
            ("Embarcación", r["embarcacion"] or "—"), ("Motor", r["motor"] or "—"),
            ("Estado", "Activo" if r["activo"] else "Inactivo"),
            ("Registrado", (r["creado_en"] or "")[:16]),
        ]
        modals.DetailModal(self.app, "Ver beneficiario", fields, [])

    def _editar(self, r):
        self._open_form(forms.BeneficiarioFormPage, registro=dict(r))

    def _baja(self, r, activo):
        accion = "Reactivar" if activo else "Dar de baja"
        modals.ConfirmModal(
            self.app, f"{accion} beneficiario",
            f"¿Confirma {accion.lower()} a {r['nombre']} {r['apellido']}?",
            confirm_text=accion, variant="reactivate" if activo else "danger",
            on_confirm=lambda _: self._do_baja(r, activo))

    def _do_baja(self, r, activo):
        self.db.toggle_beneficiario(r["id"], activo)
        self.db.log(self.user["id"], self.user["nombre"], "Beneficiarios",
                    "Reactivar" if activo else "Dar de baja", f"{r['nombre']} {r['apellido']}")
        self._refresh()
        self.app.toast("Beneficiario " + ("reactivado" if activo else "dado de baja"))
