"""Formulario amplio: despacho de combustible (pasos guiados)."""
from __future__ import annotations
import customtkinter as ctk
from core.business import METODOS_SIN_REFERENCIA
from core.theme import C, FONT_BODY, FONT_SM, FONT_SM_M, R_MD, BTN_H
from ui.forms.page import FormPage
from ui.forms import fields as F
from ui.components.widgets import btn


class DespachoFormPage(FormPage):
    STEPS = ("Beneficiario", "Combustible", "Pago")

    def __init__(self, parent, db, user, app, on_done, on_cancel, on_new_beneficiario=None):
        self.db, self.user, self.app = db, user, app
        self.on_done = on_done
        self._on_new_beneficiario = on_new_beneficiario
        self._step = 0
        super().__init__(
            parent,
            "Nuevo despacho",
            on_cancel=on_cancel,
            save_text="Registrar despacho",
            on_save=self._save,
        )
        self._bens = db.get_beneficiarios(solo_activos=True)
        self._invs = db.get_inventario(solo_activos=True)
        self._moneda = db.get_all_config().get("moneda", "Bs")
        self._metodos = {m["nombre"]: m["id"] for m in db.get_metodos_pago()}
        self._ben_labels: list[str] = []
        self._ben_map: dict[str, int] = {}
        self._inv_map: dict[str, tuple] = {}

        for w in (self._col0, self._col1, self._full):
            w.pack_forget()
        self._col0.master.pack_forget()

        self._step_bar = ctk.CTkFrame(self.full_width, fg_color="transparent")
        self._step_bar.pack(fill="x", pady=(0, 12))
        self._step_lbls: list[ctk.CTkLabel] = []
        for i, name in enumerate(self.STEPS):
            chip = ctk.CTkFrame(self._step_bar, fg_color=C["elevated"],
                                corner_radius=R_MD, height=36)
            chip.pack(side="left", padx=(0, 8))
            chip.pack_propagate(False)
            lbl = ctk.CTkLabel(chip, text=f"  {i + 1}. {name}  ", font=FONT_SM_M,
                               text_color=C["text3"])
            lbl.pack(padx=8, pady=6)
            self._step_lbls.append(lbl)

        self._body = ctk.CTkFrame(self.full_width, fg_color="transparent")
        self._body.pack(fill="both", expand=True)

        if not self._bens or not self._invs:
            msg = ("No hay beneficiarios activos."
                   if not self._bens else "No hay tipos de combustible activos.")
            ctk.CTkLabel(self._body, text=msg, font=FONT_BODY,
                         text_color=C["warning"]).pack(pady=40, anchor="center")
            self.set_actions([("Volver", self._cancel, "ghost", 140)])
            return

        self._rebuild_maps()
        self._show_step(0)

    def _rebuild_maps(self):
        self._bens = self.db.get_beneficiarios(solo_activos=True)
        self._ben_labels = [
            f"{b['cedula']} — {b['nombre']} {b['apellido']}" for b in self._bens
        ]
        self._ben_map = {lbl: b["id"] for lbl, b in zip(self._ben_labels, self._bens)}
        self._inv_map = {
            f"{i['tipo']} ({i['litros_actual']:,.0f} L)":
            (i["id"], i["litros_actual"], i["tipo"]) for i in self._invs
        }

    def _show_step(self, n: int):
        self._step = n
        self.clear_error()
        for i, lbl in enumerate(self._step_lbls):
            active = i == n
            chip = lbl.master
            chip.configure(fg_color=C["red_subtle"] if active else C["elevated"])
            lbl.configure(text_color=C["red"] if active else C["text3"])
        for w in self._body.winfo_children():
            w.destroy()
        if n == 0:
            self._build_step_beneficiario()
        elif n == 1:
            self._build_step_combustible()
        else:
            self._build_step_pago()
        self._update_nav()

    def _update_nav(self):
        if self._step == 0:
            self.set_actions([
                ("Cancelar", self._cancel, "ghost", 130),
                ("Siguiente", self._next, "primary", 160),
            ])
        elif self._step == 1:
            self.set_actions([
                ("Atrás", self._back, "ghost", 120),
                ("Siguiente", self._next, "primary", 160),
            ])
        else:
            self.set_actions([
                ("Atrás", self._back, "ghost", 120),
                ("Registrar despacho", self._save, "primary", 190),
            ])

    def _back(self):
        self._show_step(self._step - 1)

    def _next(self):
        if not self._validate_step():
            return
        self._show_step(self._step + 1)

    def _validate_step(self) -> bool:
        if self._step == 0:
            if self.c_ben.get().strip() not in self._ben_map:
                self.set_error("Seleccione un beneficiario.")
                return False
            return True
        if self._step == 1:
            try:
                litros = float(self.e_lit.get())
                assert litros > 0
            except Exception:
                self.set_error("Ingrese litros válidos (> 0).")
                return False
            _, disp, _ = self._inv_map[self.c_inv.get()]
            if litros > disp:
                self.set_error(f"Inventario insuficiente. Disponible: {disp:,.0f} L.")
                return False
            try:
                monto = float(self.e_mon.get() or 0)
                assert monto > 0
            except Exception:
                self.set_error("Ingrese un monto válido.")
                return False
            return True
        return True

    def _build_step_beneficiario(self):
        row = ctk.CTkFrame(self._body, fg_color="transparent")
        row.pack(fill="x")
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 14))
        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        self.e_buscar = F.label_entry(
            left, "Buscar", width=self.FIELD_W, ph="Cédula o nombre…",
        )
        self.e_buscar.bind("<KeyRelease>", self._filter_beneficiarios)
        self.c_ben = F.label_combo(left, "Beneficiario", self._ben_labels, width=self.FIELD_W)
        if self._on_new_beneficiario:
            btn(left, "Nuevo beneficiario", command=self._on_new_beneficiario,
                variant="secondary", width=self.FIELD_W, height=BTN_H).pack(pady=(14, 0))

        self._ben_preview = ctk.CTkFrame(right, fg_color=C["neutral_bg"],
                                         corner_radius=R_MD, border_width=1,
                                         border_color=C["border"])
        self._ben_preview.pack(fill="both", expand=True, pady=(28, 0))
        self._ben_lbl = ctk.CTkLabel(self._ben_preview, text="—",
                                      font=FONT_BODY, text_color=C["text3"],
                                      wraplength=300, justify="left")
        self._ben_lbl.pack(anchor="w", padx=14, pady=14)
        self.c_ben.configure(command=self._update_beneficiario_preview)
        self._update_beneficiario_preview()

    def _filter_beneficiarios(self, _e=None):
        q = self.e_buscar.get().strip().lower()
        opts = [l for l in self._ben_labels if not q or q in l.lower()]
        self.c_ben.configure(values=opts or ["—"])
        if opts:
            self.c_ben.set(opts[0])
        self._update_beneficiario_preview()

    def _update_beneficiario_preview(self, _c=None):
        sel = self.c_ben.get()
        ben = next((b for b in self._bens
                    if f"{b['cedula']} — {b['nombre']} {b['apellido']}" == sel), None)
        if not ben:
            self._ben_lbl.configure(text="—", text_color=C["text3"])
            return
        self._ben_lbl.configure(
            text=f"{ben['nombre']} {ben['apellido']}\n"
                 f"Cédula: {ben['cedula']}\n"
                 f"Embarcación: {ben['embarcacion'] or '—'}\n"
                 f"Motor: {ben['motor'] or '—'}",
            text_color=C["text"],
        )

    def _build_step_combustible(self):
        row = ctk.CTkFrame(self._body, fg_color="transparent")
        row.pack(fill="x")
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 14))
        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        self.c_inv = F.label_combo(left, "Tipo de combustible",
                                   list(self._inv_map.keys()), width=self.FIELD_W)
        self.c_inv.configure(command=self._on_combustible_change)
        self.e_lit = F.label_entry(left, "Litros a despachar", width=self.FIELD_W)
        self.e_lit.bind("<KeyRelease>", lambda _: self._recalc_monto())
        self.e_mon = F.label_entry(right, f"Monto ({self._moneda})", width=self.FIELD_W)
        self.e_obs = F.label_entry(right, "Observaciones (opcional)", width=self.FIELD_W)
        self._stock_lbl = ctk.CTkLabel(right, text="", font=FONT_SM, text_color=C["text3"])
        self._stock_lbl.pack(anchor="w", pady=(8, 0))
        self._on_combustible_change()

    def _on_combustible_change(self, _c=None):
        key = self.c_inv.get()
        if key not in self._inv_map:
            return
        _, disp, tipo = self._inv_map[key]
        precio = self.db.get_precio_litro(tipo)
        self._stock_lbl.configure(
            text=f"Disponible: {disp:,.0f} L · Precio: {precio:,.2f} {self._moneda}/L"
        )
        self._recalc_monto()

    def _recalc_monto(self):
        key = self.c_inv.get()
        if key not in self._inv_map:
            return
        _, _, tipo = self._inv_map[key]
        try:
            litros = float(self.e_lit.get() or 0)
        except ValueError:
            return
        precio = self.db.get_precio_litro(tipo)
        if precio > 0 and litros > 0:
            self.e_mon.delete(0, "end")
            self.e_mon.insert(0, f"{litros * precio:.2f}")

    def _build_step_pago(self):
        ben = self._ben_sel()
        _, _, tipo = self._inv_map[self.c_inv.get()]
        resumen = (
            f"Beneficiario: {ben['nombre']} {ben['apellido']} ({ben['cedula']})\n"
            f"{tipo} · {self.e_lit.get()} L · {self.e_mon.get()} {self._moneda}"
        )
        ctk.CTkLabel(self._body, text=resumen, font=FONT_BODY,
                     text_color=C["text"]).pack(anchor="w", pady=(0, 12))

        self._modo = ctk.StringVar(value="ahora")
        ctk.CTkRadioButton(
            self._body, text="Pago inmediato",
            variable=self._modo, value="ahora", command=self._toggle_pago,
            font=FONT_SM, text_color=C["text"],
            fg_color=C["red"], hover_color=C["red_hover"],
        ).pack(anchor="w", pady=4)
        ctk.CTkRadioButton(
            self._body, text="Pago pendiente (módulo Pagos)",
            variable=self._modo, value="despues", command=self._toggle_pago,
            font=FONT_SM, text_color=C["text"],
            fg_color=C["red"], hover_color=C["red_hover"],
        ).pack(anchor="w", pady=4)
        self._pago_box = ctk.CTkFrame(self._body, fg_color="transparent")
        self._toggle_pago()

    def _toggle_pago(self):
        for w in self._pago_box.winfo_children():
            w.destroy()
        if self._modo.get() != "ahora":
            self._pago_box.pack_forget()
            return
        self._pago_box.pack(fill="x", pady=(12, 0))
        row = ctk.CTkFrame(self._pago_box, fg_color="transparent")
        row.pack(fill="x")
        col_l = ctk.CTkFrame(row, fg_color="transparent")
        col_r = ctk.CTkFrame(row, fg_color="transparent")
        col_l.pack(side="left", fill="both", expand=True, padx=(0, self.COL_GAP // 2))
        col_r.pack(side="left", fill="both", expand=True, padx=(self.COL_GAP // 2, 0))
        self.c_met = F.label_combo(col_l, "Método de pago",
                                 list(self._metodos.keys()), width=self.FIELD_W)
        self.c_met.configure(command=self._on_metodo_change)
        self.e_ref = F.label_entry(col_r, "Referencia", width=self.FIELD_W)
        self._on_metodo_change()

    def _on_metodo_change(self, _c=None):
        if self.c_met.get() in METODOS_SIN_REFERENCIA:
            self.e_ref.delete(0, "end")
            self.e_ref.configure(placeholder_text="—")

    def _ben_sel(self):
        lbl = self.c_ben.get()
        bid = self._ben_map[lbl]
        return next(b for b in self._bens if b["id"] == bid)

    def _save(self):
        if not self._validate_step():
            return
        ben = self._ben_sel()
        inv_id, _, _ = self._inv_map[self.c_inv.get()]
        litros = float(self.e_lit.get())
        monto = float(self.e_mon.get())
        cobrar = self._modo.get() == "ahora"
        ref, met_id = "", None
        if cobrar:
            met_id = self._metodos[self.c_met.get()]
            ref = self.e_ref.get().strip()
        try:
            desp_id = self.db.registrar_venta(
                ben["id"], inv_id, litros, monto, self.user["nombre"],
                self.e_obs.get().strip(), cobrar_ahora=cobrar,
                referencia=ref, metodo_pago_id=met_id,
            )
        except ValueError as e:
            self.set_error(str(e))
            return
        self.db.log(self.user["id"], self.user["nombre"], "Despachos",
                    "Registrar", f"#{desp_id} · {litros:,.0f} L · {monto:,.2f} Bs")
        if cobrar:
            self.db.log(self.user["id"], self.user["nombre"], "Pagos",
                        "Registrar", f"Despacho #{desp_id}")
        self.on_done()
        self.app.toast("Despacho registrado" + (" y pagado" if cobrar else ""))
        if self.app and hasattr(self.app, "notify_data_changed"):
            self.app.notify_data_changed()
