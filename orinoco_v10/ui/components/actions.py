"""
actions.py — Menú de acciones por fila (equivalente a partials/actions_menu.html).
"""
from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from core.theme import C, FONT_LABEL, R_MD, BTN_H

# (etiqueta, comando, es_peligroso)
ActionItem = tuple[str, callable, bool]


class RowActionMenu(ctk.CTkFrame):
    """Botón ⋮ con menú desplegable. Las acciones se resuelven al abrir (más rápido)."""

    def __init__(self, parent, items: list[ActionItem] | None = None,
                 get_items: callable | None = None):
        super().__init__(parent, fg_color="transparent", width=40, height=BTN_H)
        self._items: list[ActionItem] = items or []
        self._get_items = get_items
        self._menu: tk.Menu | None = None
        ctk.CTkButton(
            self, text="⋮", width=36, height=36,
            fg_color=C["card"], hover_color=C["table_hover"],
            border_width=1, border_color=C["border"],
            text_color=C["neutral_dark"],
            font=(FONT_LABEL[0], 16, "bold"),
            corner_radius=R_MD,
            command=self._open,
        ).place(relx=0.5, rely=0.5, anchor="center")

    def set_items(self, items: list[ActionItem]):
        self._items = items
        self._get_items = None

    def _resolve_items(self) -> list[ActionItem]:
        if self._get_items:
            return self._get_items() or []
        return self._items

    def _open(self):
        items = self._resolve_items()
        if not items:
            return
        if self._menu:
            self._menu.destroy()
        self._menu = tk.Menu(
            self, tearoff=0,
            bg=C["card"], fg=C["text"],
            activebackground=C["table_hover"],
            activeforeground=C["text"],
            borderwidth=1, relief="solid",
            font=(FONT_LABEL[0], 11),
        )
        for i, (label, cmd, danger) in enumerate(items):
            if i > 0 and danger and not items[i - 1][2]:
                self._menu.add_separator()
            self._menu.add_command(
                label=label,
                command=cmd,
                foreground=C["red"] if danger else C["text"],
            )
        try:
            x = self.winfo_rootx() + self.winfo_width() // 2 - 70
            y = self.winfo_rooty() + self.winfo_height()
            self._menu.tk_popup(max(x, 0), y)
        finally:
            self._menu.grab_release()
