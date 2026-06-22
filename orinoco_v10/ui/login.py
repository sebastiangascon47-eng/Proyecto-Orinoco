"""
login.py — Ventana de acceso v10
Panel oscuro + formulario claro. Incluye recuperación de contraseña.
"""
import customtkinter as ctk
from core.theme import C, FONT_SM, FONT_LABEL, R_LG
from ui.widgets import field, btn


class LoginWindow(ctk.CTk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title("Orinoco C.A.")
        self.configure(fg_color=C["sidebar"])
        self.resizable(False, False)
        w, h = 900, 560
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Panel izquierdo (branding)
        left = ctk.CTkFrame(self, fg_color=C["sidebar"], corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew")
        ctk.CTkFrame(left, width=4, fg_color=C["red"],
                     corner_radius=0).pack(side="left", fill="y")
        wrap = ctk.CTkFrame(left, fg_color="transparent")
        wrap.pack(expand=True, padx=48)
        ctk.CTkLabel(wrap, text="⛽", font=(FONT_LABEL[0], 80),
                     text_color=C["red"]).pack(pady=(0, 18))
        ctk.CTkLabel(wrap, text="ORINOCO", font=(FONT_LABEL[0], 26, "bold"),
                     text_color="#FFFFFF").pack()
        ctk.CTkLabel(wrap, text="Estación Fluvial · C.A.", font=(FONT_LABEL[0], 13),
                     text_color=C["text_sidebar2"]).pack(pady=(2, 0))
        ctk.CTkFrame(wrap, height=1, fg_color="#2D2D3E",
                     corner_radius=0).pack(fill="x", pady=30)
        for icon, text in [
            ("⛽", "Control de despacho de combustible"),
            ("👥", "Gestión de pescadores"),
            ("💳", "Seguimiento de pagos"),
            ("📊", "Reportes y bitácora de actividad"),
        ]:
            row = ctk.CTkFrame(wrap, fg_color="transparent")
            row.pack(anchor="w", pady=4)
            ctk.CTkLabel(row, text=icon, font=(FONT_LABEL[0], 14),
                         text_color=C["red"]).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(row, text=text, font=(FONT_LABEL[0], 11),
                         text_color="#9CA3AF").pack(side="left")
        ctk.CTkLabel(left, text="v10.0  ·  Sistema de Información",
                     font=(FONT_LABEL[0], 10), text_color="#3D3D55").pack(
            side="bottom", pady=20)

        # Panel derecho (formulario)
        right = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        form = ctk.CTkFrame(right, fg_color="transparent")
        form.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(form, text="Bienvenido", font=(FONT_LABEL[0], 30, "bold"),
                     text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(form, text="Inicia sesión para acceder al sistema",
                     font=(FONT_LABEL[0], 12), text_color=C["text3"]).pack(
            anchor="w", pady=(4, 30))

        for lbl_text, attr, ph, show_ in [
            ("USUARIO", "_user", "Nombre de usuario", ""),
            ("CONTRASEÑA", "_pwd", "••••••••", "•"),
        ]:
            ctk.CTkLabel(form, text=lbl_text, font=(FONT_LABEL[0], 9, "bold"),
                         text_color=C["text3"]).pack(anchor="w", pady=(0, 4))
            e = field(form, placeholder=ph, width=340, height=46, show=show_)
            e.pack(pady=(0, 18))
            setattr(self, attr, e)

        self._err = ctk.CTkLabel(form, text="", font=FONT_SM, text_color=C["red"])
        self._err.pack(anchor="w", pady=(0, 10))

        ctk.CTkButton(form, text="Entrar al sistema", command=self._login,
                      fg_color=C["red"], hover_color=C["red_hover"],
                      text_color="#FFFFFF", font=(FONT_LABEL[0], 13, "bold"),
                      height=48, width=340, corner_radius=R_LG).pack(fill="x")

        ctk.CTkButton(form, text="¿Olvidó su contraseña?", command=self._recuperar,
                      fg_color="transparent", hover_color=C["bg"],
                      text_color=C["text2"], font=(FONT_LABEL[0], 11),
                      height=30, width=340).pack(pady=(8, 0))
        ctk.CTkLabel(form, text="Credenciales por defecto: admin / admin123",
                     font=(FONT_LABEL[0], 10), text_color=C["text3"]).pack(
            anchor="w", pady=(8, 0))

        self.bind("<Return>", lambda _: self._login())
        self._user.focus_set()

    def _login(self):
        u = self._user.get().strip()
        p = self._pwd.get()
        if not u or not p:
            self._err.configure(text="⚠  Completa todos los campos.")
            return
        user = self.db.auth(u, p)
        if user:
            ud = dict(user)
            self.db.log(ud["id"], ud["nombre"], "Autenticación",
                        "Iniciar sesión", ud["usuario"])
            self.destroy()
            from ui.app import MainApp
            MainApp(self.db, ud).mainloop()
        else:
            self._err.configure(text="⚠  Usuario o contraseña incorrectos.")
            self._pwd.delete(0, "end")
            self._pwd.focus_set()

    def _recuperar(self):
        from ui.modals import RecuperarModal
        RecuperarModal(self, self.db)
