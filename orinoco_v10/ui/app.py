"""
app.py — Shell principal v10
Navegación por rol: el administrador ve módulos adicionales
(Operadores, Configuración, Bitácora).
"""
from __future__ import annotations
import importlib
import customtkinter as ctk
from tkinter import messagebox
from core.theme import C, FONT_LABEL, R_MD

# (icono, etiqueta, clave, solo_admin)
NAV_ITEMS = [
    ("🏠", "Inicio",        "dashboard",     False),
    ("👥", "Beneficiarios", "beneficiarios", False),
    ("🛢", "Inventario",    "inventario",    False),
    ("⛽", "Despacho",      "despacho",      False),
    ("💳", "Pagos",         "pagos",         False),
    ("📊", "Reportes",      "reportes",      False),
    ("🧑‍💼", "Operadores",   "operadores",    True),
    ("⚙️", "Configuración", "configuracion", True),
    ("📒", "Bitácora",      "bitacora",      True),
    ("👤", "Mi cuenta",     "cuenta",        False),
]

_VIEW_MAP = {
    "dashboard":     ("ui.views", "DashboardView"),
    "beneficiarios": ("ui.views", "BeneficiariosView"),
    "inventario":    ("ui.views", "InventarioView"),
    "despacho":      ("ui.views", "DespachoView"),
    "pagos":         ("ui.views", "PagosView"),
    "reportes":      ("ui.views", "ReportesView"),
    "operadores":    ("ui.views", "OperadoresView"),
    "configuracion": ("ui.views", "ConfiguracionView"),
    "bitacora":      ("ui.views", "BitacoraView"),
    "cuenta":        ("ui.views", "CuentaView"),
}


class MainApp(ctk.CTk):
    def __init__(self, db, user: dict):
        super().__init__()
        self.db = db
        self.user = user
        self.is_admin = user.get("rol") == "administrador"
        self.title("Estación Fluvial Orinoco C.A.")
        self.configure(fg_color=C["bg"])
        self.minsize(1100, 680)
        w, h = 1360, 840
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        self._nav_btns: dict[str, ctk.CTkButton] = {}
        self._indicators: dict[str, ctk.CTkFrame] = {}
        self._active_view: ctk.CTkFrame | None = None
        self._view_cache: dict[str, ctk.CTkFrame] = {}
        self._current: str | None = None

        self._build()
        self._navigate("dashboard")

    # ── Layout ────────────────────────────────────────────────────
    def _build(self):
        sidebar = ctk.CTkFrame(self, fg_color=C["sidebar"],
                               width=232, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent", height=64)
        brand.pack(fill="x")
        brand.pack_propagate(False)
        ctk.CTkFrame(brand, width=3, fg_color=C["red"],
                     corner_radius=0).pack(side="left", fill="y")
        bi = ctk.CTkFrame(brand, fg_color="transparent")
        bi.pack(side="left", padx=14)
        ctk.CTkLabel(bi, text="ORINOCO", font=(FONT_LABEL[0], 15, "bold"),
                     text_color="#FFFFFF").pack(anchor="w", pady=(14, 0))
        ctk.CTkLabel(bi, text="Estación Fluvial · v10", font=(FONT_LABEL[0], 10),
                     text_color=C["text_sidebar2"]).pack(anchor="w")

        ctk.CTkFrame(sidebar, height=1, fg_color="#252535",
                     corner_radius=0).pack(fill="x", padx=16, pady=(0, 6))

        admin_sep = False
        for icon, label, key, solo_admin in NAV_ITEMS:
            if solo_admin and not self.is_admin:
                continue
            if solo_admin and not admin_sep:
                ctk.CTkLabel(sidebar, text="  ADMINISTRACIÓN",
                             font=(FONT_LABEL[0], 9, "bold"),
                             text_color=C["text_sidebar2"]).pack(anchor="w",
                                                                 padx=16, pady=(8, 2))
                admin_sep = True
            self._add_nav_item(sidebar, icon, label, key)

        ctk.CTkFrame(sidebar, height=1, fg_color="#252535",
                     corner_radius=0).pack(fill="x", padx=16, pady=(10, 4))
        rol = "Administrador" if self.is_admin else "Operador"
        ctk.CTkLabel(sidebar, text=f"  {self.user.get('nombre','—')}  ·  {rol}",
                     font=(FONT_LABEL[0], 11), text_color=C["text_sidebar2"]).pack(
            anchor="w", padx=16, pady=(2, 2))
        ctk.CTkButton(sidebar, text="  ⏻  Cerrar Sesión", fg_color="transparent",
                      hover_color="#2A1010", text_color="#F87171",
                      font=(FONT_LABEL[0], 11, "bold"), height=40,
                      corner_radius=R_MD, anchor="w",
                      command=self._logout).pack(fill="x", padx=10, pady=(0, 12))

        self._content = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

    def _add_nav_item(self, sidebar, icon, label, key):
        row = ctk.CTkFrame(sidebar, fg_color="transparent", height=44)
        row.pack(fill="x", padx=6, pady=1)
        row.pack_propagate(False)
        ind = ctk.CTkFrame(row, width=3, fg_color="transparent", corner_radius=2)
        ind.pack(side="left", fill="y", padx=(2, 0))
        b = ctk.CTkButton(row, text=f"  {icon}  {label}",
                          command=lambda k=key: self._navigate(k),
                          fg_color="transparent", hover_color=C["sidebar_hover"],
                          text_color=C["text_sidebar"], anchor="w",
                          font=(FONT_LABEL[0], 13, "bold"), height=40,
                          corner_radius=R_MD)
        b.pack(side="left", fill="x", expand=True)
        self._nav_btns[key] = b
        self._indicators[key] = ind

    # ── Navegación ────────────────────────────────────────────────
    def _navigate(self, section: str):
        if section == self._current:
            return
        if self._current:
            self._nav_btns[self._current].configure(
                fg_color="transparent", text_color=C["text_sidebar"])
            self._indicators[self._current].configure(fg_color="transparent")
        self._current = section
        self._nav_btns[section].configure(fg_color=C["sidebar_hover"],
                                          text_color="#FFFFFF")
        self._indicators[section].configure(fg_color=C["red"])

        if self._active_view:
            self._active_view.pack_forget()
        if section not in self._view_cache:
            mod_path, cls_name = _VIEW_MAP[section]
            mod = importlib.import_module(mod_path)
            self._view_cache[section] = getattr(mod, cls_name)(
                self._content, self.db, self.user,
                navigate=self._navigate, app=self)
        self._active_view = self._view_cache[section]
        self._active_view.pack(fill="both", expand=True)
        if hasattr(self._active_view, "_refresh"):
            self._active_view._refresh()

    def toast(self, message: str, kind: str = "success"):
        from ui.widgets import Toast
        Toast.show(self, message, kind)

    def _logout(self):
        if messagebox.askyesno("Cerrar sesión", "¿Confirmar cierre de sesión?",
                               icon="question"):
            self.db.log(self.user["id"], self.user["nombre"], "Autenticación",
                        "Cerrar sesión", self.user["usuario"])
            self.destroy()
