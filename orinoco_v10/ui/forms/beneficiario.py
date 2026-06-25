"""Formulario amplio: beneficiario."""
from __future__ import annotations
from ui.forms.page import FormPage
from ui.forms import fields as F


class BeneficiarioFormPage(FormPage):
    def __init__(self, parent, db, user, app, on_done, on_cancel, registro=None):
        self.db, self.user, self.app = db, user, app
        self.on_done, self.reg = on_done, registro
        edit = registro is not None
        super().__init__(
            parent,
            "Editar beneficiario" if edit else "Nuevo beneficiario",
            on_cancel=on_cancel,
            save_text="Guardar cambios" if edit else "Registrar",
            on_save=self._save,
        )
        r = registro or {}
        w = self.FIELD_W
        self.e_ced = F.label_entry(self.col_left, "Cédula", r.get("cedula", ""), width=w,
                                   digits_only=True)
        self.e_nom = F.label_entry(self.col_left, "Nombre", r.get("nombre", ""), width=w)
        self.e_ape = F.label_entry(self.col_left, "Apellido", r.get("apellido", ""), width=w)
        self.e_tel = F.label_entry(self.col_left, "Teléfono", r.get("telefono", "") or "", width=w,
                                   phone=True)
        self.e_cor = F.label_entry(self.col_right, "Correo (opcional)", r.get("correo", "") or "", width=w)
        self.e_emb = F.label_entry(self.col_right, "Embarcación", r.get("embarcacion", "") or "", width=w)
        self.e_mot = F.label_entry(self.col_right, "Motor", r.get("motor", "") or "", width=w)

    def _save(self):
        ced = self.e_ced.get().strip()
        nom = self.e_nom.get().strip()
        ape = self.e_ape.get().strip()
        err = F.validate_cedula(ced)
        if err:
            self.set_error(err)
            return
        if not (nom and ape):
            self.set_error("Nombre y apellido son obligatorios.")
            return
        err = F.validate_phone(self.e_tel.get())
        if err:
            self.set_error(err)
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
                        "Registrar", f"{nom} {ape} ({ced})")
            msg = "Beneficiario registrado"
        self.on_done()
        self.app.toast(msg)
        if self.app and hasattr(self.app, "notify_data_changed"):
            self.app.notify_data_changed()
