"""Vista: Reportes — análisis por período y exportación."""
from __future__ import annotations
import csv
import os
from datetime import date, datetime, timedelta

import customtkinter as ctk
from app.config import REPORTS_DIR
from core.theme import C, M, FONT_SM_M, FONT_H3, PAD, PAD_SM, BTN_H, CTRL_H, HDR_H, ROW_H
from ui.components.widgets import ChartCard, DataTable, btn, card, dropdown
from ui.views.base import BaseView

_TBL_VISIBLE_ROWS = 12


class ReportesView(BaseView):
    PERIODOS = ["Hoy", "Esta semana", "Este mes", "Últimos 30 días",
                "Últimos 90 días", "Todo"]

    def _build(self):
        self._page.grid_columnconfigure(0, weight=1)
        self._page.grid_rowconfigure(1, weight=1)
        self._periodo_key = "Hoy"

        top = ctk.CTkFrame(self._page, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew")

        self.page_title("Reportes y análisis",
                         "Consulte y exporte la actividad de despachos", parent=top)
        bar = card(top)
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
        self._periodo.set(self._periodo_key)
        self._periodo.configure(command=self._on_periodo)
        self._periodo.pack(side="left")
        btn(right, "Exportar CSV", command=self._export, variant="primary",
            width=160, height=BTN_H).pack(side="right")

        body = ctk.CTkScrollableFrame(
            self._page, fg_color="transparent",
            scrollbar_button_color=C["elevated"],
            scrollbar_button_hover_color=C["border"],
        )
        body.grid(row=1, column=0, sticky="nsew")

        self._cards = self.page_metrics([
            ("Despachos", "0", M[0]), ("Litros", "0", M[1]),
            ("Total Bs", "0", M[2]), ("Pagados", "0", M[3]),
            ("Pendientes", "0", M[3]),
        ], parent=body)
        self._chart = ChartCard(body, "Litros despachados", "por día del período",
                                "últimos despachos del período",
                                value_formatter=lambda v: f"{v:,.0f} L",
                                on_scope_change=lambda s: self._load_chart(s))
        self._chart.pack(fill="x", padx=PAD, pady=6)
        self._results_lbl = ctk.CTkLabel(
            body, text="Resultados del período", font=FONT_H3, text_color=C["text"])
        self._results_lbl.pack(anchor="w", padx=PAD, pady=(12, 6))
        panel = self.page_list_panel(expand=False, parent=body)
        self._tbl = DataTable(panel, [
            ("id", "#", 40), ("fecha", "Fecha", 120), ("beneficiario", "Beneficiario", 160),
            ("cedula", "Cédula", 100), ("litros", "Litros", 90), ("tipo", "Tipo", 100),
            ("estado", "Estado", 100), ("monto", "Monto Bs", 100),
        ], height=HDR_H + ROW_H * _TBL_VISIBLE_ROWS, flat=True)
        self._tbl.set_hidden_columns({"id"})
        self._tbl.pack(fill="both", expand=True)
        ctk.CTkFrame(body, fg_color="transparent", height=24).pack()
        self._rows_cache = []

    def on_show(self):
        self.schedule_refresh()

    def _on_periodo(self, value: str):
        self._periodo_key = value
        self._refresh()

    def _rango(self):
        p = self._periodo_key
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

    @staticmethod
    def _row_display(r) -> dict:
        return {
            "id": r["id"], "fecha": r["fecha"][:16], "beneficiario": r["beneficiario"],
            "cedula": r["cedula"], "litros": f"{r['litros']:,.0f} L", "tipo": r["tipo"],
            "estado": "Anulado" if r["estado"] == "anulado" else (
                "Pagado" if r["pagado"] else "Pendiente"),
            "monto": f"{r['monto_bs']:,.2f}",
        }

    def _refresh(self):
        desde, hasta = self._rango()
        st = self.db.stats_despachos(desde, hasta)
        self._cards.update("Despachos", str(st["n"]))
        self._cards.update("Litros", f"{st['litros']:,.0f}")
        self._cards.update("Total Bs", f"{st['monto']:,.0f}")
        self._cards.update("Pagados", str(st["pagados"]))
        self._cards.update("Pendientes", str(st["pendientes"]))
        self._rows_cache = self.db.get_despachos(
            limit=2000, desde=desde, hasta=hasta, incluir_anulados=False)
        n = len(self._rows_cache)
        self._results_lbl.configure(
            text=f"Resultados del período ({n} registro{'s' if n != 1 else ''})")
        rows = [self._row_display(r) for r in self._rows_cache]
        self._tbl.cancel_load()
        self._tbl._last_fp = None
        self._tbl.set_hidden_columns({"id"})
        self._tbl.load(rows)
        self._load_chart(self._chart.scope)

    def _load_chart(self, scope):
        if not self._rows_cache and scope == "tx":
            self._chart.set_data([])
            return
        if scope == "tx":
            data = [(f"#{r['id']}", r["litros"]) for r in reversed(self._rows_cache[:20])]
        else:
            desde, hasta = self._rango()
            if desde:
                data = self.db.get_series_despachos_rango(desde, hasta)
            else:
                data = self.db.get_series_despachos(365)
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
