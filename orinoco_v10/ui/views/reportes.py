"""Vista: Reportes — análisis por período y exportación."""
from __future__ import annotations
import csv
import os
from datetime import date, datetime, timedelta

import customtkinter as ctk
from app.config import REPORTS_DIR
from core.theme import C, M, FONT_SM_M, PAD, PAD_SM, BTN_H, CTRL_H, ROWS_PER_PAGE
from ui.components.widgets import ChartCard, btn, card, dropdown
from ui.views.base import BaseView


class ReportesView(BaseView):
    PERIODOS = ["Hoy", "Esta semana", "Este mes", "Últimos 30 días",
                "Últimos 90 días", "Todo"]

    def _build(self):
        self.page_title("Reportes y análisis", "Genere y exporte la actividad de despachos")
        bar = card(self._page)
        bar.pack(fill="x", padx=PAD, pady=(2, 8))
        inner = ctk.CTkFrame(bar, fg_color="transparent", height=CTRL_H + 8)
        inner.pack(fill="x", padx=PAD_SM, pady=PAD_SM)
        inner.pack_propagate(False)
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="y")
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right", fill="y")
        ctk.CTkLabel(left, text="Período:", font=FONT_SM_M,
                     text_color=C["text2"]).pack(side="left", padx=(0, 8))
        self._periodo = dropdown(left, self.PERIODOS, width=180)
        self._periodo.set("Este mes")
        self._periodo.pack(side="left", padx=(0, 12))
        btn(left, "Generar", command=self._refresh, variant="primary",
            width=130, height=BTN_H).pack(side="left")
        btn(right, "Exportar CSV", command=self._export, variant="secondary",
            width=160, height=BTN_H).pack(side="right")
        self._cards = self.page_metrics([
            ("Despachos", "0", M[0]), ("Litros", "0", M[1]),
            ("Total Bs", "0", M[2]), ("Pagados", "0", M[3]),
            ("Pendientes", "0", M[3]),
        ])
        self._chart = ChartCard(self._page, "Litros despachados", "por día del período",
                                "últimos despachos del período",
                                value_formatter=lambda v: f"{v:,.0f} L",
                                on_scope_change=lambda s: self._load_chart(s))
        self._chart.pack(fill="x", padx=PAD, pady=6)
        panel = self.page_panel("Resultados del período")
        self._ptbl = self.page_paginated_table(panel, [
            ("id", "#", 40), ("fecha", "Fecha", 120), ("beneficiario", "Beneficiario", 160),
            ("cedula", "Cédula", 100), ("litros", "Litros", 90), ("tipo", "Tipo", 100),
            ("estado", "Estado", 100), ("monto", "Monto Bs", 100),
        ], page_size=ROWS_PER_PAGE)
        self._rows_cache = []

    def on_show(self):
        """Los reportes solo se cargan al pulsar Generar."""
        pass

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

    def _chart_days(self) -> int:
        p = self._periodo.get()
        if p == "Hoy":
            return 1
        if p == "Esta semana":
            return 7
        if p == "Este mes":
            return 31
        if p == "Últimos 30 días":
            return 30
        if p == "Últimos 90 días":
            return 90
        return 365

    def _refresh(self):
        desde, hasta = self._rango()
        st = self.db.stats_despachos(desde, hasta)
        self._cards.update("Despachos", str(st["n"]))
        self._cards.update("Litros", f"{st['litros']:,.0f}")
        self._cards.update("Total Bs", f"{st['monto']:,.0f}")
        self._cards.update("Pagados", str(st["pagados"]))
        self._cards.update("Pendientes", str(st["pendientes"]))
        self._rows_cache = self.db.get_despachos(limit=2000, desde=desde, hasta=hasta)
        self._ptbl.load([{
            "id": r["id"], "fecha": r["fecha"][:16], "beneficiario": r["beneficiario"],
            "cedula": r["cedula"], "litros": f"{r['litros']:,.0f} L", "tipo": r["tipo"],
            "estado": "Anulado" if r["estado"] == "anulado" else (
                "Pagado" if r["pagado"] else "Pendiente"),
            "monto": f"{r['monto_bs']:,.2f}",
        } for r in self._rows_cache])
        self._load_chart(self._chart.scope)
        periodo = self._periodo.get()
        self.db.log(self.user["id"], self.user["nombre"], "Reportes",
                    "Generar", f"{periodo} — {st['n']} despachos")

    def _load_chart(self, scope):
        if not self._rows_cache and scope == "tx":
            self._chart.set_data([])
            return
        if scope == "tx":
            data = [(f"#{r['id']}", r["litros"]) for r in reversed(self._rows_cache[:20])]
        else:
            data = self.db.get_series_despachos(self._chart_days())
        self._chart.set_data(data)

    def _export(self):
        if not self._rows_cache:
            self.app.toast("No hay datos para exportar", "error")
            return
        os.makedirs(REPORTS_DIR, exist_ok=True)
        ruta = os.path.join(REPORTS_DIR, f"reporte_{datetime.now():%Y%m%d_%H%M%S}.csv")
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
        self.db.log(self.user["id"], self.user["nombre"], "Reportes",
                    "Exportar CSV", os.path.basename(ruta))
        self.app.toast(f"Exportado: {ruta}")
