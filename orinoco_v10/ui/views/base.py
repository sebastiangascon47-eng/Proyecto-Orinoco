"""
base.py — Plantilla de página (equivalente a templates/base.html + .page de SISARAD).

Estructura estándar de cada módulo:
  page → title → [metrics] → toolbar → panel → [sections]
"""
from __future__ import annotations
import time
import customtkinter as ctk
from core.theme import C, FONT_H1, FONT_H3, FONT_SM, PAD, PAD_SM, R_LG, BTN_H, CTRL_H, ROWS_PER_PAGE
from core import permissions as perm
from ui.components.widgets import MetricCards, btn, card, PaginatedTable

# Mínimo entre refrescos al re-entrar a un módulo (evita recargas al alternar menú)
_REFRESH_COOLDOWN_S = 2.0


class BaseView(ctk.CTkFrame):
    """Vista base con layout profesional reutilizable."""

    def __init__(self, parent, db, user, navigate=None, app=None):
        super().__init__(parent, fg_color=C["bg"])
        self.db = db
        self.user = user
        self.navigate = navigate
        self.app = app
        self.is_admin = perm.is_admin(user)
        self._refresh_job = None
        self._needs_refresh = True
        self._last_refresh = 0.0
        self._page = ctk.CTkFrame(self, fg_color="transparent")
        self._page.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        pass

    @property
    def can_edit(self) -> bool:
        return perm.can_edit(self.user)

    @property
    def can_delete(self) -> bool:
        return perm.can_delete(self.user)

    @property
    def can_report(self) -> bool:
        return perm.can_report(self.user)

    def _require_admin(self) -> bool:
        """Muestra aviso y devuelve False si el usuario no es administrador."""
        if self.is_admin:
            return True
        self.page_title("Acceso restringido")
        ctk.CTkLabel(
            self._page,
            text="Esta sección es exclusiva del administrador.",
            font=FONT_H3, text_color=C["text2"],
        ).pack(padx=PAD, pady=PAD)
        return False

    def _refresh(self):
        pass

    def mark_stale(self):
        self._needs_refresh = True

    def on_hide(self):
        """Al salir del módulo: cancelar cargas y cerrar formularios superpuestos."""
        self.cancel_async()
        if hasattr(self, "_form_host") and self._form_host.winfo_ismapped():
            self._close_form()

    def on_show(self):
        """Recarga datos solo si hace falta (diferido para no bloquear la UI)."""
        if hasattr(self, "_form_host") and self._form_host.winfo_ismapped():
            return
        if not self._needs_refresh:
            elapsed = time.monotonic() - self._last_refresh
            if elapsed < _REFRESH_COOLDOWN_S:
                return
        self.schedule_refresh()

    def schedule_refresh(self):
        self._needs_refresh = True
        if self._refresh_job:
            try:
                self.after_cancel(self._refresh_job)
            except Exception:
                pass
        self._refresh_job = self.after_idle(self._do_refresh)

    def _do_refresh(self):
        self._refresh_job = None
        self._refresh()
        self._needs_refresh = False
        self._last_refresh = time.monotonic()

    def cancel_async(self):
        """Cancela cargas pendientes al salir de la vista."""
        if self._refresh_job:
            try:
                self.after_cancel(self._refresh_job)
            except Exception:
                pass
            self._refresh_job = None
        from ui.components.widgets import DataTable, PaginatedTable
        for obj in vars(self).values():
            if isinstance(obj, (DataTable, PaginatedTable)):
                obj.cancel_load()

    def page_title(self, title: str, subtitle: str = "", actions=None, parent=None):
        """Encabezado .title + acciones principales."""
        root = parent or self._page
        h = ctk.CTkFrame(root, fg_color="transparent")
        h.pack(fill="x", padx=PAD, pady=(PAD, 6))
        left = ctk.CTkFrame(h, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(left, text=title, font=FONT_H1, text_color=C["text"]).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(left, text=subtitle, font=FONT_SM,
                         text_color=C["text3"]).pack(anchor="w", pady=(2, 0))
        if actions:
            actions_row = ctk.CTkFrame(h, fg_color="transparent")
            actions_row.pack(side="right")
            for text, variant, cmd in actions:
                btn(actions_row, text, command=cmd, variant=variant,
                    width=168, height=BTN_H).pack(side="left", padx=(0, 8))
        return h

    def page_metrics(self, metrics: list[tuple], parent=None) -> MetricCards:
        """Fila de tarjetas KPI (.cardGrid). Métrica: (label, value, color[, on_click])."""
        root = parent or self._page
        cards = MetricCards(root, metrics)
        cards.pack(fill="x", padx=PAD, pady=(2, 8))
        return cards

    def page_toolbar(self, parent=None):
        """Barra con zonas izquierda (filtros) y derecha (acciones)."""
        root = parent or self._page
        bar = ctk.CTkFrame(root, fg_color="transparent", height=CTRL_H + 8)
        bar.pack(fill="x", padx=PAD, pady=(0, 10))
        bar.pack_propagate(False)
        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left", fill="y")
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right", fill="y")
        bar.left = left
        bar.right = right
        return bar

    def toolbar_btn(self, parent, text, command=None, variant="primary", width=168):
        """Botón estándar para toolbars."""
        return btn(parent, text, command=command, variant=variant,
                   width=width, height=BTN_H)

    def page_list_panel(self, expand: bool = True, parent=None) -> ctk.CTkFrame:
        """Panel plano (.panel) para listas — sin título interno."""
        root = parent or self._page
        outer = ctk.CTkFrame(root, fg_color=C["card"], corner_radius=R_LG,
                             border_width=1, border_color=C["border"])
        outer.pack(fill="both" if expand else "x", expand=expand,
                   padx=PAD, pady=(0, PAD))
        body = ctk.CTkFrame(outer, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=PAD_SM, pady=PAD_SM)
        return body

    def page_panel(self, title: str | None = None, expand: bool = True) -> ctk.CTkFrame:
        """Panel con borde (.panel) — contenedor para tablas o formularios."""
        outer = card(self._page)
        outer.pack(fill="both" if expand else "x", expand=expand, padx=PAD, pady=(0, PAD))
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=PAD_SM, pady=PAD_SM)
        if title:
            ctk.CTkLabel(inner, text=title, font=FONT_H3,
                         text_color=C["text"]).pack(anchor="w", pady=(0, 8))
        body = ctk.CTkFrame(inner, fg_color="transparent")
        body.pack(fill="both", expand=True)
        return body

    def section_title(self, text: str):
        """Título de sección dentro de la página (.sectionTitle)."""
        ctk.CTkLabel(self._page, text=text, font=FONT_H3,
                     text_color=C["text"]).pack(anchor="w", padx=PAD, pady=(12, 6))

    def _header(self, title, subtitle="", actions=None):
        return self.page_title(title, subtitle, actions)

    def page_paginated_table(self, parent, columns, page_size=ROWS_PER_PAGE,
                             row_actions=None, expand=False) -> PaginatedTable:
        """Tabla con paginación (sin barra de scroll interna)."""
        root = parent or self._page
        pt = PaginatedTable(root, columns, page_size=page_size, row_actions=row_actions)
        if expand:
            pt.pack(fill="both", expand=True)
        else:
            pt.pack(fill="x")
        return pt


class ListFormMixin:
    """Alterna entre lista y formulario amplio en el mismo módulo."""

    def _init_list_form_hosts(self):
        self._list_host = ctk.CTkFrame(self._page, fg_color="transparent")
        self._form_host = ctk.CTkFrame(self._page, fg_color=C["bg"])
        self._list_host.pack(fill="both", expand=True)

    def _open_form(self, form_cls, on_done=None, **kwargs):
        for w in self._form_host.winfo_children():
            w.destroy()
        form_cls(
            self._form_host,
            db=self.db,
            user=self.user,
            app=self.app,
            on_done=on_done or self._form_saved,
            on_cancel=self._close_form,
            **kwargs,
        ).pack(fill="both", expand=True)
        self._list_host.pack_forget()
        self._form_host.pack(fill="both", expand=True)

    def _close_form(self):
        for w in self._form_host.winfo_children():
            w.destroy()
        self._form_host.pack_forget()
        self._list_host.pack(fill="both", expand=True)

    def _form_saved(self):
        self._close_form()
        self.mark_stale()
        self.schedule_refresh()
        if self.app and hasattr(self.app, "notify_data_changed"):
            self.app.notify_data_changed()
