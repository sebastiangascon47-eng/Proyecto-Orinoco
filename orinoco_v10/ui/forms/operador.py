"""Formulario amplio: operador."""
from __future__ import annotations
from core.catalogs import ROLES_OPERADOR, ROLE_LABEL_BY_VALUE, ROLE_VALUE_BY_LABEL
from ui.forms.page import FormPage
from ui.forms import fields as F


class OperadorFormPage(FormPage):
    def __init__(self, parent, db, user, app, on_done, on_cancel, registro=None):
        self.db, self.user, self.app = db, user, app
        self.on_done, self.reg = on_done, registro
        edit = registro is not None
        super().__init__(
            parent,
            "Editar operador" if edit else "Nuevo operador",
            subtitle="Cuenta de acceso y datos personales",
            on_cancel=on_cancel,
            save_text="Guardar cambios" if edit else "Registrar operador",
            on_save=self._save,
        )
        r = registro or {}
        w = self.FIELD_W
        self.e_usr = F.label_entry(self.col_left, "Usuario", r.get("usuario", ""), width=w)
        if edit:
            self.e_usr.configure(state="disabled")
        self.e_nom = F.label_entry(self.col_left, "Nombre", r.get("nombre", ""), width=w)
        self.e_ape = F.label_entry(self.col_left, "Apellido", r.get("apellido", "") or "", width=w)
        self.e_ced = F.label_entry(
            self.col_right, "Cédula", r.get("cedula", "") or "", width=w,
            digits_only=True, ph=f"{F.CEDULA_MIN_LEN}-{F.CEDULA_MAX_LEN} dígitos",
        )
        self.e_tel = F.label_entry(
            self.col_right, "Teléfono", r.get("telefono", "") or "", width=w,
            phone=True, ph=f"Ej. 04141234567 ({F.PHONE_MIN_DIGITS}-{F.PHONE_MAX_DIGITS} dígitos)",
        )
        rol_actual = ROLE_LABEL_BY_VALUE.get(r.get("rol", "operador"), "Operador")
        self.c_rol = F.label_combo(
            self.col_right, "Rol",
            [lbl for lbl, _ in ROLES_OPERADOR],
            value=rol_actual, width=w,
        )
        self.e_pwd = None
        if not edit:
            self.e_pwd = F.label_entry(self.col_right, "Contraseña inicial", show="•", width=w)

    def _save(self):
        usr = self.e_usr.get().strip()
        nom = self.e_nom.get().strip()
        rol = ROLE_VALUE_BY_LABEL[self.c_rol.get()]
        if not (usr and nom):
            self.set_error("Usuario y nombre son obligatorios.")
            return
        if " " in usr:
            self.set_error("El usuario no debe contener espacios.")
            return
        ced = self.e_ced.get().strip()
        err = F.validate_cedula(ced, required=False)
        if err:
            self.set_error(err)
            return
        err = F.validate_phone(self.e_tel.get())
        if err:
            self.set_error(err)
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
                        "Registrar", f"{usr} ({rol})")
            msg = "Operador registrado"
        self.on_done()
        self.app.toast(msg)
