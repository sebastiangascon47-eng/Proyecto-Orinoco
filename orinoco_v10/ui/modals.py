"""
modals.py — Ventanas modales v10
Formularios CRUD, visor de detalle (paso previo obligatorio para borrar),
confirmaciones con motivo, y recuperación de contraseña.
"""
from __future__ import annotations
import customtkinter as ctk
from core.theme import C, FONT_BODY, FONT_SM, FONT_LABEL, FONT_XS, R_MD, PAD, PAD_SM
from ui.widgets import Modal, field, dropdown, btn, divider


# ── helpers de formulario ────────────────────────────────────────
def _lbl(parent, text):
    ctk.CTkLabel(parent, text=text.upper(), font=(FONT_LABEL[0], 9, "bold"),
                 text_color=C["text3"]).pack(anchor="w", pady=(12, 3))


def _entry(parent, value="", show="", ph=""):
    e = field(parent, width=410, height=40, show=show, placeholder=ph)
    if value not in ("", None):
        e.insert(0, str(value))
    e.pack(fill="x")
    return e


def _combo(parent, values, value=None):
    d = dropdown(parent, values, width=410)
    if value is not None:
        d.set(value)
    elif values:
        d.set(values[0])
    d.pack(fill="x")
    return d


def _money(v) -> str:
    try:
        return f"{float(v):,.2f}"
    except Exception:
        return str(v)


# ════════════════════ VISOR DE DETALLE ══════════════════════════
class DetailModal(Modal):
    """Muestra un registro en solo-lectura. Acciones (editar/borrar) van abajo."""
    def __init__(self, app, title, fields, actions=None, accent=None, badge=None):
        h = min(620, 210 + len(fields) * 60 + (60 if badge else 0))
        super().__init__(app, title, width=480, height=h, accent=accent)
        if badge:
            chip = ctk.CTkFrame(self.body, fg_color=C["green_bg"],
                                border_width=1, border_color=C["green_border"],
                                corner_radius=R_MD)
            chip.pack(fill="x", pady=(8, 2))
            ctk.CTkLabel(chip, text=f"  🔒  {badge}", font=(FONT_LABEL[0], 12, "bold"),
                         text_color=C["green_dark"]).pack(anchor="w", padx=10, pady=8)
        for label, value in fields:
            _lbl(self.body, label)
            ctk.CTkLabel(self.body, text=str(value), font=FONT_BODY,
                         text_color=C["text"], anchor="w", justify="left",
                         wraplength=410).pack(fill="x")
        if actions:
            for text, variant, cmd in actions:
                def _wrap(c=cmd):
                    self.destroy(); c()
                btn(self.btn_row, text, command=_wrap, variant=variant,
                    width=150).pack(side="right", padx=(8, 0))
        btn(self.btn_row, "Cerrar", command=self.destroy,
            variant="ghost", width=100).pack(side="left")


# ════════════════════ CONFIRMACIÓN (con motivo) ═════════════════
class ConfirmModal(Modal):
    def __init__(self, app, title, message, on_confirm,
                 need_reason=False, confirm_text="Confirmar", variant="danger"):
        super().__init__(app, title, width=460, height=300 if need_reason else 230,
                         accent=C["red"])
        self._on_confirm = on_confirm
        self._need = need_reason
        ctk.CTkLabel(self.body, text=message, font=FONT_BODY, text_color=C["text"],
                     wraplength=410, justify="left").pack(anchor="w", pady=(10, 4))
        self._reason = None
        if need_reason:
            _lbl(self.body, "Motivo")
            self._reason = _entry(self.body, ph="Indique el motivo")
        btn(self.btn_row, "Cancelar", command=self.destroy,
            variant="ghost", width=110).pack(side="right", padx=(8, 0))
        btn(self.btn_row, confirm_text, command=self._ok,
            variant=variant, width=160).pack(side="right")

    def _ok(self):
        reason = self._reason.get().strip() if self._reason else ""
        if self._need and not reason:
            self.set_error("Debe indicar un motivo.")
            return
        self.destroy()
        self._on_confirm(reason)


# ════════════════════ BENEFICIARIOS ═════════════════════════════
class BeneficiarioModal(Modal):
    def __init__(self, app, db, user, on_done, registro=None):
        self.app, self.db, self.user = app, db, user
        self.on_done, self.reg = on_done, registro
        edit = registro is not None
        super().__init__(app, "Editar beneficiario" if edit else "Nuevo beneficiario",
                         width=480, height=620)
        r = registro or {}
        self.e_ced = _label_entry(self.body, "Cédula", r.get("cedula", ""))
        self.e_nom = _label_entry(self.body, "Nombre", r.get("nombre", ""))
        self.e_ape = _label_entry(self.body, "Apellido", r.get("apellido", ""))
        self.e_tel = _label_entry(self.body, "Teléfono", r.get("telefono", "") or "")
        self.e_cor = _label_entry(self.body, "Correo (opcional)", r.get("correo", "") or "")
        self.e_emb = _label_entry(self.body, "Embarcación", r.get("embarcacion", "") or "")
        self.e_mot = _label_entry(self.body, "Motor", r.get("motor", "") or "")
        self.add_buttons("Guardar cambios" if edit else "Registrar", self._save)

    def _save(self):
        ced = self.e_ced.get().strip()
        nom = self.e_nom.get().strip()
        ape = self.e_ape.get().strip()
        if not (ced and nom and ape):
            self.set_error("Cédula, nombre y apellido son obligatorios.")
            return
        existe = self.db.get_beneficiario_by_cedula(ced)
        if existe and (not self.reg or existe["id"] != self.reg["id"]):
            self.set_error("Ya existe un beneficiario con esa cédula.")
            return
        datos = (ced, nom, ape, self.e_tel.get().strip(),
                 self.e_emb.get().strip(), self.e_mot.get().strip(),
                 self.e_cor.get().strip())
        if self.reg:
            self.db.update_beneficiario(self.reg["id"], *datos)
            self.db.log(self.user["id"], self.user["nombre"], "Beneficiarios",
                        "Actualizar", f"{nom} {ape} ({ced})")
            msg = "Beneficiario actualizado"
        else:
            self.db.add_beneficiario(*datos)
            self.db.log(self.user["id"], self.user["nombre"], "Beneficiarios",
                        "Crear", f"{nom} {ape} ({ced})")
            msg = "Beneficiario registrado"
        self.destroy(); self.on_done(); self.app.toast(msg)


# ════════════════════ OPERADORES ════════════════════════════════
class OperadorModal(Modal):
    def __init__(self, app, db, user, on_done, registro=None):
        self.app, self.db, self.user = app, db, user
        self.on_done, self.reg = on_done, registro
        edit = registro is not None
        super().__init__(app, "Editar operador" if edit else "Nuevo operador",
                         width=480, height=640, accent=C["blue"])
        r = registro or {}
        self.e_usr = _label_entry(self.body, "Usuario", r.get("usuario", ""))
        if edit:
            self.e_usr.configure(state="disabled")
        self.e_nom = _label_entry(self.body, "Nombre", r.get("nombre", ""))
        self.e_ape = _label_entry(self.body, "Apellido", r.get("apellido", "") or "")
        self.e_ced = _label_entry(self.body, "Cédula", r.get("cedula", "") or "")
        self.e_tel = _label_entry(self.body, "Teléfono", r.get("telefono", "") or "")
        _lbl(self.body, "Rol")
        self.c_rol = _combo(self.body, ["operador", "administrador"],
                            r.get("rol", "operador"))
        if not edit:
            self.e_pwd = _label_entry(self.body, "Contraseña inicial", show="•")
        self.add_buttons("Guardar cambios" if edit else "Crear operador",
                         self._save, variant="blue")

    def _save(self):
        usr = self.e_usr.get().strip()
        nom = self.e_nom.get().strip()
        rol = self.c_rol.get()
        if not (usr and nom):
            self.set_error("Usuario y nombre son obligatorios.")
            return
        if " " in usr:
            self.set_error("El usuario no debe contener espacios.")
            return
        if self.reg:
            self.db.update_operador(self.reg["id"], nom, self.e_ape.get().strip(),
                                    self.e_ced.get().strip(),
                                    self.e_tel.get().strip(), rol)
            self.db.log(self.user["id"], self.user["nombre"], "Operadores",
                        "Actualizar", f"{usr} ({rol})")
            msg = "Operador actualizado"
        else:
            pwd = self.e_pwd.get()
            if len(pwd) < 4:
                self.set_error("La contraseña debe tener al menos 4 caracteres.")
                return
            if self.db.usuario_existe(usr):
                self.set_error("Ese usuario ya existe.")
                return
            self.db.add_operador(usr, pwd, nom, self.e_ape.get().strip(),
                                 self.e_ced.get().strip(),
                                 self.e_tel.get().strip(), rol)
            self.db.log(self.user["id"], self.user["nombre"], "Operadores",
                        "Crear", f"{usr} ({rol})")
            msg = "Operador creado"
        self.destroy(); self.on_done(); self.app.toast(msg)


class ResetPasswordModal(Modal):
    def __init__(self, app, db, user, on_done, registro):
        self.app, self.db, self.user, self.on_done, self.reg = app, db, user, on_done, registro
        super().__init__(app, "Restablecer contraseña", width=460, height=300,
                         accent=C["amber_dark"])
        ctk.CTkLabel(self.body, text=f"Operador: {registro['usuario']}",
                     font=FONT_BODY, text_color=C["text"]).pack(anchor="w", pady=(8, 2))
        self.e1 = _label_entry(self.body, "Nueva contraseña", show="•")
        self.add_buttons("Restablecer", self._save, variant="amber")

    def _save(self):
        p = self.e1.get()
        if len(p) < 4:
            self.set_error("Mínimo 4 caracteres.")
            return
        self.db.reset_password_operador(self.reg["id"], p)
        self.db.log(self.user["id"], self.user["nombre"], "Operadores",
                    "Restablecer contraseña", self.reg["usuario"])
        self.destroy(); self.on_done(); self.app.toast("Contraseña restablecida")


# ════════════════════ INVENTARIO ════════════════════════════════
class TipoCombustibleModal(Modal):
    def __init__(self, app, db, user, on_done, registro=None):
        self.app, self.db, self.user, self.on_done, self.reg = app, db, user, on_done, registro
        edit = registro is not None
        super().__init__(app, "Editar tipo de combustible" if edit else "Nuevo tipo de combustible",
                         width=470, height=440, accent=C["amber_dark"])
        r = registro or {}
        self.e_tipo = _label_entry(self.body, "Tipo / Nombre", r.get("tipo", ""))
        self.e_cap = _label_entry(self.body, "Capacidad (litros)",
                                  r.get("capacidad", 20000))
        self.e_min = _label_entry(self.body, "Mínimo de alerta (litros)",
                                  r.get("minimo_alerta", 2000))
        self.add_buttons("Guardar" if edit else "Crear", self._save, variant="amber")

    def _save(self):
        tipo = self.e_tipo.get().strip()
        if not tipo:
            self.set_error("El tipo es obligatorio.")
            return
        try:
            cap = float(self.e_cap.get() or 0)
            mn = float(self.e_min.get() or 0)
        except ValueError:
            self.set_error("Capacidad y mínimo deben ser numéricos.")
            return
        existe = self.db.get_inventario_by_tipo(tipo)
        if existe and (not self.reg or existe["id"] != self.reg["id"]):
            self.set_error("Ya existe ese tipo de combustible.")
            return
        if self.reg:
            self.db.update_tipo_combustible(self.reg["id"], tipo, cap, mn)
            self.db.log(self.user["id"], self.user["nombre"], "Inventario",
                        "Actualizar tipo", tipo)
            msg = "Tipo actualizado"
        else:
            self.db.add_tipo_combustible(tipo, cap, mn)
            self.db.log(self.user["id"], self.user["nombre"], "Inventario",
                        "Crear tipo", tipo)
            msg = "Tipo de combustible creado"
        self.destroy(); self.on_done(); self.app.toast(msg)


class ReabastecerModal(Modal):
    def __init__(self, app, db, user, on_done, inv):
        self.app, self.db, self.user, self.on_done, self.inv = app, db, user, on_done, inv
        super().__init__(app, "Reabastecer combustible", width=470, height=400,
                         accent=C["green_dark"])
        ctk.CTkLabel(self.body,
                     text=f"{inv['tipo']} · actual: {inv['litros_actual']:,.0f} L",
                     font=FONT_BODY, text_color=C["text"]).pack(anchor="w", pady=(8, 2))
        self.e = _label_entry(self.body, "Litros a agregar")
        self.e_mot = _label_entry(self.body, "Motivo / Nota", "Reabastecimiento")
        self.add_buttons("Reabastecer", self._save, variant="success")

    def _save(self):
        try:
            litros = float(self.e.get())
            assert litros > 0
        except Exception:
            self.set_error("Ingrese una cantidad válida mayor a cero.")
            return
        self.db.reabastecer(self.inv["id"], litros, self.user["nombre"],
                            self.e_mot.get().strip() or "Reabastecimiento")
        self.db.log(self.user["id"], self.user["nombre"], "Inventario",
                    "Reabastecer", f"{self.inv['tipo']} +{litros:,.0f} L")
        self.destroy(); self.on_done(); self.app.toast("Inventario reabastecido")


class AjusteModal(Modal):
    def __init__(self, app, db, user, on_done, inv):
        self.app, self.db, self.user, self.on_done, self.inv = app, db, user, on_done, inv
        super().__init__(app, "Ajustar inventario", width=470, height=440,
                         accent=C["amber_dark"])
        ctk.CTkLabel(self.body,
                     text=f"{inv['tipo']} · actual: {inv['litros_actual']:,.0f} L",
                     font=FONT_BODY, text_color=C["text"]).pack(anchor="w", pady=(8, 2))
        _lbl(self.body, "Operación")
        self.c_op = _combo(self.body, ["Agregar", "Restar"])
        self.e = _label_entry(self.body, "Litros")
        self.e_mot = _label_entry(self.body, "Motivo", "Ajuste manual")
        self.add_buttons("Aplicar ajuste", self._save, variant="amber")

    def _save(self):
        try:
            litros = float(self.e.get())
            assert litros > 0
        except Exception:
            self.set_error("Ingrese una cantidad válida mayor a cero.")
            return
        op = "add" if self.c_op.get() == "Agregar" else "sub"
        self.db.ajustar(self.inv["id"], litros, op, self.user["nombre"],
                        self.e_mot.get().strip() or "Ajuste manual")
        self.db.log(self.user["id"], self.user["nombre"], "Inventario",
                    "Ajustar", f"{self.inv['tipo']} {self.c_op.get()} {litros:,.0f} L")
        self.destroy(); self.on_done(); self.app.toast("Ajuste aplicado")


# ════════════════════ DESPACHO ══════════════════════════════════
class DespachoModal(Modal):
    def __init__(self, app, db, user, on_done):
        self.app, self.db, self.user, self.on_done = app, db, user, on_done
        super().__init__(app, "Nuevo despacho", width=500, height=680)
        bens = db.get_beneficiarios(solo_activos=True)
        invs = db.get_inventario(solo_activos=True)
        if not bens:
            ctk.CTkLabel(self.body, text="No hay beneficiarios activos registrados.",
                         font=FONT_BODY, text_color=C["amber"]).pack(pady=20)
            self.add_buttons("Cerrar", self.destroy, variant="ghost")
            return
        if not invs:
            ctk.CTkLabel(self.body, text="No hay tipos de combustible activos.",
                         font=FONT_BODY, text_color=C["amber"]).pack(pady=20)
            self.add_buttons("Cerrar", self.destroy, variant="ghost")
            return
        self._ben_map = {f"{b['cedula']} — {b['nombre']} {b['apellido']}": b["id"] for b in bens}
        self._inv_map = {f"{i['tipo']} ({i['litros_actual']:,.0f} L)":
                         (i["id"], i["litros_actual"]) for i in invs}
        self._metodos = {m["nombre"]: m["id"] for m in db.get_metodos_pago()}

        _lbl(self.body, "Beneficiario")
        self.c_ben = _combo(self.body, list(self._ben_map.keys()))
        _lbl(self.body, "Tipo de combustible")
        self.c_inv = _combo(self.body, list(self._inv_map.keys()))
        self.e_lit = _label_entry(self.body, "Litros a despachar")
        self.e_mon = _label_entry(self.body, "Monto (Bs)")
        self.e_obs = _label_entry(self.body, "Observaciones (opcional)")

        self._pago = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.body, text="Registrar pago inmediato",
                        variable=self._pago, command=self._toggle_pago,
                        font=FONT_SM, text_color=C["text"],
                        fg_color=C["red"], hover_color=C["red_hover"]).pack(anchor="w", pady=(14, 0))
        self._pago_box = ctk.CTkFrame(self.body, fg_color="transparent")
        self.add_buttons("Registrar despacho", self._save)

    def _toggle_pago(self):
        if self._pago.get():
            self._pago_box.pack(fill="x")
            _lbl(self._pago_box, "Referencia de pago")
            self.e_ref = _entry(self._pago_box, ph="N.° de referencia")
            _lbl(self._pago_box, "Método de pago")
            self.c_met = _combo(self._pago_box, list(self._metodos.keys()))
        else:
            for w in self._pago_box.winfo_children():
                w.destroy()
            self._pago_box.pack_forget()

    def _save(self):
        try:
            litros = float(self.e_lit.get())
            assert litros > 0
        except Exception:
            self.set_error("Ingrese litros válidos (> 0).")
            return
        try:
            monto = float(self.e_mon.get() or 0)
        except ValueError:
            self.set_error("Monto inválido.")
            return
        inv_id, disp = self._inv_map[self.c_inv.get()]
        if litros > disp:
            self.set_error(f"Inventario insuficiente. Disponible: {disp:,.0f} L.")
            return
        ben_id = self._ben_map[self.c_ben.get()]
        desp_id = self.db.add_despacho(ben_id, inv_id, litros, monto,
                                       self.user["nombre"], self.e_obs.get().strip())
        self.db.log(self.user["id"], self.user["nombre"], "Despachos",
                    "Registrar", f"#{desp_id} · {litros:,.0f} L · {monto:,.2f} Bs")
        if self._pago.get():
            ref = self.e_ref.get().strip()
            met_id = self._metodos[self.c_met.get()]
            if not ref:
                self.set_error("Indique la referencia del pago.")
                return
            self.db.add_pago(desp_id, ben_id, monto, ref, met_id, self.user["nombre"])
            self.db.log(self.user["id"], self.user["nombre"], "Pagos",
                        "Registrar", f"Despacho #{desp_id} · {monto:,.2f} Bs")
        self.destroy(); self.on_done()
        self.app.toast("Despacho registrado" + (" y pagado" if self._pago.get() else ""))


# ════════════════════ PAGO ══════════════════════════════════════
class PagoModal(Modal):
    def __init__(self, app, db, user, on_done, despacho):
        self.app, self.db, self.user, self.on_done, self.d = app, db, user, on_done, despacho
        super().__init__(app, "Registrar pago", width=480, height=480,
                         accent="#7C3AED")
        self._metodos = {m["nombre"]: m["id"] for m in db.get_metodos_pago()}
        ctk.CTkLabel(self.body,
                     text=f"Despacho #{despacho['id']} · {despacho['beneficiario']}",
                     font=FONT_BODY, text_color=C["text"]).pack(anchor="w", pady=(8, 0))
        ctk.CTkLabel(self.body, text=f"{despacho['litros']:,.0f} L · {despacho['tipo']}",
                     font=FONT_SM, text_color=C["text3"]).pack(anchor="w")
        self.e_mon = _label_entry(self.body, "Monto a cobrar (Bs)",
                                  f"{despacho['monto_bs']:.2f}")
        self.e_ref = _label_entry(self.body, "Referencia")
        _lbl(self.body, "Método de pago")
        self.c_met = _combo(self.body, list(self._metodos.keys()))
        self.add_buttons("Registrar pago", self._save, variant="primary")

    def _save(self):
        try:
            monto = float(self.e_mon.get())
            assert monto >= 0
        except Exception:
            self.set_error("Monto inválido.")
            return
        ref = self.e_ref.get().strip()
        if not ref:
            self.set_error("La referencia es obligatoria.")
            return
        met_id = self._metodos[self.c_met.get()]
        pid = self.db.add_pago(self.d["id"], self.d["beneficiario_id"], monto,
                               ref, met_id, self.user["nombre"])
        self.db.log(self.user["id"], self.user["nombre"], "Pagos",
                    "Registrar", f"Despacho #{self.d['id']} · {monto:,.2f} Bs")
        self.destroy(); self.on_done(); self.app.toast("Pago registrado")


# ════════════════════ CAMBIAR CONTRASEÑA (propia) ═══════════════
class CambiarPasswordModal(Modal):
    def __init__(self, app, db, user, on_done=None):
        self.app, self.db, self.user, self.on_done = app, db, user, on_done
        super().__init__(app, "Cambiar contraseña", width=460, height=400,
                         accent=C["blue"])
        self.e_act = _label_entry(self.body, "Contraseña actual", show="•")
        self.e_n1 = _label_entry(self.body, "Nueva contraseña", show="•")
        self.e_n2 = _label_entry(self.body, "Confirmar nueva contraseña", show="•")
        self.add_buttons("Actualizar", self._save, variant="blue")

    def _save(self):
        if not self.db.auth(self.user["usuario"], self.e_act.get()):
            self.set_error("La contraseña actual es incorrecta.")
            return
        n1, n2 = self.e_n1.get(), self.e_n2.get()
        if len(n1) < 4:
            self.set_error("La nueva contraseña debe tener al menos 4 caracteres.")
            return
        if n1 != n2:
            self.set_error("Las contraseñas no coinciden.")
            return
        self.db.change_password(self.user["id"], n1)
        self.db.log(self.user["id"], self.user["nombre"], "Cuenta",
                    "Cambiar contraseña", self.user["usuario"])
        self.destroy()
        if self.on_done:
            self.on_done()
        self.app.toast("Contraseña actualizada")


# ════════════════════ RECUPERAR CONTRASEÑA (login) ══════════════
class RecuperarModal(Modal):
    def __init__(self, parent, db):
        self.db = db
        super().__init__(parent, "Recuperar contraseña", width=460, height=440,
                         accent=C["amber_dark"])
        _lbl(self.body, "Usuario")
        self.e_usr = _entry(self.body, ph="Nombre de usuario")
        btn(self.body, "Buscar pregunta de seguridad", command=self._buscar,
            variant="secondary", width=410, height=38).pack(pady=(10, 0))
        self._extra = ctk.CTkFrame(self.body, fg_color="transparent")
        self._extra.pack(fill="x")
        self.add_buttons("Restablecer", self._save, variant="amber")

    def _buscar(self):
        for w in self._extra.winfo_children():
            w.destroy()
        usr = self.e_usr.get().strip()
        preg = self.db.get_pregunta(usr)
        if not preg:
            self.set_error("Usuario no encontrado.")
            return
        self.clear_error()
        ctk.CTkLabel(self._extra, text=preg, font=(FONT_LABEL[0], 12, "bold"),
                     text_color=C["text"], wraplength=410).pack(anchor="w", pady=(14, 2))
        _lbl(self._extra, "Respuesta")
        self.e_resp = _entry(self._extra, ph="Su respuesta")
        _lbl(self._extra, "Nueva contraseña")
        self.e_pwd = _entry(self._extra, show="•")

    def _save(self):
        usr = self.e_usr.get().strip()
        if not hasattr(self, "e_resp"):
            self.set_error("Primero busque su pregunta de seguridad.")
            return
        resp, pwd = self.e_resp.get(), self.e_pwd.get()
        if len(pwd) < 4:
            self.set_error("La nueva contraseña debe tener al menos 4 caracteres.")
            return
        if self.db.recuperar_password(usr, resp, pwd):
            self.destroy()
        else:
            self.set_error("Respuesta incorrecta.")


# ── helpers que combinan label + entry ───────────────────────────
def _label_entry(parent, label, value="", show=""):
    _lbl(parent, label)
    return _entry(parent, value=value, show=show)


def _lbl_above(modal, label, widget):
    """Inserta una etiqueta justo antes de un widget ya empaquetado (no-op visual)."""
    pass
