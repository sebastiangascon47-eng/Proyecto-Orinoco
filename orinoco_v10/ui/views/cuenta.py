"""Vista: Mi cuenta."""
from __future__ import annotations
import customtkinter as ctk
from core.theme import C, FONT_BODY, FONT_H3, FONT_SM, FONT_SM_M, PAD, PAD_SM
from ui import modals
from ui.components.widgets import btn_row, card
from ui.views.base import BaseView


class CuentaView(BaseView):
    def _build(self):
        self.page_title("Mi cuenta", "Datos de la sesión y seguridad")
        info = card(self._page)
        info.pack(fill="x", padx=PAD, pady=(2, 10))
        inner = ctk.CTkFrame(info, fg_color="transparent")
        inner.pack(fill="x", padx=PAD, pady=PAD_SM)
        for label, val in [
            ("Usuario", self.user.get("usuario", "—")),
            ("Nombre", f"{self.user.get('nombre','')} {self.user.get('apellido','')}".strip()),
            ("Rol", "Administrador" if self.is_admin else "Operador"),
        ]:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, font=FONT_SM_M, text_color=C["text2"],
                         width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=FONT_BODY, text_color=C["text"]).pack(side="left")
        sec = card(self._page)
        sec.pack(fill="x", padx=PAD, pady=(0, 10))
        si = ctk.CTkFrame(sec, fg_color="transparent")
        si.pack(fill="x", padx=PAD, pady=PAD_SM)
        ctk.CTkLabel(si, text="Seguridad", font=FONT_H3, text_color=C["text"]).pack(anchor="w")
        btn_row(si, [("Cambiar contraseña", self._cambiar, "secondary", 200)], align="center")
        sis = card(self._page)
        sis.pack(fill="x", padx=PAD, pady=(0, PAD))
        sysi = ctk.CTkFrame(sis, fg_color="transparent")
        sysi.pack(fill="x", padx=PAD, pady=PAD_SM)
        ctk.CTkLabel(sysi, text="Información del sistema", font=FONT_H3,
                     text_color=C["text"]).pack(anchor="w", pady=(0, 6))
        cfg = self.db.get_all_config()
        for label, val in [
            ("Sistema", "Orinoco v10"),
            ("Estación", cfg.get("nombre_estacion", "—")),
            ("RIF", cfg.get("rif", "—")),
            ("Base de datos", "SQLite (data/orinoco.db)"),
        ]:
            row = ctk.CTkFrame(sysi, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=label, font=FONT_SM_M, text_color=C["text2"],
                         width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=FONT_SM, text_color=C["text"]).pack(side="left")

    def _refresh(self):
        pass

    def _cambiar(self):
        modals.CambiarPasswordModal(self.app, self.db, self.user)
