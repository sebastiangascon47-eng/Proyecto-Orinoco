"""Vista: Operadores (admin)."""
from __future__ import annotations
from core.theme import ROWS_PER_PAGE
from ui import modals
from ui import forms
from ui.views.base import BaseView, ListFormMixin


class OperadoresView(ListFormMixin, BaseView):
    def _build(self):
        if not self._require_admin():
            return
        self._init_list_form_hosts()
        self.page_title("Operadores", parent=self._list_host)
        bar = self.page_toolbar(parent=self._list_host)
        self.toolbar_btn(bar.right, "Nuevo operador", command=self._nuevo,
                         width=168).pack(side="right")
        panel = self.page_list_panel(parent=self._list_host)
        self._ptbl = self.page_paginated_table(panel, [
            ("usuario", "Usuario", 130), ("nombre", "Nombre", 200),
            ("rol", "Rol", 140), ("estado", "Estado", 130),
        ], page_size=ROWS_PER_PAGE, row_actions=self._row_actions)

    def _refresh(self):
        rows = []
        for o in self.db.get_operadores():
            propio = o["id"] == self.user["id"]
            estado = "Activo" if o["activo"] else "Inactivo"
            if propio:
                estado = "Protegido"
            rows.append({
                "usuario": o["usuario"], "nombre": f"{o['nombre']} {o['apellido']}".strip(),
                "rol": "Administrador" if o["rol"] == "administrador" else "Operador",
                "estado": estado, "_raw": o, "_propio": propio,
            })
        self._ptbl.load(rows)

    def _row_actions(self, row, _idx):
        o, propio = row["_raw"], row["_propio"]
        items = [
            ("Ver", lambda: self._ver(o, propio), False),
            ("Editar", lambda: self._editar(o), False),
            ("Restablecer clave", lambda: self._reset(o), False),
        ]
        if not propio and self.can_delete:
            if o["activo"]:
                items.append(("Dar de baja", lambda: self._toggle(o, 0), True))
            else:
                items.append(("Reactivar", lambda: self._toggle(o, 1), False))
        return items

    def _nuevo(self):
        self._open_form(forms.OperadorFormPage)

    def _ver(self, o, propio):
        fields = [
            ("Usuario", o["usuario"]), ("Nombre", f"{o['nombre']} {o['apellido']}".strip()),
            ("Cédula", o["cedula"] or "—"), ("Teléfono", o["telefono"] or "—"),
            ("Rol", "Administrador" if o["rol"] == "administrador" else "Operador"),
            ("Estado", "Activo" if o["activo"] else "Inactivo"),
            ("Creado", (o["creado_en"] or "")[:16]),
        ]
        badge = "Cuenta protegida — sesión actual" if propio else None
        modals.DetailModal(self.app, "Ver operador", fields, [], badge=badge)

    def _editar(self, o):
        self._open_form(forms.OperadorFormPage, registro=dict(o))

    def _reset(self, o):
        modals.ResetPasswordModal(self.app, self.db, self.user, self._refresh, dict(o))

    def _toggle(self, o, activo):
        accion = "Reactivar" if activo else "Desactivar"
        modals.ConfirmModal(
            self.app, f"{accion} operador",
            f"¿{accion} la cuenta de {o['usuario']}?",
            confirm_text=accion, variant="reactivate" if activo else "danger",
            on_confirm=lambda _: self._do_toggle(o, activo))

    def _do_toggle(self, o, activo):
        self.db.toggle_operador(o["id"], activo)
        self.db.log(self.user["id"], self.user["nombre"], "Operadores",
                    "Reactivar" if activo else "Desactivar", o["usuario"])
        self._refresh()
        self.app.toast("Operador " + ("reactivado" if activo else "desactivado"))
