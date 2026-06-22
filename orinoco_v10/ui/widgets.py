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
    FONT_LABEL, R_MD, R_LG, PAD, PAD_SM,
)


# ── Inputs ────────────────────────────────────────────────────────

def field(parent, placeholder="", width=240, show="", height=38, **kw):
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
        dropdown_hover_color=C["blue_bg"],
        text_color=C["text"], font=FONT_BODY, corner_radius=R_MD, **kw,
    )


# ── Botones ───────────────────────────────────────────────────────

_VARIANTS = {
    "primary":    dict(fg_color=C["red"], hover_color=C["red_hover"], text_color="#FFFFFF"),
    "secondary":  dict(fg_color=C["elevated"], hover_color="#D1D5DB", text_color=C["text"]),
    "ghost":      dict(fg_color="transparent", hover_color=C["elevated"], text_color=C["text2"],
                       border_width=1, border_color=C["border"]),
    "success":    dict(fg_color=C["green_dark"], hover_color=C["green_hover"], text_color="#FFFFFF"),
    "danger":     dict(fg_color=C["red_light"], hover_color="#FEE2E2", text_color=C["red"],
                       border_width=1, border_color=C["red_mid"]),
    "amber":      dict(fg_color=C["amber_dark"], hover_color=C["amber_hover"], text_color="#FFFFFF"),
    "blue":       dict(fg_color=C["blue"], hover_color=C["blue_hover"], text_color="#FFFFFF"),
    "flat":       dict(fg_color="transparent", hover_color=C["elevated"], text_color=C["text2"]),
    "reactivate": dict(fg_color=C["green_bg"], hover_color="#DCFCE7", text_color=C["green_dark"],
                       border_width=1, border_color=C["green_border"]),
}


def btn(parent, text, command=None, variant="primary", width=130, height=36, **kw):
    p = dict(_VARIANTS.get(variant, _VARIANTS["primary"]))
    p.update(kw)
    return ctk.CTkButton(
        parent, text=text, command=command,
        width=width, height=height, corner_radius=R_MD,
        font=(FONT_LABEL[0], 11, "bold"), **p,
    )


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
        "success": (C["green_dark"], C["green_bg"],  C["green_border"]),
        "error":   (C["red"],        C["red_light"], C["red_mid"]),
        "info":    (C["blue"],       C["blue_bg"],   "#93C5FD"),
        "warning": (C["amber_dark"], C["amber_bg"],  C["amber_border"]),
    }
    _ICONS = {"success": "✓", "error": "✕", "info": "ℹ", "warning": "⚠"}

    # Stack global de toasts activos (para apilar verticalmente)
    _stack: list = []

    @classmethod
    def show(cls, root, message: str, kind: str = "success",
             duration: int = 2800):
        """
        root: la MainApp (ctk.CTk). El toast se coloca con .place() sobre ella.
        """
        fg, bg, border = cls._COLORS.get(kind, cls._COLORS["info"])
        icon = cls._ICONS.get(kind, "")

        # Frame flotante
        toast = ctk.CTkFrame(
            root, fg_color=bg, corner_radius=R_LG,
            border_width=1, border_color=border,
        )
        ctk.CTkLabel(
            toast, text=f"  {icon}  {message}  ",
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


# ── DataTable ─────────────────────────────────────────────────────

class DataTable(ctk.CTkScrollableFrame):
    """Tabla con selección y colores semánticos."""

    ROW_H = 36

    def __init__(self, parent, columns, height=300, **kw):
        super().__init__(parent, fg_color="transparent", height=height,
                         scrollbar_button_color=C["elevated"],
                         scrollbar_button_hover_color=C["border"], **kw)
        self.columns = columns
        self._rows_data = []
        self._row_frames = []
        self._row_cells = []
        self._selected = None
        self._select_cb = None
        self._empty_lbl = None
        self._build_header()
        self.bind("<Button-1>", lambda _: self.deselect())

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=C["table_header"],
                           corner_radius=0, height=34)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        for _, label, w in self.columns:
            ctk.CTkLabel(hdr, text=label.upper(),
                         font=(FONT_LABEL[0], 9, "bold"),
                         text_color=C["text3"], width=w, anchor="w"
                         ).pack(side="left", padx=(12, 0))

    def load(self, rows):
        if self._empty_lbl:
            self._empty_lbl.destroy()
            self._empty_lbl = None
        for rf in self._row_frames:
            rf.destroy()
        self._row_frames.clear()
        self._row_cells.clear()
        self._rows_data = rows
        self._selected = None

        for i, row in enumerate(rows):
            bg = C["card"] if i % 2 == 0 else C["table_alt"]
            rf = ctk.CTkFrame(self, fg_color=bg, corner_radius=0,
                              height=self.ROW_H, cursor="hand2")
            rf.pack(fill="x")
            rf.pack_propagate(False)
            cells = []
            for key, _, w in self.columns:
                val_s = str(row[key] if isinstance(row, dict) else row[int(key)])
                cell = ctk.CTkLabel(rf, text=val_s, font=FONT_SM,
                                    text_color=self._sem_color(val_s),
                                    width=w, anchor="w", cursor="hand2")
                cell.pack(side="left", padx=(12, 0))
                cell.bind("<Button-1>", lambda e, idx=i: self._click(idx))
                cells.append(cell)
            rf.bind("<Button-1>", lambda e, idx=i: self._click(idx))
            self._row_frames.append(rf)
            self._row_cells.append(cells)

        if not rows:
            self._empty_lbl = ctk.CTkLabel(self, text="Sin registros para mostrar",
                                            font=FONT_SM, text_color=C["text3"])
            self._empty_lbl.pack(pady=32)

    @staticmethod
    def _sem_color(val: str) -> str:
        if val.startswith("✓") or "Pagado" in val or "Activo" in val:
            return C["green"]
        if "⏳" in val or "Pendiente" in val or "Inactivo" in val or val.startswith("✗"):
            return C["amber"]
        return C["text"]

    def _click(self, idx):
        if self._selected is not None:
            self._restore_row(self._selected)
        self._selected = idx
        self._row_frames[idx].configure(fg_color=C["table_sel"])
        for cell in self._row_cells[idx]:
            cell.configure(fg_color=C["table_sel"], text_color=C["table_sel_text"])
        if self._select_cb:
            self._select_cb(idx, self._rows_data[idx])

    def _restore_row(self, idx):
        if idx >= len(self._row_frames):
            return
        bg = C["card"] if idx % 2 == 0 else C["table_alt"]
        self._row_frames[idx].configure(fg_color=bg)
        for j, cell in enumerate(self._row_cells[idx]):
            key = self.columns[j][0]
            val = self._rows_data[idx].get(key, "") if isinstance(
                self._rows_data[idx], dict) else ""
            cell.configure(fg_color=bg, text_color=self._sem_color(str(val)))

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


# ── Modal base ────────────────────────────────────────────────────

class Modal(ctk.CTkToplevel):
    def __init__(self, parent, title, width=480, height=540, accent=None):
        super().__init__(parent)
        self.title(title)
        self.configure(fg_color=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.bind("<Escape>", lambda _: self.destroy())

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{width}x{height}+{(sw-width)//2}+{(sh-height)//2}")

        ctk.CTkFrame(self, height=4, fg_color=accent or C["red"],
                     corner_radius=0).pack(fill="x")
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=PAD, pady=(PAD_SM, 0))
        ctk.CTkLabel(hdr, text=title, font=(FONT_LABEL[0], 20, "bold"),
                     text_color=C["text"]).pack(side="left")
        divider(self, padx=PAD, pady=(8, 0))

        self.body = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C["elevated"],
            scrollbar_button_hover_color=C["border"],
        )
        self.body.pack(fill="both", expand=True, padx=PAD, pady=(8, 0))

        self._err = ctk.CTkLabel(self, text="", font=FONT_SM, text_color=C["red"])
        self._err.pack(padx=PAD, anchor="w", pady=(2, 0))

        self.btn_row = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_row.pack(fill="x", padx=PAD, pady=(4, PAD_SM))

    def field_label(self, text, row=0, col=0):
        ctk.CTkLabel(self.body, text=text.upper(),
                     font=(FONT_LABEL[0], 9, "bold"),
                     text_color=C["text3"]).grid(
            row=row, column=col, sticky="w", pady=(12, 3))

    def set_error(self, msg):
        self._err.configure(text=f"  ⚠  {msg}")

    def clear_error(self):
        self._err.configure(text="")

    def add_buttons(self, save_text="Guardar", save_cmd=None,
                    cancel_cmd=None, variant="primary"):
        btn(self.btn_row, "Cancelar", command=cancel_cmd or self.destroy,
            variant="ghost", width=110).pack(side="right", padx=(8, 0))
        btn(self.btn_row, save_text, command=save_cmd,
            variant=variant, width=180).pack(side="right")


# ── MetricCards ──────────────────────────────────────────────────

class MetricCards(ctk.CTkFrame):
    """KPI cards minimalistas con barra de acento lateral."""

    CARD_HEIGHT = 86

    def __init__(self, parent, metrics, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._labels = {}
        for i in range(len(metrics)):
            self.columnconfigure(i, weight=1)
        for i, (label, value, color) in enumerate(metrics):
            self._make_card(label, value, color, i, last=(i == len(metrics) - 1))

    def _make_card(self, label, value, color, col, last=False):
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
                                text_color=color, anchor="w")
        val_lbl.pack(anchor="w", pady=(2, 0))
        self._labels[label] = val_lbl

    def update(self, label, value):
        if label in self._labels:
            self._labels[label].configure(text=str(value))


# ── Internals para dibujado de líneas ─────────────────────────────

def _pale(hex_color):
    """Versión muy clara del color para el área rellena."""
    MAP = {
        "#CC0000": "#FFEEEE",
        "#1D4ED8": "#EFF6FF",
        "#15803D": "#F0FDF4",
        "#B45309": "#FFFBEB",
        "#14532D": "#F0FDF4",
        "#7C3AED": "#F5F3FF",
    }
    return MAP.get(hex_color, "#F5F5F5")


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
                 line_color="#CC0000", value_formatter=None,
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
            canvas, self, line_color,
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
                 line_color="#CC0000", value_formatter=None,
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
                corner_radius=R_MD, height=26, width=100,
                command=lambda k=key: self._switch(k))
            b.pack(side="left", padx=3, pady=3)
            self._sw_btns[key] = b
        self._sw_btns["day"].configure(fg_color=C["card"], text_color=C["text"])

        canvas = tk.Canvas(card_f, height=height, bg=C["card"],
                            highlightthickness=0)
        canvas.pack(fill="x", padx=PAD_SM, pady=(0, PAD_SM))
        self._renderer = _ChartRenderer(
            canvas, self, line_color,
            value_formatter or (lambda v: f"{v:,.0f}"),
            height=height)

    def _switch(self, scope):
        if scope == self._scope:
            return
        self._scope = scope
        for k, b in self._sw_btns.items():
            if k == scope:
                b.configure(fg_color=C["card"], text_color=C["text"])
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
