"""
main.py — Punto de entrada
Estación Fluvial Orinoco C.A.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.theme import setup
from core.database import DB
from ui.shell.login import LoginWindow


def main():
    setup()
    db = DB()
    app = LoginWindow(db)
    app.mainloop()


if __name__ == "__main__":
    main()
