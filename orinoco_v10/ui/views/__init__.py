"""
Vistas del sistema — un módulo por pantalla (estilo sections/ de SISARAD).
"""
from ui.views.base import BaseView
from ui.views.dashboard import DashboardView
from ui.views.beneficiarios import BeneficiariosView
from ui.views.inventario import InventarioView
from ui.views.despacho import DespachoView
from ui.views.pagos import PagosView
from ui.views.reportes import ReportesView
from ui.views.operadores import OperadoresView
from ui.views.configuracion import ConfiguracionView
from ui.views.bitacora import BitacoraView
from ui.views.cuenta import CuentaView

VIEW_MAP = {
    "dashboard":     DashboardView,
    "beneficiarios": BeneficiariosView,
    "inventario":    InventarioView,
    "despacho":      DespachoView,
    "pagos":         PagosView,
    "reportes":      ReportesView,
    "operadores":    OperadoresView,
    "configuracion": ConfiguracionView,
    "bitacora":      BitacoraView,
    "cuenta":        CuentaView,
}

__all__ = [
    "BaseView", "VIEW_MAP",
    "DashboardView", "BeneficiariosView", "InventarioView", "DespachoView",
    "PagosView", "ReportesView", "OperadoresView", "ConfiguracionView",
    "BitacoraView", "CuentaView",
]
