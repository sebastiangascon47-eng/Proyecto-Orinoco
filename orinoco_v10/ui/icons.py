"""
icons.py — Iconos en color usando PIL
Genera CTkImage con icono coloreado sobre fondo badge.
"""
from __future__ import annotations
import io
from functools import lru_cache
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_OK = True
except ImportError:
    PIL_OK = False

import customtkinter as ctk
from core.theme import C

# Mapa de emoji → representación visual (usamos PIL para dibujar con color real)
# Para cada icono generamos una imagen PNG 32x32 en memoria

_ICON_DEFS: dict[str, tuple[str, str, str]] = {
    # key: (emoji, fg_hex, bg_hex)
    "home":      ("🏠", "#FFFFFF", C["blue"]),
    "users":     ("👥", "#FFFFFF", C["green_dark"]),
    "fuel":      ("⛽", "#FFFFFF", C["red"]),
    "payment":   ("💳", "#FFFFFF", "#7C3AED"),   # violeta
    "chart":     ("📊", "#FFFFFF", C["amber_dark"]),
    "settings":  ("⚙",  "#FFFFFF", C["text2"]),
    "logout":    ("⏻",  "#FFFFFF", "#EF4444"),
    "add":       ("＋", "#FFFFFF", C["red"]),
    "edit":      ("✏",  "#FFFFFF", C["blue"]),
    "delete":    ("⊘",  "#FFFFFF", "#DC2626"),
    "refresh":   ("↺",  "#FFFFFF", C["text2"]),
    "export":    ("↓",  "#FFFFFF", C["green_dark"]),
    "search":    ("🔍", "#FFFFFF", C["blue"]),
    "stock":     ("🛢",  "#FFFFFF", C["amber_dark"]),
    "check":     ("✓",  "#FFFFFF", C["green_dark"]),
    "clock":     ("🕐", "#FFFFFF", C["text2"]),
    "warning":   ("⚠",  "#FFFFFF", C["amber_dark"]),
    "info":      ("ℹ",  "#FFFFFF", C["blue"]),
}


@lru_cache(maxsize=128)
def get_icon(name: str, size: int = 28) -> "ctk.CTkImage | None":
    """Retorna CTkImage con icono coloreado, o None si PIL no está disponible."""
    if not PIL_OK:
        return None
    emoji, fg, bg = _ICON_DEFS.get(name, ("?", "#FFFFFF", "#888888"))
    return _make_badge(emoji, bg, size)


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _make_badge(emoji: str, bg_hex: str, size: int) -> "ctk.CTkImage":
    """Crea una imagen cuadrada con fondo de color y emoji centrado."""
    bg_rgb = _hex_to_rgb(bg_hex)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Círculo de fondo
    margin = 1
    draw.rounded_rectangle(
        [margin, margin, size - margin - 1, size - margin - 1],
        radius=size // 4,
        fill=bg_rgb + (255,),
    )

    # Intentar dibujar el emoji centrado
    try:
        # Usar fuente por defecto del sistema
        font_size = int(size * 0.55)
        try:
            font = ImageFont.truetype("seguiemj.ttf", font_size)  # Windows emoji font
        except Exception:
            try:
                font = ImageFont.truetype("NotoColorEmoji.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), emoji, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (size - tw) // 2 - bbox[0]
        y = (size - th) // 2 - bbox[1]
        draw.text((x, y), emoji, font=font, embedded_color=True)
    except Exception:
        pass  # Si falla el rendering del emoji, el badge queda sin texto

    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))


def sidebar_icon(name: str) -> "ctk.CTkImage | None":
    return get_icon(name, size=22)


def action_icon(name: str) -> "ctk.CTkImage | None":
    return get_icon(name, size=18)
