"""
modals.py — Ventanas modales v10
Formularios CRUD, visor de detalle (paso previo obligatorio para borrar),
confirmaciones con motivo, y recuperación de contraseña.
"""
from __future__ import annotations
import customtkinter as ctk
from core.theme import C, FONT_BODY, FONT_SM, FONT_LABEL, FONT_XS, R_MD, PAD, PAD_SM
from core.catalogs import (
    TIPOS_COMBUSTIBLE, TIPO_COMBUSTIBLE_OTRO,
    MOTIVOS_REABASTECIMIENTO, MOTIVOS_AJUSTE,
)
from ui.components.widgets import Modal, btn, divider, btn_row
from ui.forms import fields as F


# ── aliases locales (modales cortos) ─────────────────────────────
MW = Modal.FIELD_W


def _entry(parent, value="", show="", ph="", width=MW):
    return F.entry(parent, value=value, show=show, ph=ph, width=width)


def _combo(parent, values, value=None, state="normal", width=MW):
    return F.combo(parent, values, value=value, state=state, width=width)


def _label_entry(parent, label, value="", show="", width=MW, ph=""):
    return F.label_entry(parent, label, value=value, show=show, width=width, ph=ph)


def _label_combo(parent, label, values, value=None, state="normal", width=MW):
    return F.label_combo(parent, label, values, value=value, state=state, width=width)


_lbl = F.lbl


def _money(v) -> str:
    try:
        return f"{float(v):,.2f}"
    except Exception:
        return str(v)


# ════════════════════ VISOR DE DETALLE ══════════════════════════
class DetailModal(Modal):
    """Muestra un registro en solo-lectura. Acciones (editar/borrar) van abajo."""
    def __init__(self, app, title, fields, actions=None, accent=None, badge=None):
        footer = 108
        h = min(640, 160 + len(fields) * 52 + (52 if badge else 0) + footer)
        super().__init__(app, title, width=480, height=h, accent=accent)
        if badge:
            chip = ctk.CTkFrame(self.body, fg_color=C["neutral_bg"],
                                border_width=1, border_color=C["border"],
                                corner_radius=R_MD)
            chip.pack(fill="x", pady=(8, 2))
            ctk.CTkLabel(chip, text=f"  {badge}", font=(FONT_LABEL[0], 12, "bold"),
                         text_color=C["neutral_dark"]).pack(anchor="w", padx=10, pady=8)
        for label, value in fields:
            _lbl(self.body, label)
            ctk.CTkLabel(self.body, text=str(value), font=FONT_BODY,
                         text_color=C["text"], anchor="w", justify="left",
                         wraplength=MW).pack(fill="x")
        if actions:
            specs = []
            for text, variant, cmd in actions:
                def _wrap(c=cmd):
                    self.destroy()
                    c()
                specs.append((text, _wrap, variant, 148))
            specs.append(("Cerrar", self.destroy, "ghost", Modal.BTN_CANCEL_W))
            self.set_buttons(specs, align="center")
        else:
            self.set_buttons([("Cerrar", self.destroy, "ghost", Modal.BTN_CANCEL_W)],
                             align="center")


# ════════════════════ CONFIRMACIÓN (con motivo) ═════════════════
class ConfirmModal(Modal):
    def __init__(self, app, title, message, on_confirm,
                 need_reason=False, confirm_text="Confirmar", variant="danger"):
        super().__init__(app, title, width=480,
                         height=320 if need_reason else 248, accent=C["red"])
        self._on_confirm = on_confirm
        self._need = need_reason
        ctk.CTkLabel(self.body, text=message, font=FONT_BODY, text_color=C["text"],
                     wraplength=MW, justify="left").pack(anchor="w", pady=(10, 4))
        self._reason = None
        if need_reason:
            _lbl(self.body, "Motivo")
            self._reason = _entry(self.body, ph="Indique el motivo")
        self.add_buttons(confirm_text, self._ok, variant=variant)

    def _ok(self):
        reason = self._reason.get().strip() if self._reason else ""
        if self._need and not reason:
            self.set_error("Debe indicar un motivo.")
            return
        self.destroy()
        self._on_confirm(reason)


# ════════════════════ OPERADORES (modal corto) ════════════════════
class ResetPasswordModal(Modal):
    def __init__(self, app, db, user, on_done, registro):
        self.app, self.db, self.user, self.on_done, self.reg = app, db, user, on_done, registro
        super().__init__(app, "Restablecer contraseña", width=480, height=300)
        ctk.CTkLabel(self.body, text=f"Operador: {registro['usuario']}",
                     font=FONT_BODY, text_color=C["text"]).pack(anchor="w", pady=(8, 2))
        self.e1 = _label_entry(self.body, "Nueva contraseña", show="•")
        self.add_buttons("Restablecer", self._save, variant="primary")

    def _save(self):
        p = self.e1.get()
        if len(p) < 4:
            self.set_error("Mínimo 4 caracteres.")
            return
        self.db.reset_password_operador(self.reg["id"], p)
        self.db.log(self.user["id"], self.user["nombre"], "Operadores",
                    "Restablecer contraseña", self.reg["usuario"])
        self.destroy(); self.on_done(); self.app.toast("Contraseña restablecida")


# ════════════════════ INVENTARIO (modales cortos) ═════════════════
class TipoCombustibleModal(Modal):
    def __init__(self, app, db, user, on_done, registro=None):
        self.app, self.db, self.user, self.on_done, self.reg = app, db, user, on_done, registro
        edit = registro is not None
        super().__init__(app, "Editar tipo de combustible" if edit else "Nuevo tipo de combustible",
                         width=480, height=520)
        r = dict(registro) if registro else {}
        self.e_tipo_otro = None
        self._otro_box = ctk.CTkFrame(self.body, fg_color="transparent")
        if edit:
            self.e_tipo = _label_entry(
                self.body, "Tipo de combustible", value=r.get("tipo", ""))
            self.c_tipo = None
            self._tipo_fijo = None
        else:
            self.e_tipo = None
            existentes = {i["tipo"] for i in db.get_inventario(solo_activos=False)}
            opciones = [t for t in TIPOS_COMBUSTIBLE if t not in existentes]
            opciones.append(TIPO_COMBUSTIBLE_OTRO)
            self.c_tipo = _label_combo(self.body, "Tipo de combustible", opciones)
            self.c_tipo.configure(command=self._on_tipo_sel)
            self._tipo_fijo = None
            if len(opciones) == 1:
                self._on_tipo_sel()
        self.e_cap = _label_entry(self.body, "Capacidad (litros)",
                                  r.get("capacidad", 20000))
        self.e_min = _label_entry(self.body, "Mínimo de alerta (litros)",
                                  r.get("minimo_alerta", 2000))
        self.add_buttons("Guardar" if edit else "Registrar", self._save, variant="primary")

    def _on_tipo_sel(self, _choice=None):
        if self.c_tipo.get() != TIPO_COMBUSTIBLE_OTRO:
            self._otro_box.pack_forget()
            return
        if self.e_tipo_otro is None:
            _lbl(self._otro_box, "Nombre personalizado")
            self.e_tipo_otro = _label_entry(self._otro_box, "Nombre del combustible")
        self._otro_box.pack(fill="x", pady=(0, 4))

    def _save(self):
        if self.reg and self.e_tipo is not None:
            tipo = self.e_tipo.get().strip()
        elif self._tipo_fijo:
            tipo = self._tipo_fijo
        elif self.c_tipo and self.c_tipo.get() == TIPO_COMBUSTIBLE_OTRO:
            tipo = (self.e_tipo_otro.get().strip() if self.e_tipo_otro else "")
            if not tipo:
                self.set_error("Indique el nombre del nuevo tipo de combustible.")
                return
        elif self.c_tipo:
            tipo = self.c_tipo.get().strip()
        else:
            tipo = ""
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
                        "Registrar tipo", tipo)
            msg = "Tipo de combustible registrado"
        self.destroy(); self.on_done(); self.app.toast(msg)


class DespachoEditModal(Modal):
    """Editar despacho pendiente de pago (litros, monto, observaciones)."""

    def __init__(self, app, db, user, on_done, despacho: dict):
        self.app, self.db, self.user, self.on_done, self.d = app, db, user, on_done, despacho
        super().__init__(app, f"Editar despacho #{despacho['id']}", width=480, height=460)
        ctk.CTkLabel(
            self.body,
            text=f"{despacho['beneficiario']} · {despacho['tipo']}",
            font=FONT_BODY, text_color=C["text"],
        ).pack(anchor="w", pady=(8, 4))
        self.e_lit = _label_entry(self.body, "Litros", value=despacho["litros"])
        self.e_mon = _label_entry(self.body, "Monto Bs", value=despacho["monto_bs"])
        self.e_obs = _label_entry(
            self.body, "Observaciones", value=despacho["observaciones"] or "")
        self.add_buttons("Guardar cambios", self._save, variant="primary")

    def _save(self):
        try:
            litros = float(self.e_lit.get())
            monto = float(self.e_mon.get())
            assert litros > 0 and monto >= 0
        except Exception:
            self.set_error("Litros y monto deben ser valores numéricos válidos.")
            return
        try:
            self.db.update_despacho_pendiente(
                self.d["id"], litros, monto, self.e_obs.get().strip(),
                self.user["nombre"],
            )
        except ValueError as e:
            self.set_error(str(e))
            return
        self.db.log(self.user["id"], self.user["nombre"], "Despachos",
                    "Editar", f"#{self.d['id']} · {litros:,.0f} L")
        self.destroy()
        self.on_done()
        self.app.toast("Despacho actualizado")


class ReabastecerModal(Modal):
    def __init__(self, app, db, user, on_done, inv):
        self.app, self.db, self.user, self.on_done, self.inv = app, db, user, on_done, inv
        super().__init__(app, "Reabastecer combustible", width=480, height=400)
        ctk.CTkLabel(self.body,
                     text=f"{inv['tipo']} · actual: {inv['litros_actual']:,.0f} L",
                     font=FONT_BODY, text_color=C["text"]).pack(anchor="w", pady=(8, 2))
        self.e = _label_entry(self.body, "Litros a agregar")
        self.c_mot = _label_combo(self.body, "Motivo", list(MOTIVOS_REABASTECIMIENTO))
        self.add_buttons("Reabastecer", self._save, variant="primary")

    def _save(self):
        try:
            litros = float(self.e.get())
            assert litros > 0
        except Exception:
            self.set_error("Ingrese una cantidad válida mayor a cero.")
            return
        self.db.reabastecer(self.inv["id"], litros, self.user["nombre"],
                            self.c_mot.get())
        self.db.log(self.user["id"], self.user["nombre"], "Inventario",
                    "Reabastecer", f"{self.inv['tipo']} +{litros:,.0f} L")
        self.destroy(); self.on_done(); self.app.toast("Inventario reabastecido")


class AjusteModal(Modal):
    def __init__(self, app, db, user, on_done, inv):
        self.app, self.db, self.user, self.on_done, self.inv = app, db, user, on_done, inv
        super().__init__(app, "Ajustar inventario", width=480, height=460)
        ctk.CTkLabel(self.body,
                     text=f"{inv['tipo']} · actual: {inv['litros_actual']:,.0f} L",
                     font=FONT_BODY, text_color=C["text"]).pack(anchor="w", pady=(8, 2))
        _lbl(self.body, "Operación")
        self.c_op = _combo(self.body, ["Agregar", "Restar"])
        self.e = _label_entry(self.body, "Litros")
        self.c_mot = _label_combo(self.body, "Motivo", list(MOTIVOS_AJUSTE))
        self.add_buttons("Aplicar ajuste", self._save, variant="primary")

    def _save(self):
        try:
            litros = float(self.e.get())
            assert litros > 0
        except Exception:
            self.set_error("Ingrese una cantidad válida mayor a cero.")
            return
        op = "add" if self.c_op.get() == "Agregar" else "sub"
        self.db.ajustar(self.inv["id"], litros, op, self.user["nombre"],
                        self.c_mot.get())
        self.db.log(self.user["id"], self.user["nombre"], "Inventario",
                    "Ajustar", f"{self.inv['tipo']} {self.c_op.get()} {litros:,.0f} L")
        self.destroy(); self.on_done(); self.app.toast("Ajuste aplicado")


# ════════════════════ PAGO (modal corto) ════════════════════════
class PagoModal(Modal):
    def __init__(self, app, db, user, on_done, despacho):
        self.app, self.db, self.user, self.on_done, self.d = app, db, user, on_done, despacho
        super().__init__(app, "Registrar pago", width=480, height=520)
        self._metodos = {m["nombre"]: m["id"] for m in db.get_metodos_pago()}
        ctk.CTkLabel(self.body,
                     text=f"Despacho #{despacho['id']} · {despacho['beneficiario']}",
                     font=FONT_BODY, text_color=C["text"]).pack(anchor="w", pady=(8, 0))
        ctk.CTkLabel(self.body, text=f"{despacho['litros']:,.0f} L · {despacho['tipo']}",
                     font=FONT_SM, text_color=C["text3"]).pack(anchor="w", pady=(0, 8))
        self.e_mon = _label_entry(self.body, "Monto a cobrar (Bs)",
                                  f"{despacho['monto_bs']:.2f}")
        self.c_met = _label_combo(self.body, "Método de pago", list(self._metodos.keys()))
        self.c_met.configure(command=self._on_metodo)
        self.e_ref = _label_entry(self.body, "Referencia")
        self._on_metodo()
        self.add_buttons("Registrar pago", self._save, variant="primary")

    def _on_metodo(self, _c=None):
        from core.business import METODOS_SIN_REFERENCIA
        if self.c_met.get() in METODOS_SIN_REFERENCIA:
            self.e_ref.delete(0, "end")
            self.e_ref.configure(placeholder_text="—")

    def _save(self):
        from core.business import METODOS_SIN_REFERENCIA
        try:
            monto = float(self.e_mon.get())
            assert monto > 0
        except Exception:
            self.set_error("Monto inválido.")
            return
        met = self.c_met.get()
        ref = self.e_ref.get().strip()
        if met not in METODOS_SIN_REFERENCIA and not ref:
            self.set_error("Indique la referencia del pago.")
            return
        if met in METODOS_SIN_REFERENCIA and not ref:
            ref = "Efectivo"
        met_id = self._metodos[met]
        self.db.add_pago(self.d["id"], self.d["beneficiario_id"], monto,
                         ref, met_id, self.user["nombre"])
        self.db.log(self.user["id"], self.user["nombre"], "Pagos",
                    "Registrar", f"Despacho #{self.d['id']} · {monto:,.2f} Bs")
        self.destroy(); self.on_done(); self.app.toast("Pago registrado")
        if self.app and hasattr(self.app, "notify_data_changed"):
            self.app.notify_data_changed()


# ════════════════════ CAMBIAR CONTRASEÑA (propia) ═══════════════
class CambiarPasswordModal(Modal):
    def __init__(self, app, db, user, on_done=None):
        self.app, self.db, self.user, self.on_done = app, db, user, on_done
        super().__init__(app, "Cambiar contraseña", width=480, height=440)
        self.e_act = _label_entry(self.body, "Contraseña actual", show="•")
        self.e_n1 = _label_entry(self.body, "Nueva contraseña", show="•")
        self.e_n2 = _label_entry(self.body, "Confirmar nueva contraseña", show="•")
        self.add_buttons("Actualizar", self._save, variant="primary")

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
        super().__init__(parent, "Recuperar contraseña", width=480, height=460)
        _lbl(self.body, "Usuario")
        self.e_usr = _entry(self.body, ph="Nombre de usuario")
        btn(self.body, "Buscar pregunta de seguridad", command=self._buscar,
            variant="secondary", width=MW, height=38).pack(pady=(10, 0))
        self._extra = ctk.CTkFrame(self.body, fg_color="transparent")
        self._extra.pack(fill="x")
        self.add_buttons("Restablecer", self._save, variant="primary")

    def _resize(self, h: int):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w = 480
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

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
                     text_color=C["text"], wraplength=MW).pack(anchor="w", pady=(14, 2))
        _lbl(self._extra, "Respuesta")
        self.e_resp = _entry(self._extra, ph="Su respuesta")
        _lbl(self._extra, "Nueva contraseña")
        self.e_pwd = _entry(self._extra, show="•")
        self._resize(560)

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

