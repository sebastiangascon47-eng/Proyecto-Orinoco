"""
theme.py — Design system Orinoco v10
Estación Fluvial Orinoco C.A.
Paleta unificada: rojo corporativo + neutros slate.
"""
import customtkinter as ctk

# ── Paleta ───────────────────────────────────────────────────────
C = {
    # Superficies
    "bg":            "#F4F5F7",
    "sidebar":       "#12141A",
    "sidebar_hover": "#1C1F26",
    "sidebar_border":"#252830",
    "sidebar_sel":   "#C41E1E",
    "card":          "#FFFFFF",
    "elevated":      "#EBEDF0",
    "input":         "#FFFFFF",
    "input_focus":   "#FEFEFE",
    "border":        "#E2E5EA",
    "border_focus":  "#C41E1E",

    # Marca — rojo corporativo Orinoco
    "red":           "#C41E1E",
    "red_hover":     "#A31818",
    "red_dark":      "#7F1414",
    "red_light":     "#FDF2F2",
    "red_mid":       "#FECACA",
    "red_subtle":    "#FEE8E8",

    # Semánticos (tonos apagados, sin arcoíris)
    "accent":        "#C41E1E",
    "success":       "#3D5A4C",
    "success_bg":    "#F2F6F4",
    "success_border":"#C5D4CC",
    "warning":       "#8B6914",
    "warning_bg":    "#FAF6EE",
    "warning_border":"#E8DFC8",
    "neutral":       "#475569",
    "neutral_dark":  "#334155",
    "neutral_bg":    "#F1F3F5",

    # Acentos KPI — variación sutil entre tarjetas
    "metric_1":      "#C41E1E",
    "metric_2":      "#334155",
    "metric_3":      "#64748B",
    "metric_4":      "#7F1414",

    # Texto
    "text":          "#1A1D21",
    "text2":         "#5C6570",
    "text3":         "#9AA3AD",
    "text_sidebar":  "#C8CDD4",
    "text_sidebar2": "#6B7280",
    "text_inv":      "#FFFFFF",

    # Tabla
    "table_header":  "#F8F9FA",
    "table_alt":     "#FAFBFC",
    "table_sel":     "#FDF2F2",
    "table_sel_text":"#C41E1E",
    "table_hover":   "#F4F5F7",

    # Compatibilidad con referencias heredadas
    "green":         "#3D5A4C",
    "green_dark":    "#2D4438",
    "green_bg":      "#F2F6F4",
    "green_border":  "#C5D4CC",
    "green_hover":   "#2D4438",
    "amber":         "#8B6914",
    "amber_dark":    "#6B5010",
    "amber_bg":      "#FAF6EE",
    "amber_border":  "#E8DFC8",
    "amber_hover":   "#6B5010",
    "blue":          "#334155",
    "blue_dark":     "#1E293B",
    "blue_bg":       "#F1F3F5",
    "blue_hover":    "#1E293B",
}

# Atajos para tarjetas de métricas por posición
M = (C["metric_1"], C["metric_2"], C["metric_3"], C["metric_4"])

# ── Tipografía ────────────────────────────────────────────────────
_F = "Segoe UI"

FONT_H1     = (_F, 24, "bold")
FONT_H2     = (_F, 18, "bold")
FONT_H3     = (_F, 14, "bold")
FONT_BODY   = (_F, 13)
FONT_BODY_M = (_F, 13, "bold")
FONT_SM     = (_F, 12)
FONT_SM_M   = (_F, 12, "bold")
FONT_XS     = (_F, 11)
FONT_XS_M   = (_F, 11, "bold")
FONT_LABEL  = (_F, 9,  "bold")
FONT_MONO   = ("Consolas", 12)
FONT_NUM    = (_F, 32, "bold")
FONT_NAV    = (_F, 12, "bold")

# ── Radios y espaciado ───────────────────────────────────────────
R_SM   = 6
R_MD   = 10
R_LG   = 14
R_XL   = 18
PAD    = 24
PAD_SM = 14
PAD_XS = 8

# Controles unificados (simetría en toda la app)
BTN_H   = 40
CTRL_H  = 40
ROW_H   = 44
HDR_H   = 40

# Listas paginadas (sin scroll interno en la tabla)
ROWS_PER_PAGE = 10
ROWS_PER_PAGE_COMPACT = 6


def setup():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("dark-blue")
