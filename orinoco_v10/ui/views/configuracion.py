"""Vista: Configuración (admin)."""
from __future__ import annotations
import customtkinter as ctk
from core.catalogs import MONEDAS
from core.theme import C, FONT_LABEL, PAD, PAD_SM
from ui.components.widgets import btn_row, card, dropdown, field
from ui.views.base import BaseView


class ConfiguracionView(BaseView):
    CAMPOS_TEXTO = [
        ("nombre_estacion", "Nombre de la estación"),
        ("rif", "RIF"),
    ]
    CAMPOS_PRECIO = [
        ("precio_litro_gasoil", "Precio por litro — Gasoil"),
        ("precio_litro_gasolina_91", "Precio por litro — Gasolina 91"),
        ("precio_litro_gasolina_95", "Precio por litro — Gasolina 95"),
    ]

    def _build(self):
        if not self._require_admin():
            return
        self.page_title("Configuración", "Parámetros generales del sistema")
        panel = card(self._page)
        panel.pack(fill="x", padx=PAD, pady=(2, PAD))
        inner = ctk.CTkFrame(panel, fg_color="transparent")
        inner.pack(fill="x", padx=PAD, pady=PAD_SM)
        self._entries = {}
        cfg = self.db.get_all_config()
        for clave, label in self.CAMPOS_TEXTO:
            ctk.CTkLabel(inner, text=label.upper(), font=(FONT_LABEL[0], 9, "bold"),
                         text_color=C["text3"]).pack(anchor="w", pady=(12, 3))
            e = field(inner, width=420, height=40)
            e.insert(0, cfg.get(clave, ""))
            e.pack(anchor="w")
            self._entries[clave] = e
        for clave, label in self.CAMPOS_PRECIO:
            ctk.CTkLabel(inner, text=label.upper(), font=(FONT_LABEL[0], 9, "bold"),
                         text_color=C["text3"]).pack(anchor="w", pady=(12, 3))
            e = field(inner, width=200, height=40)
            e.insert(0, cfg.get(clave, ""))
            e.pack(anchor="w")
            self._entries[clave] = e
        ctk.CTkLabel(inner, text="MONEDA", font=(FONT_LABEL[0], 9, "bold"),
                     text_color=C["text3"]).pack(anchor="w", pady=(12, 3))
        moneda = cfg.get("moneda", "Bs")
        self.c_moneda = dropdown(inner, list(MONEDAS), width=200)
        self.c_moneda.set(moneda if moneda in MONEDAS else MONEDAS[0])
        self.c_moneda.pack(anchor="w")
        btn_row(inner, [("Guardar configuración", self._save, "primary", 220)], align="center")

    def _refresh(self):
        pass

    def _save(self):
        for clave, e in self._entries.items():
            self.db.set_config(clave, e.get().strip())
        self.db.set_config("moneda", self.c_moneda.get())
        self.db.log(self.user["id"], self.user["nombre"], "Configuración",
                    "Actualizar", "Parámetros del sistema")
        self.app.toast("Configuración guardada")
