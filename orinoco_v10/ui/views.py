"""
views.py — Vistas v10
Cada módulo: listar + clic en registro abre detalle; desde el detalle se
edita y (solo administrador) se borra/anula. Operador: crear/ver/editar.
"""
from __future__ import annotations
import csv
import os
from datetime import date, datetime, timedelta

import customtkinter as ctk
from core.theme import (C, FONT_H1, FONT_H2, FONT_H3, FONT_BODY, FONT_BODY_M,
                        FONT_SM, FONT_SM_M, FONT_XS, FONT_LABEL, R_LG, R_MD,
                        PAD, PAD_SM)
from ui.widgets import MetricCards, ChartCard, DataTable, btn, field, card, divider
from ui import modals


def _money(v) -> str:
    try:
        return f"{float(v):,.2f}"
    except Exception:
        return str(v)


def _stock_color(litros, minimo=2000) -> str:
    if litros <= minimo:
        return C["red"]
    if litros <= minimo * 2:
        return C["amber"]
    return C["green"]


class BaseView(ctk.CTkFrame):
    def __init__(self, parent, db, user, navigate=None, app=None):
        super().__init__(parent, fg_color=C["bg"])
        self.db = db
        self.user = user
        self.navigate = navigate
        self.app = app
        self.is_admin = user.get("rol") == "administrador"
        self._build()

    def _build(self):  # override
        pass

    def _refresh(self):  # override
        pass

    def _header(self, title, subtitle="", actions=None):
        h = ctk.CTkFrame(self, fg_color="transparent")
        h.pack(fill="x", padx=PAD, pady=(PAD, 6))
        left = ctk.CTkFrame(h, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text=title, font=FONT_H1, text_color=C["text"]).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(left, text=subtitle, font=FONT_SM,
                         text_color=C["text3"]).pack(anchor="w")
        if actions:
            for text, variant, cmd in reversed(actions):
                btn(h, text, command=cmd, variant=variant,
                    width=160, height=38).pack(side="right", padx=(8, 0))
        return h


# ════════════════════ DASHBOARD ═════════════════════════════════
class DashboardView(BaseView):
    def _build(self):
        self._header("Inicio", "Resumen del sistema",
                     actions=[("↺  Actualizar", "secondary", self._refresh)])
        self._cards = MetricCards(self, [
            ("Inventario disponible", "0 L", C["green"]),
            ("Despachado este mes", "0 L", C["blue"]),
            ("Beneficiarios activos", "0", C["green_dark"]),
            ("Pagos pendientes", "0", C["amber"]),
        ])
        self._cards.pack(fill="x", padx=PAD, pady=(2, 6))

        self._chart = ChartCard(self, "Litros despachados", "últimos 14 días",
                                 "últimos 20 despachos", line_color=C["red"],
                                 value_formatter=lambda v: f"{v:,.0f} L",
                                 on_scope_change=lambda s: self._load_chart(s))
        self._chart.pack(fill="x", padx=PAD, pady=6)

        lbl = ctk.CTkLabel(self, text="Despachos recientes", font=FONT_H3,
                           text_color=C["text"])
        lbl.pack(anchor="w", padx=PAD, pady=(8, 4))
        self._tbl = DataTable(self, [
            ("id", "#", 40), ("fecha", "Fecha", 130), ("beneficiario", "Beneficiario", 180),
            ("litros", "Litros", 90), ("tipo", "Tipo", 110), ("estado", "Estado", 110),
        ], height=230)
        self._tbl.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

    def _refresh(self):
        s = self.db.stats()
        self._cards.update("Inventario disponible", f"{s['stock']:,.0f} L")
        self._cards.update("Despachado este mes", f"{s['litros_mes']:,.0f} L")
        self._cards.update("Beneficiarios activos", str(s["ben_total"]))
        self._cards.update("Pagos pendientes", str(s["pendientes"]))
        self._load_chart(self._chart.scope)
        rows = [self._fmt(r) for r in self.db.get_despachos(limit=10)]
        self._tbl.load(rows)

    def _load_chart(self, scope):
        data = self.db.get_despachos_tx(20) if scope == "tx" else self.db.get_series_despachos(14)
        self._chart.set_data(data)

    @staticmethod
    def _fmt(r):
        estado = "✗ Anulado" if r["estado"] == "anulado" else (
            "✓ Pagado" if r["pagado"] else "⏳ Pendiente")
        return {"id": r["id"], "fecha": r["fecha"][:16],
                "beneficiario": r["beneficiario"], "litros": f"{r['litros']:,.0f} L",
                "tipo": r["tipo"], "estado": estado}


# ════════════════════ BENEFICIARIOS ═════════════════════════════
class BeneficiariosView(BaseView):
    def _build(self):
        self._header("Beneficiarios", "Pescadores afiliados (clic en un registro para ver detalle)",
                     actions=[("＋  Nuevo beneficiario", "primary", self._nuevo)])
        self._cards = MetricCards(self, [
            ("Total", "0", C["blue"]), ("Activos", "0", C["green"]),
            ("Inactivos", "0", C["amber"]), ("Con embarcación", "0", C["green_dark"]),
        ])
        self._cards.pack(fill="x", padx=PAD, pady=(2, 8))

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=PAD)
        self._search = field(bar, placeholder="Buscar por cédula, nombre o embarcación…",
                             width=380, height=40)
        self._search.pack(side="left")
        self._search.bind("<KeyRelease>", lambda _: self._refresh())
        self._ver_inact = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(bar, text="Ver inactivos", variable=self._ver_inact,
                        command=self._refresh, font=FONT_SM, text_color=C["text2"],
                        fg_color=C["red"], hover_color=C["red_hover"]).pack(side="left", padx=14)

        self._tbl = DataTable(self, [
            ("cedula", "Cédula", 110), ("nombre", "Nombre", 130),
            ("apellido", "Apellido", 130), ("embarcacion", "Embarcación", 150),
            ("telefono", "Teléfono", 130), ("estado", "Estado", 90),
        ], height=320)
        self._tbl.pack(fill="both", expand=True, padx=PAD, pady=(10, PAD))
        self._tbl.bind_select(self._detalle)

    def _refresh(self):
        st = self.db.stats_beneficiarios()
        self._cards.update("Total", str(st["total"]))
        self._cards.update("Activos", str(st["activos"]))
        self._cards.update("Inactivos", str(st["inactivos"]))
        self._cards.update("Con embarcación", str(st["con_embarcacion"]))
        solo = not self._ver_inact.get()
        term = self._search.get().strip()
        rows = (self.db.search_beneficiarios(term, solo) if term
                else self.db.get_beneficiarios(solo))
        self._tbl.load([{
            "cedula": r["cedula"], "nombre": r["nombre"], "apellido": r["apellido"],
            "embarcacion": r["embarcacion"] or "—", "telefono": r["telefono"] or "—",
            "estado": "Activo" if r["activo"] else "Inactivo", "_raw": r,
        } for r in rows])

    def _nuevo(self):
        modals.BeneficiarioModal(self.app, self.db, self.user, self._refresh)

    def _detalle(self, idx, row):
        r = row["_raw"]
        fields = [
            ("Cédula", r["cedula"]), ("Nombre", f"{r['nombre']} {r['apellido']}"),
            ("Teléfono", r["telefono"] or "—"), ("Correo", r["correo"] or "—"),
            ("Embarcación", r["embarcacion"] or "—"), ("Motor", r["motor"] or "—"),
            ("Estado", "Activo" if r["activo"] else "Inactivo"),
            ("Registrado", (r["creado_en"] or "")[:16]),
        ]
        actions = [("Editar", "blue", lambda: modals.BeneficiarioModal(
            self.app, self.db, self.user, self._refresh, dict(r)))]
        if self.is_admin:
            if r["activo"]:
                actions.append(("Dar de baja", "danger", lambda: self._baja(r, 0)))
            else:
                actions.append(("Reactivar", "reactivate", lambda: self._baja(r, 1)))
        modals.DetailModal(self.app, "Detalle del beneficiario", fields, actions)

    def _baja(self, r, activo):
        accion = "Reactivar" if activo else "Dar de baja"
        modals.ConfirmModal(
            self.app, f"{accion} beneficiario",
            f"¿Confirma {accion.lower()} a {r['nombre']} {r['apellido']}?",
            confirm_text=accion, variant="reactivate" if activo else "danger",
            on_confirm=lambda _: self._do_baja(r, activo))

    def _do_baja(self, r, activo):
        self.db.toggle_beneficiario(r["id"], activo)
        self.db.log(self.user["id"], self.user["nombre"], "Beneficiarios",
                    "Reactivar" if activo else "Dar de baja", f"{r['nombre']} {r['apellido']}")
        self._refresh()
        self.app.toast("Beneficiario " + ("reactivado" if activo else "dado de baja"))


# ════════════════════ INVENTARIO ════════════════════════════════
class InventarioView(BaseView):
    def _build(self):
        self._header("Inventario", "Combustible por tipo (clic en un tipo para gestionarlo)",
                     actions=[("＋  Nuevo tipo", "primary", self._nuevo)])
        self._cards = MetricCards(self, [
            ("Total disponible", "0 L", C["green"]),
            ("Tipos de combustible", "0", C["blue"]),
            ("Bajo el mínimo", "0", C["amber"]),
        ])
        self._cards.pack(fill="x", padx=PAD, pady=(2, 8))

        self._tbl = DataTable(self, [
            ("tipo", "Tipo", 160), ("litros", "Disponible", 130),
            ("capacidad", "Capacidad", 130), ("minimo", "Mínimo alerta", 130),
            ("estado", "Estado", 120),
        ], height=240)
        self._tbl.pack(fill="x", padx=PAD, pady=(0, 8))
        self._tbl.bind_select(self._detalle)

        ctk.CTkLabel(self, text="Últimos movimientos (kardex)", font=FONT_H3,
                     text_color=C["text"]).pack(anchor="w", padx=PAD, pady=(6, 4))
        self._mov = DataTable(self, [
            ("fecha", "Fecha", 130), ("tipo", "Tipo", 130), ("mov", "Movimiento", 110),
            ("litros", "Litros", 110), ("motivo", "Motivo", 200), ("operador", "Operador", 120),
        ], height=200)
        self._mov.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

    def _refresh(self):
        st = self.db.stats_inventario()
        self._cards.update("Total disponible", f"{st['total_litros']:,.0f} L")
        self._cards.update("Tipos de combustible", str(st["tipos"]))
        self._cards.update("Bajo el mínimo", str(st["bajo_minimo"]))
        self._tbl.load([{
            "tipo": r["tipo"], "litros": f"{r['litros_actual']:,.0f} L",
            "capacidad": f"{r['capacidad']:,.0f} L", "minimo": f"{r['minimo_alerta']:,.0f} L",
            "estado": ("Activo" if r["activo"] else "Inactivo") +
                      ("  ⚠" if r["activo"] and r["litros_actual"] <= r["minimo_alerta"] else ""),
            "_raw": r,
        } for r in self.db.get_inventario()])
        self._mov.load([{
            "fecha": m["fecha"][:16], "tipo": m["tipo"],
            "mov": m["tipo_movimiento"].capitalize(),
            "litros": f"{m['litros']:,.0f}", "motivo": m["motivo"] or "—",
            "operador": m["operador"] or "—",
        } for m in self.db.get_movimientos(limit=40)])

    def _nuevo(self):
        modals.TipoCombustibleModal(self.app, self.db, self.user, self._refresh)

    def _detalle(self, idx, row):
        r = row["_raw"]
        fields = [
            ("Tipo", r["tipo"]), ("Disponible", f"{r['litros_actual']:,.0f} L"),
            ("Capacidad", f"{r['capacidad']:,.0f} L"),
            ("Mínimo de alerta", f"{r['minimo_alerta']:,.0f} L"),
            ("Estado", "Activo" if r["activo"] else "Inactivo"),
            ("Actualizado", (r["actualizado_en"] or "")[:16]),
        ]
        actions = [
            ("Reabastecer", "success", lambda: modals.ReabastecerModal(
                self.app, self.db, self.user, self._refresh, dict(r))),
            ("Ajustar", "amber", lambda: modals.AjusteModal(
                self.app, self.db, self.user, self._refresh, dict(r))),
            ("Editar", "blue", lambda: modals.TipoCombustibleModal(
                self.app, self.db, self.user, self._refresh, dict(r))),
        ]
        if self.is_admin:
            actions.append(("Eliminar", "danger", lambda: self._eliminar(r)))
        modals.DetailModal(self.app, "Detalle de combustible", fields, actions,
                           accent=C["amber_dark"])

    def _eliminar(self, r):
        modals.ConfirmModal(
            self.app, "Eliminar tipo de combustible",
            f"¿Eliminar “{r['tipo']}”? Solo es posible si no tiene despachos asociados.",
            confirm_text="Eliminar", variant="danger",
            on_confirm=lambda _: self._do_eliminar(r))

    def _do_eliminar(self, r):
        if self.db.delete_tipo_combustible(r["id"]):
            self.db.log(self.user["id"], self.user["nombre"], "Inventario",
                        "Eliminar tipo", r["tipo"])
            self._refresh()
            self.app.toast("Tipo de combustible eliminado")
        else:
            self.app.toast("No se puede eliminar: tiene despachos asociados", "error")


# ════════════════════ DESPACHOS ═════════════════════════════════
class DespachoView(BaseView):
    def _build(self):
        self._header("Despacho de combustible",
                     "Clic en un despacho para ver su detalle",
                     actions=[("＋  Nuevo despacho", "primary", self._nuevo),
                              ("↺  Actualizar", "secondary", self._refresh)])
        self._cards = MetricCards(self, [
            ("Total despachos", "0", C["blue"]), ("Litros", "0", C["amber_dark"]),
            ("Pagados", "0", C["green"]), ("Pendientes", "0", C["amber"]),
            ("Recaudado Bs", "0", C["green_dark"]),
        ])
        self._cards.pack(fill="x", padx=PAD, pady=(2, 6))

        self._chart = ChartCard(self, "Litros despachados", "últimos 14 días",
                                 "últimos 20 despachos", line_color=C["blue"],
                                 value_formatter=lambda v: f"{v:,.0f} L",
                                 on_scope_change=lambda s: self._load_chart(s))
        self._chart.pack(fill="x", padx=PAD, pady=6)

        self._tbl = DataTable(self, [
            ("id", "#", 40), ("fecha", "Fecha", 120), ("cedula", "Cédula", 100),
            ("beneficiario", "Beneficiario", 160), ("litros", "Litros", 90),
            ("tipo", "Tipo", 100), ("monto", "Monto Bs", 100), ("estado", "Estado", 110),
        ], height=240)
        self._tbl.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))
        self._tbl.bind_select(self._detalle)

    def _refresh(self):
        st = self.db.stats_despachos()
        self._cards.update("Total despachos", str(st["n"]))
        self._cards.update("Litros", f"{st['litros']:,.0f}")
        self._cards.update("Pagados", str(st["pagados"]))
        self._cards.update("Pendientes", str(st["pendientes"]))
        self._cards.update("Recaudado Bs", f"{st['monto']:,.0f}")
        self._load_chart(self._chart.scope)
        self._tbl.load([self._fmt(r) for r in self.db.get_despachos(limit=300)])

    def _load_chart(self, scope):
        data = self.db.get_despachos_tx(20) if scope == "tx" else self.db.get_series_despachos(14)
        self._chart.set_data(data)

    @staticmethod
    def _fmt(r):
        estado = "✗ Anulado" if r["estado"] == "anulado" else (
            "✓ Pagado" if r["pagado"] else "⏳ Pendiente")
        return {"id": r["id"], "fecha": r["fecha"][:16], "cedula": r["cedula"],
                "beneficiario": r["beneficiario"], "litros": f"{r['litros']:,.0f} L",
                "tipo": r["tipo"], "monto": f"{r['monto_bs']:,.2f}", "estado": estado,
                "_raw": r}

    def _nuevo(self):
        modals.DespachoModal(self.app, self.db, self.user, self._refresh)

    def _detalle(self, idx, row):
        r = row["_raw"]
        estado = "Anulado" if r["estado"] == "anulado" else (
            "Pagado" if r["pagado"] else "Pendiente")
        fields = [
            ("Despacho", f"#{r['id']}"), ("Fecha", r["fecha"][:16]),
            ("Beneficiario", f"{r['beneficiario']} ({r['cedula']})"),
            ("Combustible", r["tipo"]), ("Litros", f"{r['litros']:,.0f} L"),
            ("Monto", f"{r['monto_bs']:,.2f} Bs"), ("Estado", estado),
            ("Operador", r["operador"]), ("Observaciones", r["observaciones"] or "—"),
        ]
        if r["estado"] == "anulado":
            fields.append(("Motivo de anulación", r["motivo_anulacion"] or "—"))
        actions = []
        if self.is_admin and r["estado"] != "anulado":
            actions.append(("Anular despacho", "danger", lambda: self._anular(r)))
        modals.DetailModal(self.app, "Detalle del despacho", fields, actions)

    def _anular(self, r):
        modals.ConfirmModal(
            self.app, "Anular despacho",
            f"¿Anular el despacho #{r['id']}? Se devolverán {r['litros']:,.0f} L al inventario.",
            need_reason=True, confirm_text="Anular", variant="danger",
            on_confirm=lambda motivo: self._do_anular(r, motivo))

    def _do_anular(self, r, motivo):
        self.db.anular_despacho(r["id"], motivo, self.user["nombre"])
        self.db.log(self.user["id"], self.user["nombre"], "Despachos",
                    "Anular", f"#{r['id']} — {motivo}")
        self._refresh()
        self.app.toast("Despacho anulado")


# ════════════════════ PAGOS ═════════════════════════════════════
class PagosView(BaseView):
    def _build(self):
        self._header("Control de pagos", "Clic en un pago para ver su detalle",
                     actions=[("↺  Actualizar", "secondary", self._refresh)])
        self._cards = MetricCards(self, [
            ("Pendientes", "0", C["amber"]), ("Recaudado Bs", "0", C["green_dark"]),
            ("Total pagos", "0", C["blue"]), ("Biopago / Otros", "0 / 0", C["blue_dark"]),
        ])
        self._cards.pack(fill="x", padx=PAD, pady=(2, 8))

        ctk.CTkLabel(self, text="Despachos pendientes de pago", font=FONT_H3,
                     text_color=C["text"]).pack(anchor="w", padx=PAD, pady=(4, 4))
        self._pend_tbl = DataTable(self, [
            ("id", "#", 40), ("fecha", "Fecha", 120), ("cedula", "Cédula", 100),
            ("beneficiario", "Beneficiario", 180), ("litros", "Litros", 90),
            ("monto", "Monto Bs", 110),
        ], height=170)
        self._pend_tbl.pack(fill="x", padx=PAD, pady=(0, 4))
        self._pend_tbl.bind_select(self._cobrar)

        ctk.CTkLabel(self, text="Pagos registrados", font=FONT_H3,
                     text_color=C["text"]).pack(anchor="w", padx=PAD, pady=(8, 4))
        self._done_tbl = DataTable(self, [
            ("id", "#", 40), ("fecha", "Fecha", 120), ("beneficiario", "Beneficiario", 180),
            ("monto", "Monto Bs", 110), ("referencia", "Referencia", 130),
            ("metodo", "Método", 110), ("estado", "Estado", 100),
        ], height=200)
        self._done_tbl.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))
        self._done_tbl.bind_select(self._detalle)

    def _refresh(self):
        st = self.db.stats_pagos()
        self._cards.update("Pendientes", str(st["pendientes"]))
        self._cards.update("Recaudado Bs", f"{st['recaudado']:,.0f}")
        self._cards.update("Total pagos", str(st["n"]))
        self._cards.update("Biopago / Otros", f"{st['biopago']} / {st['otros']}")
        self._pend_tbl.load([{
            "id": r["id"], "fecha": r["fecha"][:16], "cedula": r["cedula"],
            "beneficiario": r["beneficiario"], "litros": f"{r['litros']:,.0f} L",
            "monto": f"{r['monto_bs']:,.2f}", "_raw": r,
        } for r in self.db.get_despachos_pendientes()])
        self._done_tbl.load([{
            "id": p["id"], "fecha": p["fecha"][:16], "beneficiario": p["beneficiario"],
            "monto": f"{p['monto_bs']:,.2f}", "referencia": p["referencia"] or "—",
            "metodo": p["metodo"], "estado": "✗ Anulado" if p["estado"] == "anulado" else "✓ Activo",
            "_raw": p,
        } for p in self.db.get_pagos(limit=300)])

    def _cobrar(self, idx, row):
        modals.PagoModal(self.app, self.db, self.user, self._refresh, row["_raw"])

    def _detalle(self, idx, row):
        p = row["_raw"]
        estado = "Anulado" if p["estado"] == "anulado" else "Registrado"
        fields = [
            ("Pago", f"#{p['id']}"), ("Despacho", f"#{p['despacho_id']}"),
            ("Beneficiario", f"{p['beneficiario']} ({p['cedula']})"),
            ("Monto", f"{p['monto_bs']:,.2f} Bs"), ("Referencia", p["referencia"] or "—"),
            ("Método", p["metodo"]), ("Estado", estado),
            ("Fecha", p["fecha"][:16]), ("Operador", p["operador"]),
        ]
        if p["estado"] == "anulado":
            fields.append(("Motivo de anulación", p["motivo_anulacion"] or "—"))
        actions = []
        if self.is_admin and p["estado"] != "anulado":
            actions.append(("Anular pago", "danger", lambda: self._anular(p)))
        modals.DetailModal(self.app, "Detalle del pago", fields, actions, accent="#7C3AED")

    def _anular(self, p):
        modals.ConfirmModal(
            self.app, "Anular pago",
            f"¿Anular el pago #{p['id']}? El despacho asociado volverá a quedar pendiente.",
            need_reason=True, confirm_text="Anular", variant="danger",
            on_confirm=lambda motivo: self._do_anular(p, motivo))

    def _do_anular(self, p, motivo):
        self.db.anular_pago(p["id"], motivo, self.user["nombre"])
        self.db.log(self.user["id"], self.user["nombre"], "Pagos",
                    "Anular", f"#{p['id']} — {motivo}")
        self._refresh()
        self.app.toast("Pago anulado")


# ════════════════════ REPORTES ══════════════════════════════════
class ReportesView(BaseView):
    PERIODOS = ["Hoy", "Esta semana", "Este mes", "Últimos 30 días",
                "Últimos 90 días", "Todo"]

    def _build(self):
        self._header("Reportes y análisis", "Genere y exporte la actividad de despachos")
        bar = card(self)
        bar.pack(fill="x", padx=PAD, pady=(2, 8))
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=PAD_SM, pady=PAD_SM)
        from ui.widgets import dropdown
        ctk.CTkLabel(inner, text="Período:", font=FONT_SM_M,
                     text_color=C["text2"]).pack(side="left", padx=(0, 6))
        self._periodo = dropdown(inner, self.PERIODOS, width=170)
        self._periodo.set("Este mes")
        self._periodo.pack(side="left", padx=(0, 14))
        btn(inner, "Generar", command=self._refresh, variant="primary",
            width=120).pack(side="left")
        btn(inner, "↓  Exportar CSV", command=self._export, variant="success",
            width=150).pack(side="right")

        self._cards = MetricCards(self, [
            ("Despachos", "0", C["blue"]), ("Litros", "0", C["amber_dark"]),
            ("Total Bs", "0", C["green_dark"]), ("Pagados", "0", C["green"]),
            ("Pendientes", "0", C["amber"]),
        ])
        self._cards.pack(fill="x", padx=PAD, pady=(2, 8))

        self._tbl = DataTable(self, [
            ("id", "#", 40), ("fecha", "Fecha", 120), ("beneficiario", "Beneficiario", 160),
            ("cedula", "Cédula", 100), ("litros", "Litros", 90), ("tipo", "Tipo", 100),
            ("estado", "Estado", 100), ("monto", "Monto Bs", 100),
        ], height=300)
        self._tbl.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))
        self._rows_cache = []

    def _rango(self):
        p = self._periodo.get()
        hoy = date.today()
        if p == "Hoy":
            return str(hoy), str(hoy)
        if p == "Esta semana":
            return str(hoy - timedelta(days=hoy.weekday())), str(hoy)
        if p == "Este mes":
            return str(hoy.replace(day=1)), str(hoy)
        if p == "Últimos 30 días":
            return str(hoy - timedelta(days=30)), str(hoy)
        if p == "Últimos 90 días":
            return str(hoy - timedelta(days=90)), str(hoy)
        return None, None

    def _refresh(self):
        desde, hasta = self._rango()
        st = self.db.stats_despachos(desde, hasta)
        self._cards.update("Despachos", str(st["n"]))
        self._cards.update("Litros", f"{st['litros']:,.0f}")
        self._cards.update("Total Bs", f"{st['monto']:,.0f}")
        self._cards.update("Pagados", str(st["pagados"]))
        self._cards.update("Pendientes", str(st["pendientes"]))
        self._rows_cache = self.db.get_despachos(limit=1000, desde=desde, hasta=hasta)
        self._tbl.load([{
            "id": r["id"], "fecha": r["fecha"][:16], "beneficiario": r["beneficiario"],
            "cedula": r["cedula"], "litros": f"{r['litros']:,.0f} L", "tipo": r["tipo"],
            "estado": "Anulado" if r["estado"] == "anulado" else (
                "Pagado" if r["pagado"] else "Pendiente"),
            "monto": f"{r['monto_bs']:,.2f}",
        } for r in self._rows_cache])

    def _export(self):
        if not self._rows_cache:
            self.app.toast("No hay datos para exportar", "error")
            return
        carpeta = os.path.join(os.path.expanduser("~"), "orinoco_reportes")
        os.makedirs(carpeta, exist_ok=True)
        ruta = os.path.join(carpeta, f"reporte_{datetime.now():%Y%m%d_%H%M%S}.csv")
        with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["#", "Fecha", "Cédula", "Beneficiario", "Litros", "Tipo",
                        "Monto Bs", "Estado", "Operador"])
            for r in self._rows_cache:
                w.writerow([r["id"], r["fecha"], r["cedula"], r["beneficiario"],
                            r["litros"], r["tipo"], r["monto_bs"],
                            "Anulado" if r["estado"] == "anulado" else (
                                "Pagado" if r["pagado"] else "Pendiente"),
                            r["operador"]])
        self.app.toast(f"Exportado: {ruta}")


# ════════════════════ OPERADORES (admin) ════════════════════════
class OperadoresView(BaseView):
    def _build(self):
        self._header("Operadores", "Cuentas de usuario del sistema (clic para gestionar)",
                     actions=[("＋  Nuevo operador", "primary", self._nuevo)])
        self._tbl = DataTable(self, [
            ("usuario", "Usuario", 130), ("nombre", "Nombre", 200),
            ("rol", "Rol", 140), ("estado", "Estado", 130),
        ], height=380)
        self._tbl.pack(fill="both", expand=True, padx=PAD, pady=(6, PAD))
        self._tbl.bind_select(self._detalle)

    def _refresh(self):
        rows = []
        for o in self.db.get_operadores():
            propio = o["id"] == self.user["id"]
            estado = "Activo" if o["activo"] else "Inactivo"
            if propio:
                estado = "🔒 Protegido"
            rows.append({
                "usuario": o["usuario"], "nombre": f"{o['nombre']} {o['apellido']}".strip(),
                "rol": "Administrador" if o["rol"] == "administrador" else "Operador",
                "estado": estado, "_raw": o, "_propio": propio,
            })
        self._tbl.load(rows)

    def _nuevo(self):
        modals.OperadorModal(self.app, self.db, self.user, self._refresh)

    def _detalle(self, idx, row):
        o = row["_raw"]
        propio = row["_propio"]
        fields = [
            ("Usuario", o["usuario"]), ("Nombre", f"{o['nombre']} {o['apellido']}".strip()),
            ("Cédula", o["cedula"] or "—"), ("Teléfono", o["telefono"] or "—"),
            ("Rol", "Administrador" if o["rol"] == "administrador" else "Operador"),
            ("Estado", "Activo" if o["activo"] else "Inactivo"),
            ("Creado", (o["creado_en"] or "")[:16]),
        ]
        actions = [
            ("Editar", "blue", lambda: modals.OperadorModal(
                self.app, self.db, self.user, self._refresh, dict(o))),
            ("Restablecer clave", "amber", lambda: modals.ResetPasswordModal(
                self.app, self.db, self.user, self._refresh, dict(o))),
        ]
        if not propio:
            if o["activo"]:
                actions.append(("Desactivar", "danger", lambda: self._toggle(o, 0)))
            else:
                actions.append(("Activar", "reactivate", lambda: self._toggle(o, 1)))
        badge = "Cuenta protegida — es la sesión actual" if propio else None
        modals.DetailModal(self.app, "Detalle del operador", fields, actions,
                           accent=C["blue"], badge=badge)

    def _toggle(self, o, activo):
        accion = "Activar" if activo else "Desactivar"
        modals.ConfirmModal(
            self.app, f"{accion} operador",
            f"¿{accion} la cuenta de {o['usuario']}?",
            confirm_text=accion, variant="reactivate" if activo else "danger",
            on_confirm=lambda _: self._do_toggle(o, activo))

    def _do_toggle(self, o, activo):
        self.db.toggle_operador(o["id"], activo)
        self.db.log(self.user["id"], self.user["nombre"], "Operadores",
                    "Activar" if activo else "Desactivar", o["usuario"])
        self._refresh()
        self.app.toast("Operador " + ("activado" if activo else "desactivado"))


# ════════════════════ CUENTA ════════════════════════════════════
class CuentaView(BaseView):
    def _build(self):
        self._header("Mi cuenta", "Datos de la sesión y seguridad")
        info = card(self)
        info.pack(fill="x", padx=PAD, pady=(2, 10))
        inner = ctk.CTkFrame(info, fg_color="transparent")
        inner.pack(fill="x", padx=PAD, pady=PAD_SM)
        for label, val in [
            ("Usuario", self.user.get("usuario", "—")),
            ("Nombre", f"{self.user.get('nombre','')} {self.user.get('apellido','')}".strip()),
            ("Rol", "Administrador" if self.is_admin else "Operador"),
        ]:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, font=FONT_SM_M, text_color=C["text2"],
                         width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=FONT_BODY, text_color=C["text"]).pack(side="left")

        sec = card(self)
        sec.pack(fill="x", padx=PAD, pady=(0, 10))
        si = ctk.CTkFrame(sec, fg_color="transparent")
        si.pack(fill="x", padx=PAD, pady=PAD_SM)
        ctk.CTkLabel(si, text="Seguridad", font=FONT_H3, text_color=C["text"]).pack(anchor="w")
        btn(si, "Cambiar contraseña", command=self._cambiar, variant="blue",
            width=200, height=40).pack(anchor="w", pady=(8, 0))

        sis = card(self)
        sis.pack(fill="x", padx=PAD, pady=(0, PAD))
        sysi = ctk.CTkFrame(sis, fg_color="transparent")
        sysi.pack(fill="x", padx=PAD, pady=PAD_SM)
        ctk.CTkLabel(sysi, text="Información del sistema", font=FONT_H3,
                     text_color=C["text"]).pack(anchor="w", pady=(0, 6))
        cfg = self.db.get_all_config()
        for label, val in [
            ("Sistema", "Orinoco v10"),
            ("Estación", cfg.get("nombre_estacion", "—")),
            ("RIF", cfg.get("rif", "—")),
            ("Base de datos", "SQLite (orinoco.db)"),
        ]:
            row = ctk.CTkFrame(sysi, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=label, font=FONT_SM_M, text_color=C["text2"],
                         width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=FONT_SM, text_color=C["text"]).pack(side="left")

    def _refresh(self):
        pass

    def _cambiar(self):
        modals.CambiarPasswordModal(self.app, self.db, self.user)


# ════════════════════ CONFIGURACIÓN (admin) ═════════════════════
class ConfiguracionView(BaseView):
    CAMPOS = [
        ("nombre_estacion", "Nombre de la estación"),
        ("rif", "RIF"),
        ("moneda", "Moneda"),
        ("alerta_minima_inventario", "Alerta mínima de inventario (L)"),
    ]

    def _build(self):
        self._header("Configuración", "Parámetros generales del sistema")
        box = card(self)
        box.pack(fill="x", padx=PAD, pady=(2, PAD))
        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(fill="x", padx=PAD, pady=PAD_SM)
        self._entries = {}
        cfg = self.db.get_all_config()
        for clave, label in self.CAMPOS:
            ctk.CTkLabel(inner, text=label.upper(), font=(FONT_LABEL[0], 9, "bold"),
                         text_color=C["text3"]).pack(anchor="w", pady=(12, 3))
            e = field(inner, width=420, height=40)
            e.insert(0, cfg.get(clave, ""))
            e.pack(anchor="w")
            self._entries[clave] = e
        btn(inner, "Guardar configuración", command=self._save, variant="primary",
            width=220, height=42).pack(anchor="w", pady=(18, 0))

    def _refresh(self):
        pass

    def _save(self):
        for clave, e in self._entries.items():
            self.db.set_config(clave, e.get().strip())
        self.db.log(self.user["id"], self.user["nombre"], "Configuración",
                    "Actualizar", "Parámetros del sistema")
        self.app.toast("Configuración guardada")


# ════════════════════ BITÁCORA (admin) ══════════════════════════
class BitacoraView(BaseView):
    def _build(self):
        self._header("Bitácora de actividad", "Registro de acciones de los usuarios",
                     actions=[("↺  Actualizar", "secondary", self._refresh)])
        self._tbl = DataTable(self, [
            ("fecha", "Fecha", 150), ("operador", "Operador", 150),
            ("modulo", "Módulo", 140), ("accion", "Acción", 150),
            ("detalle", "Detalle", 260),
        ], height=420)
        self._tbl.pack(fill="both", expand=True, padx=PAD, pady=(6, PAD))

    def _refresh(self):
        self._tbl.load([{
            "fecha": b["fecha"][:19], "operador": b["operador"] or "—",
            "modulo": b["modulo"] or "—", "accion": b["accion"] or "—",
            "detalle": b["detalle"] or "—",
        } for b in self.db.get_bitacora(limit=300)])
