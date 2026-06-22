"""
theme.py — Design system v5
Estación Fluvial Orinoco C.A.
"""
import customtkinter as ctk

# ── Paleta ───────────────────────────────────────────────────────
C = {
    # Superficie
    "bg":            "#F0F2F5",
    "sidebar":       "#111318",   # casi negro, máximo contraste
    "sidebar_hover": "#1E2028",
    "sidebar_sel":   "#C41E1E",
    "card":          "#FFFFFF",
    "elevated":      "#E9EBEE",
    "input":         "#FFFFFF",
    "input_focus":   "#FAFBFF",
    "border":        "#D1D5DB",
    "border_focus":  "#CC0000",

    # Rojo corporativo
    "red":           "#CC0000",
    "red_hover":     "#A80000",
    "red_dark":      "#8B0000",
    "red_light":     "#FEF2F2",
    "red_mid":       "#FCA5A5",

    # Verde
    "green":         "#15803D",
    "green_dark":    "#14532D",
    "green_bg":      "#F0FDF4",
    "green_border":  "#86EFAC",
    "green_hover":   "#166534",

    # Ámbar
    "amber":         "#B45309",
    "amber_dark":    "#78350F",
    "amber_bg":      "#FFFBEB",
    "amber_border":  "#FCD34D",
    "amber_hover":   "#92400E",

    # Azul
    "blue":          "#1D4ED8",
    "blue_dark":     "#1E3A8A",
    "blue_bg":       "#EFF6FF",
    "blue_hover":    "#1E40AF",

    # Texto
    "text":          "#0F172A",   # slate-900
    "text2":         "#475569",   # slate-600
    "text3":         "#94A3B8",   # slate-400
    "text_sidebar":  "#CBD5E1",
    "text_sidebar2": "#64748B",
    "text_inv":      "#FFFFFF",

    # Tabla
    "table_header":  "#F8FAFC",
    "table_alt":     "#FAFBFC",
    "table_sel":     "#EFF6FF",
    "table_sel_text":"#1D4ED8",
    "table_hover":   "#F1F5F9",
}

# ── Tipografía ────────────────────────────────────────────────────
_F = "Segoe UI"   # Windows / system fallback en macOS

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


def setup():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("dark-blue")
