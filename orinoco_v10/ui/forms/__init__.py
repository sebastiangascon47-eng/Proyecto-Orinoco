"""Vistas de formulario amplio (pantalla completa dentro del módulo)."""
from ui.forms.page import FormPage, FORM_FIELD_THRESHOLD
from ui.forms.beneficiario import BeneficiarioFormPage
from ui.forms.operador import OperadorFormPage
from ui.forms.despacho import DespachoFormPage

__all__ = [
    "FormPage", "FORM_FIELD_THRESHOLD",
    "BeneficiarioFormPage", "OperadorFormPage", "DespachoFormPage",
]
