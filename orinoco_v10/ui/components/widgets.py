"""
widgets.py — Componentes reutilizables v9
Estación Fluvial Orinoco C.A.

v9:
- LineChart con alineación correcta de puntos/sombreado, scope Día/Transacción
- Crosshair vertical en hover + tooltip
- Toast in-app anclado a la ventana principal
- MetricCards limpio sin iconos, barra de acento lateral
- DataTable con cursor pointer
"""
from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from core.theme import (
    C, FONT_BODY, FONT_SM, FONT_SM_M, FONT_XS, FONT_XS_M,
    FONT_LABEL, R_MD, R_LG, PAD, PAD_SM, BTN_H, CTRL_H, ROW_H, HDR_H,
)
from ui.components.actions import RowActionMenu


# ── Inputs ────────────────────────────────────────────────────────

def field(parent, placeholder="", width=240, show="", height=CTRL_H, **kw):
    e = ctk.CTkEntry(
        parent, placeholder_text=placeholder,
        width=width, height=height,
        fg_color=C["input"], border_color=C["border"], border_width=1,
        text_color=C["text"], placeholder_text_color=C["text3"],
        corner_radius=R_MD, font=FONT_BODY, show=show, **kw,
    )
    e.bind("<FocusIn>",  lambda _: e.configure(border_color=C["border_focus"],
                                                fg_color=C["input_focus"]))
    e.bind("<FocusOut>", lambda _: e.configure(border_color=C["border"],
                                                fg_color=C["input"]))
    return e


def dropdown(parent, values, width=200, **kw):
    return ctk.CTkComboBox(
        parent, values=values, width=width,
        fg_color=C["input"], border_color=C["border"],
        button_color=C["elevated"], button_hover_color=C["border"],
        dropdown_fg_color=C["card"], dropdown_text_color=C["text"],
        dropdown_hover_color=C["neutral_bg"],
        text_color=C["text"], font=FONT_BODY, corner_radius=R_MD, **kw,
    )


# ── Botones ───────────────────────────────────────────────────────

_SECONDARY = dict(fg_color=C["neutral_dark"], hover_color=C["neutral"],
                 text_color=C["text_inv"])

_VARIANTS = {
    "primary":    dict(fg_color=C["red"], hover_color=C["red_hover"], text_color=C["text_inv"]),
    "secondary":  dict(fg_color=C["elevated"], hover_color=C["border"], text_color=C["text"]),
    "ghost":      dict(fg_color="transparent", hover_color=C["elevated"], text_color=C["text2"],
                       border_width=1, border_color=C["border"]),
    "success":    _SECONDARY,
    "danger":     dict(fg_color=C["red_light"], hover_color=C["red_subtle"], text_color=C["red"],
                       border_width=1, border_color=C["red_mid"]),
    "amber":      _SECONDARY,
    "blue":       _SECONDARY,
    "flat":       dict(fg_color="transparent", hover_color=C["elevated"], text_color=C["text2"]),
    "reactivate": dict(fg_color=C["success_bg"], hover_color=C["neutral_bg"],
                       text_color=C["success"], border_width=1, border_color=C["success_border"]),
}


def btn(parent, text, command=None, variant="primary", width=140, height=BTN_H, **kw):
    p = dict(_VARIANTS.get(variant, _VARIANTS["primary"]))
    p.update(kw)
    return ctk.CTkButton(
        parent, text=text, command=command,
        width=width, height=height, corner_radius=R_MD,
        font=FONT_SM_M, **p,
    )


def btn_row(parent, specs, align="center"):
    """Fila de botones alineada (center | right | left). specs: (text, cmd, variant, width)."""
    outer = ctk.CTkFrame(parent, fg_color="transparent")
    outer.pack(fill="x")
    inner = ctk.CTkFrame(outer, fg_color="transparent")
    if align == "center":
        inner.pack(anchor="center", pady=2)
    elif align == "right":
        inner.pack(side="right", pady=2)
    else:
        inner.pack(side="left", pady=2)
    for i, spec in enumerate(specs):
        text = spec[0]
        cmd = spec[1] if len(spec) > 1 else None
        variant = spec[2] if len(spec) > 2 else "primary"
        width = spec[3] if len(spec) > 3 else 140
        padx = (0, 10) if i < len(specs) - 1 else 0
        btn(inner, text, command=cmd, variant=variant, width=width).pack(
            side="left", padx=padx)
    return outer


# ── Estructura ────────────────────────────────────────────────────

def divider(parent, padx=0, pady=(0, 0)):
    ctk.CTkFrame(parent, height=1, fg_color=C["border"],
                 corner_radius=0).pack(fill="x", padx=padx, pady=pady)


def card(parent, **kw):
    return ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=R_LG,
                        border_width=1, border_color=C["border"], **kw)


# ── Tooltip ──────────────────────────────────────────────────────

class Tooltip:
    """Tooltip flotante. Toplevel sin decoración."""

    def __init__(self, parent):
        self._parent = parent
        self._win = None
        self._lbl_title = None
        self._lbl_value = None

    def _ensure(self):
        if self._win is not None:
            return
        self._win = tk.Toplevel(self._parent)
        self._win.wm_overrideredirect(True)
        self._win.attributes("-topmost", True)
        try:
            self._win.attributes("-alpha", 0.97)
        except tk.TclError:
            pass

        frame = tk.Frame(self._win, bg=C["text"], highlightthickness=0)
        frame.pack(padx=1, pady=1)
        inner = tk.Frame(frame, bg=C["text"])
        inner.pack(padx=11, pady=8)

        self._lbl_title = tk.Label(inner, text="", bg=C["text"], fg="#CBD5E1",
                                    font=(FONT_LABEL[0], 9, "bold"))
        self._lbl_title.pack(anchor="w")
        self._lbl_value = tk.Label(inner, text="", bg=C["text"], fg="#FFFFFF",
                                    font=(FONT_LABEL[0], 13, "bold"))
        self._lbl_value.pack(anchor="w")
        self._win.withdraw()

    def show(self, x, y, title, value):
        self._ensure()
        self._lbl_title.configure(text=title)
        self._lbl_value.configure(text=value)
        self._win.update_idletasks()
        h = self._win.winfo_reqheight()
        self._win.geometry(f"+{x + 14}+{y - h - 12}")
        self._win.deiconify()

    def hide(self):
        if self._win is not None:
            self._win.withdraw()

    def destroy(self):
        if self._win is not None:
            self._win.destroy()
            self._win = None


# ── Toast IN-APP ─────────────────────────────────────────────────

class Toast:
    """
    Notificación flotante anclada DENTRO de la ventana principal.
    Aparece arriba a la derecha del área de contenido, se desliza hacia abajo,
    desaparece sola.
    """

    _COLORS = {
        "success": (C["success"],      C["success_bg"],  C["success_border"]),
        "error":   (C["red"],          C["red_light"],   C["red_mid"]),
        "info":    (C["neutral_dark"], C["neutral_bg"],  C["border"]),
        "warning": (C["warning"],      C["warning_bg"],  C["warning_border"]),
    }

    # Stack global de toasts activos (para apilar verticalmente)
    _stack: list = []

    @classmethod
    def show(cls, root, message: str, kind: str = "success",
             duration: int = 2800):
        """
        root: la MainApp (ctk.CTk). El toast se coloca con .place() sobre ella.
        """
        fg, bg, border = cls._COLORS.get(kind, cls._COLORS["info"])
        toast = ctk.CTkFrame(
            root, fg_color=bg, corner_radius=R_LG,
            border_width=1, border_color=border,
        )
        ctk.CTkLabel(
            toast, text=f"  {message}  ",
            font=FONT_SM_M, text_color=fg,
        ).pack(padx=PAD_SM, pady=10)

        # Calcular posición: arriba-derecha
        root.update_idletasks()
        rw = root.winfo_width()
        toast.update_idletasks()
        tw = toast.winfo_reqwidth()
        th = toast.winfo_reqheight()

        # Apilamiento vertical: cuántos toasts activos
        stack_offset = sum(t.winfo_reqheight() + 8 for t in cls._stack if t.winfo_exists())
        margin_right = 24
        margin_top   = 16

        x = rw - tw - margin_right
        y = margin_top + stack_offset

        toast.place(x=x, y=y)
        cls._stack.append(toast)

        # Auto-destruir
        def _dismiss():
            if toast in cls._stack:
                cls._stack.remove(toast)
            try:
                toast.destroy()
            except Exception:
                pass
            # Re-ordenar el stack
            for i, t in enumerate(cls._stack):
                if t.winfo_exists():
                    t.place(x=x, y=margin_top + sum(
                        s.winfo_reqheight() + 8
                        for s in cls._stack[:i] if s.winfo_exists()))

        toast.after(duration, _dismiss)


# ── Tabla (núcleo compartido) ─────────────────────────────────────

class _TableCore:
    """Lógica de filas/columnas compartida por tablas con y sin scroll."""

    ROW_H = ROW_H
    ACTION_W = 44
    CHUNK_SIZE = 200
    BATCH_THRESHOLD = 120
    _CENTER_COLS = frozenset({"id", "litros", "monto", "minimo", "capacidad", "_actions"})
    _CELL_PAD = (12, 8)
    _CELL_PAD_CENTER = (6, 6)
    _CELL_PAD_ACTION = (2, 2)

    def _init_table(self, columns, flat, row_actions):
        self.columns = list(columns)
        self.flat = flat
        self.row_actions = row_actions
        self._rows_data: list = []
        self._row_frames: list = []
        self._row_cells: list = []
        self._pool: list[dict] = []
        self._selected = None
        self._select_cb = None
        self._empty_lbl = None
        self._batch_job = None
        self._data_cols = []
        self._last_fp = None
        if row_actions:
            self.columns.append(("_actions", "⋮", self.ACTION_W))
        self._data_cols = [c for c in self.columns if c[0] != "_actions"]
        self._action_col = len(self.columns) - 1 if row_actions else -1
        self._grid = ctk.CTkFrame(self, fg_color=C["card"] if flat else "transparent")
        self._grid.pack(fill="both", expand=True)
        self._apply_col_grid(self._grid)
        self._grid.grid_rowconfigure(0, minsize=HDR_H, weight=0)
        self._build_header()
        if not row_actions:
            self.bind("<Button-1>", lambda _: self.deselect())

    def _col_anchor(self, key: str) -> str:
        return "center" if key in self._CENTER_COLS else "w"

    def _cell_pad(self, key: str) -> tuple[int, int]:
        if key == "_actions":
            return self._CELL_PAD_ACTION
        if key in self._CENTER_COLS:
            return self._CELL_PAD_CENTER
        return self._CELL_PAD

    def _apply_col_grid(self, frame):
        """Una sola grilla: columnas de datos proporcionales, acciones fijas."""
        for i, (key, _, hint) in enumerate(self.columns):
            if key == "_actions":
                frame.grid_columnconfigure(i, weight=0, minsize=self.ACTION_W)
            else:
                frame.grid_columnconfigure(i, weight=max(int(hint), 1))

    def _cancel_batch(self):
        if self._batch_job is not None:
            try:
                self.after_cancel(self._batch_job)
            except Exception:
                pass
            self._batch_job = None

    def cancel_load(self):
        self._cancel_batch()

    def _menu_items(self, entry: dict) -> list:
        idx = entry.get("idx", -1)
        if idx < 0 or not self.row_actions:
            return []
        return self.row_actions(self._rows_data[idx], idx)

    def _build_header(self):
        hdr_bg = ctk.CTkFrame(self._grid, fg_color=C["table_header"],
                              corner_radius=0, height=HDR_H)
        hdr_bg.grid(row=0, column=0, columnspan=len(self.columns), sticky="ew")
        for i, (key, label, _) in enumerate(self.columns):
            anchor = self._col_anchor(key)
            ctk.CTkLabel(
                self._grid,
                text=label.upper() if key != "_actions" else label,
                font=(FONT_LABEL[0], 9, "bold"),
                text_color=C["neutral_dark"],
                anchor=anchor,
                fg_color=C["table_header"],
            ).grid(row=0, column=i, sticky="ew", padx=self._cell_pad(key))

    def _make_pool_row(self, grid_row: int) -> dict:
        bg = C["card"]
        self._grid.grid_rowconfigure(grid_row, minsize=self.ROW_H, weight=0)
        bg_frame = ctk.CTkFrame(self._grid, fg_color=bg, corner_radius=0, height=self.ROW_H)
        bg_frame.grid(row=grid_row, column=0, columnspan=len(self.columns), sticky="ew")
        cells: list[tuple[str, ctk.CTkLabel]] = []
        for i, (key, _, _) in enumerate(self._data_cols):
            anchor = self._col_anchor(key)
            lbl = ctk.CTkLabel(
                self._grid, text="", font=FONT_SM, height=self.ROW_H,
                anchor=anchor, text_color=C["text"], fg_color=bg,
            )
            lbl.grid(row=grid_row, column=i, sticky="ew", padx=self._cell_pad(key))
            cells.append((key, lbl))
        entry: dict = {
            "grid_row": grid_row, "bg_frame": bg_frame, "cells": cells,
            "act_wrap": None, "menu": None, "idx": -1,
        }
        if self.row_actions:
            act_wrap = ctk.CTkFrame(self._grid, fg_color=bg, height=self.ROW_H)
            act_wrap.grid(row=grid_row, column=self._action_col, sticky="ew")
            menu = RowActionMenu(act_wrap, get_items=lambda e=entry: self._menu_items(e))
            menu.place(relx=0.5, rely=0.5, anchor="center")
            entry["act_wrap"] = act_wrap
            entry["menu"] = menu
        if not self.row_actions:
            self._bind_row_click(entry)
        return entry

    def _bind_row_click(self, entry: dict):
        def _on_click(_e=None):
            if entry["idx"] >= 0:
                self._click(entry["idx"])

        entry["bg_frame"].configure(cursor="hand2")
        entry["bg_frame"].bind("<Button-1>", _on_click)
        for _, lbl in entry["cells"]:
            lbl.configure(cursor="hand2")
            lbl.bind("<Button-1>", _on_click)

    def _ensure_pool(self, n: int):
        while len(self._pool) < n:
            self._pool.append(self._make_pool_row(len(self._pool) + 1))

    def _hide_pool(self):
        for entry in self._pool:
            entry["bg_frame"].grid_remove()
            for _, lbl in entry["cells"]:
                lbl.grid_remove()
            if entry.get("act_wrap"):
                entry["act_wrap"].grid_remove()

    def _show_pool_row(self, entry: dict):
        grid_row = entry["grid_row"]
        entry["bg_frame"].grid(row=grid_row, column=0, columnspan=len(self.columns), sticky="ew")
        for i, (key, lbl) in enumerate(entry["cells"]):
            lbl.grid(row=grid_row, column=i, sticky="ew", padx=self._cell_pad(key))
        if entry.get("act_wrap"):
            entry["act_wrap"].grid(row=grid_row, column=self._action_col, sticky="ew")

    def _apply_row(self, idx: int, row: dict):
        entry = self._pool[idx]
        entry["idx"] = idx
        bg = C["card"]
        entry["bg_frame"].configure(fg_color=bg)
        labels = []
        for key, lbl in entry["cells"]:
            val_s = str(row.get(key, "") if isinstance(row, dict) else row[int(key)])
            lbl.configure(text=val_s, text_color=self._sem_color(val_s), fg_color=bg)
            labels.append(lbl)
        if entry.get("act_wrap"):
            entry["act_wrap"].configure(fg_color=bg)
        self._show_pool_row(entry)
        self._row_frames.append(entry["bg_frame"])
        self._row_cells.append(labels)

    @staticmethod
    def _row_fp(row) -> tuple:
        if not isinstance(row, dict):
            return (row,)
        return tuple((k, row[k]) for k in sorted(row.keys()) if k != "_raw")

    def _fingerprint(self, rows) -> tuple:
        return tuple(self._row_fp(r) for r in rows)

    def _update_cells(self, idx: int, row: dict):
        entry = self._pool[idx]
        entry["idx"] = idx
        bg = C["card"]
        for key, lbl in entry["cells"]:
            val_s = str(row.get(key, "") if isinstance(row, dict) else row[int(key)])
            lbl.configure(text=val_s, text_color=self._sem_color(val_s), fg_color=bg)

    def load(self, rows):
        self._cancel_batch()
        fp = self._fingerprint(rows)
        if fp == self._last_fp and self._pool:
            return

        n = len(rows)
        if (n == len(self._rows_data) == len(self._pool) and n > 0
                and not self._empty_lbl):
            self._rows_data = rows
            self._last_fp = fp
            for i, row in enumerate(rows):
                self._update_cells(i, row)
            return

        if self._empty_lbl:
            self._empty_lbl.destroy()
            self._empty_lbl = None
        self._hide_pool()
        self._rows_data = rows
        self._last_fp = fp
        self._row_frames.clear()
        self._row_cells.clear()
        self._selected = None

        if not rows:
            self._empty_lbl = ctk.CTkLabel(self, text="No hay registros",
                                            font=FONT_SM, text_color=C["text3"])
            self._empty_lbl.pack(pady=40, anchor="center")
            return

        self._batch_pos = 0
        if n <= self.BATCH_THRESHOLD:
            self._ensure_pool(n)
            for i, row in enumerate(rows):
                self._apply_row(i, row)
        else:
            self._batch_render()

    def _batch_render(self):
        start = self._batch_pos
        end = min(start + self.CHUNK_SIZE, len(self._rows_data))
        self._ensure_pool(end)
        for i in range(start, end):
            self._apply_row(i, self._rows_data[i])
        self._batch_pos = end
        if end < len(self._rows_data):
            self._batch_job = self.after(16, self._batch_render)
        else:
            self._batch_job = None

    @staticmethod
    def _sem_color(val: str) -> str:
        if "Pagado" in val or val == "Activo" or val.endswith("Activo"):
            return C["success"]
        if "Pendiente" in val:
            return C["warning"]
        if "Inactivo" in val or "Anulado" in val:
            return C["text3"]
        return C["text"]

    def _paint_row(self, idx, bg, sel=False):
        entry = self._pool[idx]
        entry["bg_frame"].configure(fg_color=bg)
        if entry.get("act_wrap"):
            entry["act_wrap"].configure(fg_color=bg)
        for j, lbl in enumerate(entry["cells"]):
            key = self._data_cols[j][0]
            val = self._rows_data[idx].get(key, "") if isinstance(
                self._rows_data[idx], dict) else ""
            color = C["table_sel_text"] if sel else self._sem_color(str(val))
            lbl.configure(fg_color=bg, text_color=color)

    def _click(self, idx):
        if self._selected is not None:
            self._paint_row(self._selected, C["card"])
        self._selected = idx
        self._paint_row(idx, C["table_sel"], sel=True)
        if self._select_cb:
            self._select_cb(idx, self._rows_data[idx])

    def _restore_row(self, idx):
        if idx >= len(self._row_frames):
            return
        self._paint_row(idx, C["card"])

    def deselect(self):
        if self._selected is not None:
            self._restore_row(self._selected)
        self._selected = None

    def bind_select(self, cb):
        self._select_cb = cb

    def get_selected(self):
        return self._rows_data[self._selected] if self._selected is not None else None

    def clear(self):
        self.load([])


class DataTable(_TableCore, ctk.CTkScrollableFrame):
    """Tabla con scroll (uso interno o listas sin paginar)."""

    def __init__(self, parent, columns, height=300, flat=True,
                 row_actions=None, **kw):
        super().__init__(parent, fg_color=C["card"] if flat else "transparent",
                         height=height,
                         scrollbar_button_color=C["elevated"],
                         scrollbar_button_hover_color=C["border"], **kw)
        self._init_table(columns, flat, row_actions)

    def destroy(self):
        self.cancel_load()
        super().destroy()


class StaticDataTable(_TableCore, ctk.CTkFrame):
    """Tabla fija sin barra de scroll — usada por PaginatedTable."""

    def __init__(self, parent, columns, height=300, flat=True,
                 row_actions=None, **kw):
        super().__init__(parent, fg_color=C["card"] if flat else "transparent",
                         height=height, corner_radius=0, **kw)
        self.pack_propagate(False)
        self._init_table(columns, flat, row_actions)

    def destroy(self):
        self.cancel_load()
        super().destroy()


# ── Tabla paginada (sin scroll interno) ───────────────────────────

class PaginatedTable(ctk.CTkFrame):
    """Lista con paginación: muestra N filas fijas y controles Anterior/Siguiente."""

    def __init__(self, parent, columns, page_size=10, row_actions=None, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self.page_size = page_size
        self._all_rows: list = []
        self._page = 0
        table_h = HDR_H + ROW_H * page_size
        self._tbl = StaticDataTable(self, columns, height=table_h, row_actions=row_actions)
        self._tbl.pack(fill="both", expand=True)

        nav = ctk.CTkFrame(self, fg_color="transparent", height=BTN_H + 4)
        nav.pack(fill="x", pady=(10, 0))
        nav.pack_propagate(False)
        self._info = ctk.CTkLabel(nav, text="", font=FONT_SM, text_color=C["text3"])
        self._info.pack(side="left")
        self._btn_next = btn(nav, "Siguiente", command=self._next, variant="ghost",
                             width=108, height=36)
        self._btn_next.pack(side="right")
        self._btn_prev = btn(nav, "Anterior", command=self._prev, variant="ghost",
                             width=108, height=36)
        self._btn_prev.pack(side="right", padx=(0, 8))

    @property
    def table(self) -> StaticDataTable:
        return self._tbl

    def cancel_load(self):
        self._tbl.cancel_load()

    def load(self, rows: list):
        self._all_rows = rows
        self._page = 0
        self._render()

    def _pages(self) -> int:
        n = len(self._all_rows)
        return max(1, (n + self.page_size - 1) // self.page_size)

    def _render(self):
        total = len(self._all_rows)
        pages = self._pages()
        self._page = max(0, min(self._page, pages - 1))
        start = self._page * self.page_size
        chunk = self._all_rows[start:start + self.page_size]
        self._tbl.load(chunk)
        if total == 0:
            self._info.configure(text="0 registros")
        else:
            end = min(start + self.page_size, total)
            self._info.configure(
                text=f"Registros {start + 1}–{end} de {total}  ·  Página {self._page + 1} de {pages}"
            )
        st = "disabled" if self._page <= 0 else "normal"
        self._btn_prev.configure(state=st)
        st = "disabled" if self._page >= pages - 1 else "normal"
        self._btn_next.configure(state=st)

    def _prev(self):
        if self._page > 0:
            self._page -= 1
            self._render()

    def _next(self):
        if self._page < self._pages() - 1:
            self._page += 1
            self._render()


# ── Modal base ────────────────────────────────────────────────────

class Modal(ctk.CTkToplevel):
    """Modal con cuerpo desplazable y pie fijo (botones siempre visibles)."""

    FIELD_W = 400
    BTN_CANCEL_W = 132
    BTN_ACTION_W = 172
    FOOTER_PAD = (PAD, PAD)

    def __init__(self, parent, title, width=480, height=540, accent=None):
        super().__init__(parent)
        self.title(title)
        self.configure(fg_color=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        self.lift()
        self.focus_force()
        self.bind("<Escape>", lambda _: self.destroy())

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{width}x{height}+{(sw-width)//2}+{(sh-height)//2}")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkFrame(self, height=4, fg_color=accent or C["red"],
                     corner_radius=0).grid(row=0, column=0, sticky="ew")

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=1, column=0, sticky="ew", padx=PAD, pady=(PAD_SM, 0))
        ctk.CTkLabel(hdr, text=title, font=(FONT_LABEL[0], 20, "bold"),
                     text_color=C["text"]).pack(anchor="w")
        ctk.CTkFrame(hdr, height=1, fg_color=C["border"],
                     corner_radius=0).pack(fill="x", pady=(8, 0))

        self.body = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C["elevated"],
            scrollbar_button_hover_color=C["border"],
        )
        self.body.grid(row=2, column=0, sticky="nsew", padx=PAD, pady=(8, 4))

        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.grid(row=3, column=0, sticky="ew", padx=self.FOOTER_PAD[0], pady=(0, self.FOOTER_PAD[1]))
        divider(foot, pady=(0, 8))
        self._err = ctk.CTkLabel(foot, text="", font=FONT_SM, text_color=C["red"],
                                 wraplength=self.FIELD_W)
        self._err.pack(fill="x", pady=(0, 4))
        self.btn_row = ctk.CTkFrame(foot, fg_color="transparent")
        self.btn_row.pack(fill="x")

    def field_label(self, text, row=0, col=0):
        ctk.CTkLabel(self.body, text=text.upper(),
                     font=(FONT_LABEL[0], 9, "bold"),
                     text_color=C["text3"]).grid(
            row=row, column=col, sticky="w", pady=(12, 3))

    def set_error(self, msg):
        self._err.configure(text=msg)

    def clear_error(self):
        self._err.configure(text="")

    def set_buttons(self, specs, align="center"):
        for w in self.btn_row.winfo_children():
            w.destroy()
        btn_row(self.btn_row, specs, align=align)

    def add_buttons(self, save_text="Guardar", save_cmd=None,
                    cancel_cmd=None, variant="primary"):
        self.set_buttons([
            ("Cancelar", cancel_cmd or self.destroy, "ghost", self.BTN_CANCEL_W),
            (save_text, save_cmd, variant, self.BTN_ACTION_W),
        ], align="center")


# ── MetricCards ──────────────────────────────────────────────────

class MetricCards(ctk.CTkFrame):
    """KPI cards minimalistas con barra de acento lateral."""

    CARD_HEIGHT = 86

    def __init__(self, parent, metrics, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._labels = {}
        for i in range(len(metrics)):
            self.columnconfigure(i, weight=1)
        for i, m in enumerate(metrics):
            label, value, color = m[0], m[1], m[2]
            on_click = m[3] if len(m) > 3 else None
            self._make_card(label, value, color, i, last=(i == len(metrics) - 1),
                            on_click=on_click)

    def _make_card(self, label, value, color, col, last=False, on_click=None):
        padx = (0, 0) if last else (0, 12)
        card = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=R_LG,
                            border_width=1, border_color=C["border"],
                            height=self.CARD_HEIGHT)
        card.grid(row=0, column=col, padx=padx, pady=4, sticky="nsew")
        card.grid_propagate(False)

        # Acento lateral
        ACCENT_H = self.CARD_HEIGHT - 28
        accent = ctk.CTkFrame(card, fg_color=color, corner_radius=0,
                              width=3, height=ACCENT_H)
        accent.place(x=0, y=14)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=(16, 14), pady=14)
        ctk.CTkLabel(inner, text=label.upper(),
                     font=(FONT_LABEL[0], 10, "bold"),
                     text_color=C["text3"], anchor="w").pack(anchor="w")
        val_lbl = ctk.CTkLabel(inner, text=str(value),
                                font=(FONT_LABEL[0], 24, "bold"),
                                text_color=C["text"], anchor="w")
        val_lbl.pack(anchor="w", pady=(2, 0))
        self._labels[label] = val_lbl
        if on_click:
            for w in (card, inner, val_lbl):
                w.configure(cursor="hand2")
                w.bind("<Button-1>", lambda _e, cmd=on_click: cmd())
            ctk.CTkLabel(inner, text="Ver detalle →", font=FONT_XS,
                         text_color=C["text3"]).pack(anchor="w", pady=(4, 0))

    def update(self, label, value):
        if label in self._labels:
            self._labels[label].configure(text=str(value))


# ── Internals para dibujado de líneas ─────────────────────────────

def _pale(hex_color):
    """Versión muy clara del color para el área rellena de gráficas."""
    if hex_color in (C["red"], C["accent"], C["metric_1"], C["metric_4"]):
        return C["red_subtle"]
    return C["neutral_bg"]


def _format_label(label):
    if len(label) == 10 and label.count("-") == 2:
        from datetime import datetime
        try:
            d = datetime.strptime(label, "%Y-%m-%d")
            meses = ["Ene","Feb","Mar","Abr","May","Jun",
                     "Jul","Ago","Sep","Oct","Nov","Dic"]
            return f"{d.day:02d} {meses[d.month-1]} {d.year}"
        except ValueError:
            pass
    if label.startswith("#"):
        return f"Transacción {label}"
    return label


def _short_x_label(lbl):
    if len(lbl) == 10 and lbl.count("-") == 2:
        return lbl[5:]
    if lbl.startswith("#"):
        return lbl
    return lbl[:8]


class _ChartRenderer:
    """
    Lógica de dibujado compartida. Una instancia maneja un Canvas, los datos
    y el hover state. ChartCard la usa internamente.
    """

    HIT_RADIUS = 18

    def __init__(self, canvas, parent_widget, line_color, formatter,
                 height=200):
        self.canvas = canvas
        self.parent = parent_widget  # para Tooltip
        self.line_color = line_color
        self.fill_color = _pale(line_color)
        self.formatter = formatter
        self.height = height
        self.data = []        # list of (label, value)
        self.pts = []         # list of (x, y) screen coords
        self.tooltip = Tooltip(parent_widget)
        self.hover_idx = None

        canvas.bind("<Configure>", lambda _: self.redraw())
        canvas.bind("<Motion>",    self._on_motion)
        canvas.bind("<Leave>",     lambda _: self._unhover())

    def set_data(self, data):
        self.data = data
        self.redraw()

    def redraw(self):
        c = self.canvas
        c.delete("all")
        self.pts.clear()

        H = c.winfo_height() or self.height
        W = c.winfo_width() or 600

        if not self.data:
            c.create_text(W // 2, H // 2, text="Sin datos suficientes",
                          fill=C["text3"], font=(FONT_LABEL[0], 11))
            return

        PAD_L, PAD_R, PAD_T, PAD_B = 58, 18, 16, 30
        values = [v for _, v in self.data]
        labels = [l for l, _ in self.data]
        max_v = max(values) if max(values) > 0 else 1
        plot_w = W - PAD_L - PAD_R
        plot_h = H - PAD_T - PAD_B

        def x_pos(i):
            n = len(self.data)
            if n <= 1:
                return PAD_L + plot_w / 2
            return PAD_L + i * plot_w / (n - 1)

        def y_pos(v):
            return PAD_T + (1 - v / max_v) * plot_h

        # Cuadrícula
        for i in range(5):
            y = PAD_T + i * plot_h / 4
            c.create_line(PAD_L, y, W - PAD_R, y,
                          fill=C["border"], width=1, dash=(3, 4))
            val = max_v * (1 - i / 4)
            c.create_text(PAD_L - 8, y, text=self.formatter(val),
                          anchor="e", fill=C["text3"],
                          font=(FONT_LABEL[0], 9))

        # Eje base
        c.create_line(PAD_L, H - PAD_B, W - PAD_R, H - PAD_B,
                      fill=C["border"], width=1)

        # Puntos
        for i, v in enumerate(values):
            self.pts.append((x_pos(i), y_pos(v)))

        # Área rellena CORRECTA: del primer punto al baseline, sigue la línea, vuelve al baseline
        if len(self.pts) >= 2:
            baseline = H - PAD_B
            poly = [self.pts[0][0], baseline]
            for px, py in self.pts:
                poly.extend([px, py])
            poly.extend([self.pts[-1][0], baseline])
            c.create_polygon(poly, fill=self.fill_color, outline="")

            # Línea
            line_pts = [coord for p in self.pts for coord in p]
            c.create_line(line_pts, fill=self.line_color, width=2.5,
                          smooth=True, capstyle="round", joinstyle="round")
        elif len(self.pts) == 1:
            # Solo un punto: dibujar marca centrada sin área
            pass

        # Puntos visuales
        r = 4
        for px, py in self.pts:
            c.create_oval(px - r, py - r, px + r, py + r,
                          fill=C["card"], outline=self.line_color, width=2)

        # Etiquetas X
        n = len(labels)
        show_idx = {0, n - 1}
        if n > 6:
            show_idx |= {n // 4, n // 2, 3 * n // 4}
        elif n > 2:
            show_idx |= {n // 2}
        else:
            show_idx |= set(range(n))

        for i, lbl in enumerate(labels):
            if i in show_idx:
                c.create_text(x_pos(i), H - PAD_B + 14,
                              text=_short_x_label(lbl),
                              fill=C["text3"],
                              font=(FONT_LABEL[0], 9), anchor="center")

    def _on_motion(self, event):
        if not self.pts:
            return
        best_i, best_dist = None, self.HIT_RADIUS ** 2
        for i, (px, py) in enumerate(self.pts):
            d2 = (event.x - px) ** 2 + (event.y - py) ** 2
            if d2 < best_dist:
                best_dist, best_i = d2, i

        if best_i is None:
            self._unhover()
            return

        if best_i != self.hover_idx:
            self.hover_idx = best_i
            self._draw_highlight(best_i)

        label, value = self.data[best_i]
        abs_x = self.canvas.winfo_rootx() + event.x
        abs_y = self.canvas.winfo_rooty() + event.y
        self.tooltip.show(abs_x, abs_y,
                          _format_label(label),
                          self.formatter(value))

    def _unhover(self):
        if self.hover_idx is not None:
            self.hover_idx = None
            self.canvas.delete("highlight")
        self.tooltip.hide()

    def _draw_highlight(self, idx):
        self.canvas.delete("highlight")
        px, py = self.pts[idx]
        H = self.canvas.winfo_height() or self.height

        # Crosshair vertical
        self.canvas.create_line(
            px, 16, px, H - 30,
            fill=self.line_color, width=1, dash=(2, 3),
            tags="highlight")
        # Glow
        self.canvas.create_oval(
            px - 9, py - 9, px + 9, py + 9,
            fill=self.fill_color, outline="",
            tags="highlight")
        # Punto resaltado
        self.canvas.create_oval(
            px - 6, py - 6, px + 6, py + 6,
            fill=self.line_color, outline=C["card"],
            width=2, tags="highlight")

    def cleanup(self):
        try:
            self.tooltip.destroy()
        except Exception:
            pass


# ── LineChart (simple) ────────────────────────────────────────────

class LineChart(ctk.CTkFrame):
    """Gráfica simple sin switch de scope."""

    def __init__(self, parent, title, subtitle="",
                 line_color=None, value_formatter=None,
                 height=220, **kw):
        super().__init__(parent, fg_color=C["card"], corner_radius=R_LG,
                         border_width=1, border_color=C["border"], **kw)

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=PAD_SM, pady=(PAD_SM, 2))
        ctk.CTkLabel(hdr, text=title, font=FONT_SM_M,
                     text_color=C["text"]).pack(side="left")
        if subtitle:
            ctk.CTkLabel(hdr, text=f"  {subtitle}", font=FONT_XS,
                         text_color=C["text3"]).pack(side="left",
                                                      anchor="s", pady=2)

        canvas = tk.Canvas(self, height=height, bg=C["card"],
                            highlightthickness=0)
        canvas.pack(fill="x", padx=PAD_SM, pady=(0, PAD_SM))
        self._renderer = _ChartRenderer(
            canvas, self, line_color or C["red"],
            value_formatter or (lambda v: f"{v:,.0f}"),
            height=height)

    def set_data(self, points):
        self._renderer.set_data(points)

    def destroy(self):
        self._renderer.cleanup()
        super().destroy()


# ── ChartCard (con switch de scope) ───────────────────────────────

class ChartCard(ctk.CTkFrame):
    """
    Gráfica con switch de scope "Por día" / "Por transacción".
    on_scope_change(scope) se invoca al cambiar; scope ∈ {"day", "tx"}.
    """

    def __init__(self, parent, title, subtitle_day, subtitle_tx,
                 line_color=None, value_formatter=None,
                 height=200, on_scope_change=None, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._on_change = on_scope_change
        self._subtitles = {"day": subtitle_day, "tx": subtitle_tx}
        self._scope = "day"

        card_f = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=R_LG,
                              border_width=1, border_color=C["border"])
        card_f.pack(fill="both", expand=True)

        # Header
        hdr = ctk.CTkFrame(card_f, fg_color="transparent")
        hdr.pack(fill="x", padx=PAD_SM, pady=(PAD_SM, 4))
        ctk.CTkLabel(hdr, text=title, font=FONT_SM_M,
                     text_color=C["text"]).pack(side="left")
        self._sub_lbl = ctk.CTkLabel(hdr, text=f"  · {subtitle_day}",
                                      font=FONT_XS, text_color=C["text3"])
        self._sub_lbl.pack(side="left", anchor="s", pady=2)

        # Switch
        switch = ctk.CTkFrame(hdr, fg_color=C["elevated"], corner_radius=R_MD)
        switch.pack(side="right")
        self._sw_btns = {}
        for key, lbl_text in [("day", "Por día"), ("tx", "Por transacción")]:
            b = ctk.CTkButton(
                switch, text=lbl_text,
                fg_color="transparent", hover_color=C["card"],
                text_color=C["text2"], font=(FONT_LABEL[0], 10, "bold"),
                corner_radius=R_MD, height=30, width=112,
                command=lambda k=key: self._switch(k))
            b.pack(side="left", padx=4, pady=4)
            self._sw_btns[key] = b
        self._sw_btns["day"].configure(fg_color=C["red_light"], text_color=C["red"])

        canvas = tk.Canvas(card_f, height=height, bg=C["card"],
                            highlightthickness=0)
        canvas.pack(fill="x", padx=PAD_SM, pady=(0, PAD_SM))
        self._renderer = _ChartRenderer(
            canvas, self, line_color or C["red"],
            value_formatter or (lambda v: f"{v:,.0f}"),
            height=height)

    def _switch(self, scope):
        if scope == self._scope:
            return
        self._scope = scope
        for k, b in self._sw_btns.items():
            if k == scope:
                b.configure(fg_color=C["red_light"], text_color=C["red"])
            else:
                b.configure(fg_color="transparent", text_color=C["text2"])
        self._sub_lbl.configure(text=f"  · {self._subtitles[scope]}")
        if self._on_change:
            self._on_change(scope)

    def set_data(self, points):
        self._renderer.set_data(points)

    @property
    def scope(self):
        return self._scope

    def destroy(self):
        self._renderer.cleanup()
        super().destroy()
