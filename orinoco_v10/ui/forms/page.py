"""
page.py — Vista de formulario amplio (sustituye modales con muchos campos).

Formularios con más de FORM_FIELD_THRESHOLD campos usan esta plantilla;
los cortos siguen en ui/modals/forms.py.
"""
from __future__ import annotations
import customtkinter as ctk
from core.theme import C, FONT_H1, FONT_SM, FONT_LABEL, PAD, PAD_SM, R_LG, BTN_H
from ui.components.widgets import btn, btn_row, divider

FORM_FIELD_THRESHOLD = 5


class FormPage(ctk.CTkFrame):
    """Formulario a pantalla completa con dos columnas simétricas."""

    FIELD_W = 360
    COL_GAP = 28

    def __init__(self, parent, title: str, subtitle: str = "",
                 on_cancel=None, save_text: str = "Guardar",
                 on_save=None, accent=None):
        super().__init__(parent, fg_color=C["bg"])
        self._on_cancel = on_cancel
        self._on_save = on_save
        self._accent = accent or C["red"]

        accent_bar = ctk.CTkFrame(self, height=3, fg_color=self._accent, corner_radius=0)
        accent_bar.pack(fill="x")

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=PAD, pady=(PAD_SM, 0))
        btn(hdr, "Volver", command=self._cancel, variant="ghost",
            width=120, height=BTN_H).pack(side="left")
        tit_col = ctk.CTkFrame(hdr, fg_color="transparent")
        tit_col.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(tit_col, text=title, font=FONT_H1,
                     text_color=C["text"]).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(tit_col, text=subtitle, font=FONT_SM,
                         text_color=C["text3"]).pack(anchor="w", pady=(2, 0))

        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=PAD, pady=(10, 0))

        card = ctk.CTkFrame(outer, fg_color=C["card"], corner_radius=R_LG,
                            border_width=1, border_color=C["border"])
        card.pack(anchor="n", fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color=C["elevated"],
            scrollbar_button_hover_color=C["border"],
        )
        scroll.pack(fill="both", expand=True, padx=PAD_SM, pady=PAD_SM)

        self._full = ctk.CTkFrame(scroll, fg_color="transparent")
        self._full.pack(fill="x")

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", pady=(4, 0))
        self._col0 = ctk.CTkFrame(grid, fg_color="transparent")
        self._col1 = ctk.CTkFrame(grid, fg_color="transparent")
        self._col0.pack(side="left", fill="both", expand=True, padx=(0, self.COL_GAP // 2))
        self._col1.pack(side="left", fill="both", expand=True, padx=(self.COL_GAP // 2, 0))
        self._cols = (self._col0, self._col1)

        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.pack(fill="x", padx=PAD, pady=(8, PAD_SM))
        divider(foot, pady=(0, 10))
        self._err = ctk.CTkLabel(foot, text="", font=FONT_SM, text_color=C["red"])
        self._err.pack(anchor="center", pady=(0, 6))
        self._btn_row = ctk.CTkFrame(foot, fg_color="transparent")
        self._btn_row.pack(fill="x")
        btn_row(self._btn_row, [
            ("Cancelar", self._cancel, "ghost", 140),
            (save_text, self._save, "primary", 200),
        ], align="center")

    @property
    def col_left(self):
        return self._col0

    @property
    def col_right(self):
        return self._col1

    @property
    def full_width(self):
        return self._full

    def set_error(self, msg: str):
        self._err.configure(text=msg)

    def clear_error(self):
        self._err.configure(text="")

    def _cancel(self):
        if self._on_cancel:
            self._on_cancel()

    def _save(self):
        if self._on_save:
            self._on_save()

    def set_actions(self, specs):
        """Reemplaza los botones del pie (texto, cmd, variant, width)."""
        for w in self._btn_row.winfo_children():
            w.destroy()
        btn_row(self._btn_row, specs, align="center")
