"""
config.py — Rutas y parámetros globales (equivalente a app/config.py en SISARAD).
"""
from __future__ import annotations
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "orinoco.db")
REPORTS_DIR = os.path.join(os.path.expanduser("~"), "orinoco_reportes")

APP_NAME = "Orinoco v10"
APP_TITLE = "Estación Fluvial Orinoco C.A."
