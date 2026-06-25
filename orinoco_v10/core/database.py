"""
core/database.py — Orinoco v10
Capa de datos: esquema, migración desde v9, autenticación con hash,
CRUD y estadísticas por módulo, kardex de inventario y bitácora.
SQLite (archivo único). Sin dependencias externas.
"""
from __future__ import annotations
import sqlite3
import hashlib
import secrets
import os
import random
from datetime import datetime, timedelta

from app.config import DATA_DIR, DB_PATH

SCHEMA_VERSION = "11"
PBKDF2_ITERS = 100_000


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _new_salt() -> str:
    return secrets.token_hex(16)


def _hash(texto: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", texto.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERS
    ).hex()


class DB:
    def __init__(self, path: str | None = None):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.path = path or DB_PATH
        self._conn: sqlite3.Connection | None = None
        self._init()

    def con(self) -> sqlite3.Connection:
        """Conexión persistente (evita abrir/cerrar SQLite en cada consulta)."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.execute("PRAGMA synchronous = NORMAL")
            self._conn.execute("PRAGMA cache_size = -16000")
            self._conn.execute("PRAGMA temp_store = MEMORY")
        return self._conn

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ── columnas / utilidades de esquema ─────────────────────────
    @staticmethod
    def _cols(c, tabla: str) -> set[str]:
        return {r["name"] for r in c.execute(f"PRAGMA table_info({tabla})")}

    @staticmethod
    def _has_table(c, tabla: str) -> bool:
        return c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla,)
        ).fetchone() is not None

    # ── inicialización + migración ───────────────────────────────
    def _init(self):
        with self.con() as c:
            es_v9 = self._has_table(c, "stock") and not self._has_table(c, "inventario")
            fresca = not self._has_table(c, "operadores") and not self._has_table(c, "stock")

            self._crear_tablas(c)
            self._seed_catalogos(c)
            self._asegurar_config_extra(c)

            if es_v9:
                self._migrar_desde_v9(c)
            elif fresca:
                self._asegurar_admin(c)
                self._seed_demo(c)
            else:
                self._asegurar_columnas_v10(c)

            self._asegurar_admin(c)
            self._asegurar_operador_demo(c)
            self._aplicar_migraciones(c)

            c.execute(
                "INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('schema_version', ?)",
                (SCHEMA_VERSION,),
            )
            self._crear_indices(c)

    def _crear_indices(self, c):
        """Índices para acelerar listados y reportes."""
        c.executescript("""
        CREATE INDEX IF NOT EXISTS idx_despachos_fecha ON despachos(fecha DESC);
        CREATE INDEX IF NOT EXISTS idx_despachos_estado ON despachos(estado, pagado);
        CREATE INDEX IF NOT EXISTS idx_pagos_fecha ON pagos(fecha DESC);
        CREATE INDEX IF NOT EXISTS idx_bitacora_fecha ON bitacora(fecha DESC);
        CREATE INDEX IF NOT EXISTS idx_beneficiarios_activo ON beneficiarios(activo, apellido, nombre);
        CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos_inventario(fecha DESC);
        """)

    def _crear_tablas(self, c):
        c.executescript("""
        CREATE TABLE IF NOT EXISTS operadores (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario            TEXT    UNIQUE NOT NULL,
            nombre             TEXT    NOT NULL,
            apellido           TEXT    DEFAULT '',
            cedula             TEXT    DEFAULT '',
            telefono           TEXT    DEFAULT '',
            clave_hash         TEXT    NOT NULL,
            salt               TEXT    NOT NULL,
            pregunta_seguridad TEXT    DEFAULT '',
            respuesta_hash     TEXT    DEFAULT '',
            rol                TEXT    NOT NULL DEFAULT 'operador',
            activo             INTEGER NOT NULL DEFAULT 1,
            creado_en          TEXT    DEFAULT (datetime('now','localtime')),
            actualizado_en     TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS beneficiarios (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula         TEXT    UNIQUE NOT NULL,
            nombre         TEXT    NOT NULL,
            apellido       TEXT    NOT NULL,
            telefono       TEXT,
            correo         TEXT,
            embarcacion    TEXT,
            motor          TEXT,
            activo         INTEGER NOT NULL DEFAULT 1,
            creado_en      TEXT    DEFAULT (datetime('now','localtime')),
            actualizado_en TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS inventario (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo           TEXT    UNIQUE NOT NULL,
            litros_actual  REAL    NOT NULL DEFAULT 0,
            capacidad      REAL    NOT NULL DEFAULT 20000,
            minimo_alerta  REAL    NOT NULL DEFAULT 2000,
            activo         INTEGER NOT NULL DEFAULT 1,
            creado_en      TEXT    DEFAULT (datetime('now','localtime')),
            actualizado_en TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS movimientos_inventario (
            id                     INTEGER PRIMARY KEY AUTOINCREMENT,
            inventario_id          INTEGER NOT NULL REFERENCES inventario(id) ON DELETE CASCADE,
            tipo_movimiento        TEXT    NOT NULL,
            litros                 REAL    NOT NULL,
            referencia_despacho_id INTEGER REFERENCES despachos(id) ON DELETE SET NULL,
            motivo                 TEXT,
            operador               TEXT    DEFAULT 'Sistema',
            fecha                  TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS metodos_pago (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT    UNIQUE NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS despachos (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            beneficiario_id  INTEGER NOT NULL REFERENCES beneficiarios(id),
            inventario_id    INTEGER REFERENCES inventario(id),
            tipo             TEXT    DEFAULT 'Gasoil',
            litros           REAL    NOT NULL CHECK(litros > 0),
            monto_bs         REAL    DEFAULT 0,
            operador         TEXT    DEFAULT 'Sistema',
            observaciones    TEXT,
            pagado           INTEGER NOT NULL DEFAULT 0,
            estado           TEXT    NOT NULL DEFAULT 'registrado',
            motivo_anulacion TEXT,
            fecha            TEXT    DEFAULT (datetime('now','localtime')),
            actualizado_en   TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS pagos (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            despacho_id      INTEGER NOT NULL REFERENCES despachos(id),
            beneficiario_id  INTEGER NOT NULL REFERENCES beneficiarios(id),
            monto_bs         REAL    NOT NULL,
            referencia       TEXT,
            metodo_pago_id   INTEGER REFERENCES metodos_pago(id),
            metodo           TEXT    DEFAULT 'Biopago',
            operador         TEXT    DEFAULT 'Sistema',
            estado           TEXT    NOT NULL DEFAULT 'registrado',
            motivo_anulacion TEXT,
            fecha            TEXT    DEFAULT (datetime('now','localtime')),
            actualizado_en   TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS bitacora (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            operador_id INTEGER REFERENCES operadores(id) ON DELETE SET NULL,
            operador    TEXT,
            modulo      TEXT,
            accion      TEXT,
            detalle     TEXT,
            fecha       TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_desp_fecha ON despachos(fecha);
        CREATE INDEX IF NOT EXISTS idx_desp_ben   ON despachos(beneficiario_id);
        CREATE INDEX IF NOT EXISTS idx_pago_fecha ON pagos(fecha);
        CREATE INDEX IF NOT EXISTS idx_pago_desp  ON pagos(despacho_id);
        CREATE INDEX IF NOT EXISTS idx_mov_inv    ON movimientos_inventario(inventario_id);
        CREATE INDEX IF NOT EXISTS idx_bita_fecha ON bitacora(fecha);
        """)

    def _seed_catalogos(self, c):
        from core.catalogs import METODOS_PAGO
        for m in METODOS_PAGO:
            c.execute("INSERT OR IGNORE INTO metodos_pago (nombre) VALUES (?)", (m,))
        defaults = {
            "nombre_estacion": "Estación Fluvial Orinoco C.A.",
            "rif": "J-31086589-2",
            "moneda": "Bs",
            "alerta_minima_inventario": "2000",
            "precio_litro_gasoil": "0.50",
            "precio_litro_gasolina_91": "0.55",
            "precio_litro_gasolina_95": "0.60",
        }
        for k, v in defaults.items():
            c.execute(
                "INSERT OR IGNORE INTO configuracion (clave, valor) VALUES (?, ?)", (k, v)
            )

    def _asegurar_config_extra(self, c):
        """Claves de configuración añadidas en versiones recientes."""
        extras = {
            "precio_litro_gasoil": "0.50",
            "precio_litro_gasolina_91": "0.55",
            "precio_litro_gasolina_95": "0.60",
        }
        for k, v in extras.items():
            c.execute(
                "INSERT OR IGNORE INTO configuracion (clave, valor) VALUES (?, ?)", (k, v)
            )

    def _asegurar_admin(self, c):
        if c.execute("SELECT 1 FROM operadores WHERE usuario='admin'").fetchone():
            return
        salt = _new_salt()
        c.execute("""
            INSERT INTO operadores
                (usuario, nombre, apellido, clave_hash, salt,
                 pregunta_seguridad, respuesta_hash, rol, activo)
            VALUES (?,?,?,?,?,?,?,?,1)
        """, ("admin", "Administrador", "", _hash("admin123", salt), salt,
              "¿Nombre de la estación?", _hash("orinoco", salt), "administrador"))

    def _asegurar_operador_demo(self, c):
        if c.execute("SELECT 1 FROM operadores WHERE usuario='operador'").fetchone():
            return
        salt = _new_salt()
        c.execute("""
            INSERT INTO operadores
                (usuario, nombre, apellido, clave_hash, salt,
                 pregunta_seguridad, respuesta_hash, rol, activo)
            VALUES (?,?,?,?,?,?,?,?,1)
        """, ("operador", "Operador", "Sistema", _hash("operador123", salt), salt,
              "¿Nombre de la estación?", _hash("orinoco", salt), "operador"))

    # ── migración v9 → v10 ───────────────────────────────────────
    def _migrar_desde_v9(self, c):
        # 1) operadores: añadir columnas, hashear claves, quitar 'clave'
        ocols = self._cols(c, "operadores")
        nuevas = [
            ("apellido", "TEXT DEFAULT ''"), ("cedula", "TEXT DEFAULT ''"),
            ("telefono", "TEXT DEFAULT ''"), ("clave_hash", "TEXT"),
            ("salt", "TEXT"), ("pregunta_seguridad", "TEXT DEFAULT ''"),
            ("respuesta_hash", "TEXT DEFAULT ''"),
            ("creado_en", "TEXT"), ("actualizado_en", "TEXT"),
        ]
        for col, decl in nuevas:
            if col not in ocols:
                c.execute(f"ALTER TABLE operadores ADD COLUMN {col} {decl}")
        if "clave" in ocols:
            for r in c.execute("SELECT id, clave FROM operadores").fetchall():
                salt = _new_salt()
                c.execute(
                    "UPDATE operadores SET clave_hash=?, salt=?, creado_en=?, "
                    "actualizado_en=?, pregunta_seguridad=?, respuesta_hash=? WHERE id=?",
                    (_hash(r["clave"] or "", salt), salt, _now(), _now(),
                     "¿Nombre de la estación?", _hash("orinoco", salt), r["id"]),
                )
            c.execute("ALTER TABLE operadores DROP COLUMN clave")

        # 2) inventario desde stock
        tipos = {t["tipo"] for t in c.execute(
            "SELECT DISTINCT tipo FROM despachos WHERE tipo IS NOT NULL"
        ).fetchall()}
        tipos |= {"Gasoil", "Gasolina 91", "Gasolina 95"}
        stock = c.execute("SELECT * FROM stock WHERE id=1").fetchone()
        litros_inicial = stock["litros"] if stock else 0
        tipo_inicial = (stock["tipo"] if stock else "Gasoil") or "Gasoil"
        for t in sorted(tipos):
            litros = litros_inicial if t == tipo_inicial else 0
            c.execute(
                "INSERT OR IGNORE INTO inventario (tipo, litros_actual) VALUES (?, ?)",
                (t, litros),
            )
        inv_id = c.execute(
            "SELECT id FROM inventario WHERE tipo=?", (tipo_inicial,)
        ).fetchone()
        if inv_id and litros_inicial:
            c.execute("""
                INSERT INTO movimientos_inventario
                    (inventario_id, tipo_movimiento, litros, motivo, operador)
                VALUES (?, 'entrada', ?, 'Migración de saldo inicial v9', 'Sistema')
            """, (inv_id["id"], litros_inicial))

        # 3) despachos: columnas nuevas + mapear inventario + quitar ref_biopago
        dcols = self._cols(c, "despachos")
        for col, decl in [("inventario_id", "INTEGER"),
                          ("estado", "TEXT DEFAULT 'registrado'"),
                          ("motivo_anulacion", "TEXT"),
                          ("actualizado_en", "TEXT")]:
            if col not in dcols:
                c.execute(f"ALTER TABLE despachos ADD COLUMN {col} {decl}")
        c.execute("""
            UPDATE despachos
               SET inventario_id = (SELECT i.id FROM inventario i WHERE i.tipo = despachos.tipo),
                   estado = COALESCE(estado, 'registrado'),
                   actualizado_en = COALESCE(actualizado_en, fecha)
        """)
        if "ref_biopago" in dcols:
            c.execute("ALTER TABLE despachos DROP COLUMN ref_biopago")

        # 4) pagos: columnas nuevas + mapear metodo_pago_id
        pcols = self._cols(c, "pagos")
        for col, decl in [("metodo_pago_id", "INTEGER"),
                          ("estado", "TEXT DEFAULT 'registrado'"),
                          ("motivo_anulacion", "TEXT"),
                          ("actualizado_en", "TEXT")]:
            if col not in pcols:
                c.execute(f"ALTER TABLE pagos ADD COLUMN {col} {decl}")
        # registrar en el catálogo cualquier método histórico no contemplado
        for r in c.execute("SELECT DISTINCT metodo FROM pagos WHERE metodo IS NOT NULL").fetchall():
            c.execute("INSERT OR IGNORE INTO metodos_pago (nombre) VALUES (?)", (r["metodo"],))
        c.execute("""
            UPDATE pagos
               SET metodo_pago_id = (SELECT m.id FROM metodos_pago m WHERE m.nombre = pagos.metodo),
                   estado = COALESCE(estado, 'registrado'),
                   actualizado_en = COALESCE(actualizado_en, fecha)
        """)

        # 5) eliminar tabla stock
        c.execute("DROP TABLE IF EXISTS stock")

    def _asegurar_columnas_v10(self, c):
        if c.execute("SELECT COUNT(*) FROM inventario").fetchone()[0] == 0:
            from core.catalogs import TIPOS_COMBUSTIBLE
            for t in TIPOS_COMBUSTIBLE:
                c.execute("INSERT OR IGNORE INTO inventario (tipo) VALUES (?)", (t,))

    # ── seed demo (solo instalación nueva) ───────────────────────
    def _seed_demo(self, c):
        for t, litros in (("Gasoil", 12000), ("Gasolina 91", 8000), ("Gasolina 95", 5000)):
            c.execute(
                "INSERT OR IGNORE INTO inventario (tipo, litros_actual) VALUES (?, ?)",
                (t, litros),
            )
        bens = [
            ("18456789", "José", "Ramírez", "0414-1234567", "El Delfín", "Yamaha 40HP"),
            ("20987654", "María", "González", "0412-7654321", "La Gaviota", "Suzuki 60HP"),
            ("15321098", "Pedro", "Martínez", "0416-2223344", "San Rafael", "Yamaha 75HP"),
            ("24567890", "Luisa", "Hernández", "0426-5556677", "Estrella del Mar", "Suzuki 40HP"),
        ]
        for ced, n, a, tel, emb, mot in bens:
            c.execute("""INSERT OR IGNORE INTO beneficiarios
                (cedula, nombre, apellido, telefono, embarcacion, motor)
                VALUES (?,?,?,?,?,?)""", (ced, n, a, tel, emb, mot))

        # despachos de ejemplo (con movimiento de inventario y algunos pagados)
        bids = [r["id"] for r in c.execute("SELECT id FROM beneficiarios ORDER BY id").fetchall()]
        gid = c.execute("SELECT id FROM inventario WHERE tipo='Gasoil'").fetchone()
        bio = c.execute("SELECT id FROM metodos_pago WHERE nombre='Biopago'").fetchone()
        if bids and gid:
            inv_id, met_id = gid["id"], (bio["id"] if bio else 1)
            ejemplos = [(bids[0], 200, 1000, True), (bids[1], 150, 750, True),
                        (bids[2], 300, 1500, False), (bids[0], 120, 600, True),
                        (bids[3], 80, 400, False)]
            for ben_id, litros, monto, pagado in ejemplos:
                cur = c.execute("""INSERT INTO despachos
                    (beneficiario_id, inventario_id, tipo, litros, monto_bs, operador, pagado)
                    VALUES (?,?,?,?,?,?,?)""",
                    (ben_id, inv_id, "Gasoil", litros, monto, "Administrador", int(pagado)))
                did = cur.lastrowid
                c.execute("UPDATE inventario SET litros_actual = litros_actual - ? WHERE id=?",
                          (litros, inv_id))
                c.execute("""INSERT INTO movimientos_inventario
                    (inventario_id, tipo_movimiento, litros, referencia_despacho_id, motivo, operador)
                    VALUES (?, 'salida', ?, ?, 'Despacho de combustible', 'Administrador')""",
                    (inv_id, litros, did))
                if pagado:
                    c.execute("""INSERT INTO pagos
                        (despacho_id, beneficiario_id, monto_bs, referencia, metodo_pago_id, metodo, operador)
                        VALUES (?,?,?,?,?, 'Biopago', 'Administrador')""",
                        (did, ben_id, monto, f"BIO{did:04d}", met_id))

    def _aplicar_migraciones(self, c):
        prev = c.execute(
            "SELECT valor FROM configuracion WHERE clave='schema_version'"
        ).fetchone()
        prev_v = prev["valor"] if prev else "0"
        if prev_v < "11":
            self._migrar_v11_bulk(c)

    def _migrar_v11_bulk(self, c):
        """Carga masiva de datos de operación (una sola vez)."""
        if c.execute("SELECT valor FROM configuracion WHERE clave='bulk_v11'").fetchone():
            return

        nombres = [
            "Carlos", "Ana", "Luis", "Rosa", "Miguel", "Carmen", "Jorge", "Elena",
            "Ricardo", "Patricia", "Fernando", "Gabriela", "Héctor", "Isabel", "Raúl",
            "Sandra", "Oscar", "Teresa", "Daniel", "Beatriz", "Andrés", "Lucía",
            "Francisco", "Mónica", "Alberto", "Natalia", "Roberto", "Claudia",
        ]
        apellidos = [
            "Pérez", "Rodríguez", "Gómez", "Fernández", "López", "Martínez", "Díaz",
            "Hernández", "Torres", "Ramírez", "Flores", "Morales", "Vargas", "Rivas",
            "Castro", "Mendoza", "Silva", "Rojas", "Guerrero", "Salazar", "Peña",
        ]
        embarcaciones = [
            "El Caimán", "La Sirena", "San José", "Mar Caribe", "Estrella Norte",
            "Boca de Dragón", "Río Bravo", "La Tortuga", "Pescador I", "Pescador II",
            "Orinoco Express", "Delta Sur", "Caño Negro", "Aguila Real", "Trinidad",
        ]
        motores = ["Yamaha 40HP", "Yamaha 75HP", "Suzuki 60HP", "Mercury 90HP", "Evinrude 50HP"]

        for i in range(95):
            ced = f"{31000000 + i}"
            c.execute("""INSERT OR IGNORE INTO beneficiarios
                (cedula, nombre, apellido, telefono, embarcacion, motor, creado_en)
                VALUES (?,?,?,?,?,?,?)""",
                (ced, random.choice(nombres), random.choice(apellidos),
                 f"04{random.randint(12,26)}-{random.randint(1000000,9999999)}",
                 random.choice(embarcaciones), random.choice(motores),
                 (datetime.now() - timedelta(days=random.randint(30, 540))).strftime("%Y-%m-%d %H:%M:%S")))

        c.execute("UPDATE inventario SET litros_actual = capacidad * 0.88 WHERE activo=1")

        inv_rows = c.execute(
            "SELECT id, tipo, litros_actual, capacidad FROM inventario WHERE activo=1"
        ).fetchall()
        inv_by_tipo = {r["tipo"]: r for r in inv_rows}
        bids = [r["id"] for r in c.execute("SELECT id FROM beneficiarios WHERE activo=1").fetchall()]
        bio = c.execute("SELECT id FROM metodos_pago WHERE nombre='Biopago'").fetchone()
        met_id = bio["id"] if bio else 1
        tipos = list(inv_by_tipo.keys()) or ["Gasoil"]
        precios = {"Gasoil": 5.0, "Gasolina 91": 5.5, "Gasolina 95": 6.0}
        random.seed(2026)

        for _ in range(420):
            ben_id = random.choice(bids)
            tipo = random.choice(tipos)
            inv = inv_by_tipo.get(tipo)
            if not inv:
                continue
            litros = float(random.choice([40, 60, 80, 100, 120, 150, 180, 200, 250]))
            if inv["litros_actual"] < litros:
                continue
            monto = round(litros * precios.get(tipo, 5.0), 2)
            dias = random.randint(0, 200)
            fecha = (datetime.now() - timedelta(days=dias,
                     hours=random.randint(6, 18),
                     minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M:%S")
            pagado = random.random() < 0.68
            cur = c.execute("""INSERT INTO despachos
                (beneficiario_id, inventario_id, tipo, litros, monto_bs, operador, pagado, fecha)
                VALUES (?,?,?,?,?,?,?,?)""",
                (ben_id, inv["id"], tipo, litros, monto, "Administrador", int(pagado), fecha))
            did = cur.lastrowid
            c.execute("UPDATE inventario SET litros_actual = litros_actual - ?, actualizado_en=? WHERE id=?",
                      (litros, _now(), inv["id"]))
            inv_by_tipo[tipo] = dict(inv)
            inv_by_tipo[tipo]["litros_actual"] -= litros
            c.execute("""INSERT INTO movimientos_inventario
                (inventario_id, tipo_movimiento, litros, referencia_despacho_id, motivo, operador, fecha)
                VALUES (?, 'salida', ?, ?, 'Despacho de combustible', 'Administrador', ?)""",
                (inv["id"], litros, did, fecha))
            if pagado:
                c.execute("""INSERT INTO pagos
                    (despacho_id, beneficiario_id, monto_bs, referencia, metodo_pago_id, metodo, operador, fecha)
                    VALUES (?,?,?,?,?, 'Biopago', 'Administrador', ?)""",
                    (did, ben_id, monto, f"BIO{did:05d}", met_id, fecha))

        for inv in inv_rows:
            litros = round(float(inv["capacidad"]) * 0.05, 0)
            if litros <= 0:
                litros = 500
            fecha = (datetime.now() - timedelta(days=random.randint(10, 120))).strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""INSERT INTO movimientos_inventario
                (inventario_id, tipo_movimiento, litros, motivo, operador, fecha)
                VALUES (?, 'entrada', ?, 'Reabastecimiento programado', 'Administrador', ?)""",
                (inv["id"], litros, fecha))

        modulos = ["Despachos", "Pagos", "Beneficiarios", "Inventario", "Reportes"]
        acciones = ["Registrar", "Actualizar", "Consultar", "Exportar", "Anular"]
        for _ in range(80):
            fecha = (datetime.now() - timedelta(days=random.randint(0, 90),
                     hours=random.randint(8, 17))).strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""INSERT INTO bitacora (operador, modulo, accion, detalle, fecha)
                VALUES (?,?,?,?,?)""",
                ("Administrador", random.choice(modulos), random.choice(acciones),
                 f"Operación #{random.randint(100, 9999)}", fecha))

        c.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('bulk_v11', '1')")

    # ════════════════════ AUTENTICACIÓN ═════════════════════════
    def auth(self, usuario: str, clave: str):
        with self.con() as c:
            r = c.execute(
                "SELECT * FROM operadores WHERE usuario=? AND activo=1", (usuario,)
            ).fetchone()
            if r and _hash(clave, r["salt"]) == r["clave_hash"]:
                return r
            return None

    def get_pregunta(self, usuario: str) -> str | None:
        with self.con() as c:
            r = c.execute(
                "SELECT pregunta_seguridad FROM operadores WHERE usuario=? AND activo=1",
                (usuario,),
            ).fetchone()
            return r["pregunta_seguridad"] if r else None

    def recuperar_password(self, usuario: str, respuesta: str, clave_nueva: str) -> bool:
        with self.con() as c:
            r = c.execute(
                "SELECT id, salt, respuesta_hash FROM operadores WHERE usuario=? AND activo=1",
                (usuario,),
            ).fetchone()
            if not r or _hash(respuesta.strip().lower(), r["salt"]) != r["respuesta_hash"]:
                return False
            salt = _new_salt()
            c.execute(
                "UPDATE operadores SET clave_hash=?, salt=?, respuesta_hash=?, "
                "actualizado_en=? WHERE id=?",
                (_hash(clave_nueva, salt), salt,
                 _hash(respuesta.strip().lower(), salt), _now(), r["id"]),
            )
            return True

    def change_password(self, id_: int, clave_nueva: str):
        salt = _new_salt()
        with self.con() as c:
            c.execute(
                "UPDATE operadores SET clave_hash=?, salt=?, actualizado_en=? WHERE id=?",
                (_hash(clave_nueva, salt), salt, _now(), id_),
            )

    # ════════════════════ OPERADORES (admin) ════════════════════
    def get_operadores(self, incluir_inactivos: bool = True) -> list:
        q = "SELECT * FROM operadores"
        if not incluir_inactivos:
            q += " WHERE activo=1"
        q += " ORDER BY nombre, apellido"
        with self.con() as c:
            return c.execute(q).fetchall()

    def get_operador(self, id_: int):
        with self.con() as c:
            return c.execute("SELECT * FROM operadores WHERE id=?", (id_,)).fetchone()

    def add_operador(self, usuario, clave, nombre, apellido="", cedula="",
                     telefono="", rol="operador",
                     pregunta="¿Nombre de la estación?", respuesta="orinoco") -> int:
        salt = _new_salt()
        with self.con() as c:
            cur = c.execute("""
                INSERT INTO operadores
                    (usuario, nombre, apellido, cedula, telefono, clave_hash, salt,
                     pregunta_seguridad, respuesta_hash, rol, activo)
                VALUES (?,?,?,?,?,?,?,?,?,?,1)
            """, (usuario, nombre, apellido, cedula, telefono,
                  _hash(clave, salt), salt, pregunta,
                  _hash(respuesta.strip().lower(), salt), rol))
            return cur.lastrowid

    def update_operador(self, id_, nombre, apellido, cedula, telefono, rol):
        with self.con() as c:
            c.execute("""
                UPDATE operadores SET nombre=?, apellido=?, cedula=?, telefono=?, rol=?,
                       actualizado_en=? WHERE id=?
            """, (nombre, apellido, cedula, telefono, rol, _now(), id_))

    def toggle_operador(self, id_: int, activo: int):
        with self.con() as c:
            c.execute("UPDATE operadores SET activo=?, actualizado_en=? WHERE id=?",
                      (activo, _now(), id_))

    def reset_password_operador(self, id_: int, clave_nueva: str):
        salt = _new_salt()
        with self.con() as c:
            c.execute("UPDATE operadores SET clave_hash=?, salt=?, actualizado_en=? WHERE id=?",
                      (_hash(clave_nueva, salt), salt, _now(), id_))

    def usuario_existe(self, usuario: str, excluir_id: int | None = None) -> bool:
        with self.con() as c:
            if excluir_id:
                r = c.execute("SELECT 1 FROM operadores WHERE usuario=? AND id<>?",
                              (usuario, excluir_id)).fetchone()
            else:
                r = c.execute("SELECT 1 FROM operadores WHERE usuario=?", (usuario,)).fetchone()
            return r is not None

    # ════════════════════ BENEFICIARIOS ═════════════════════════
    def get_beneficiarios(self, solo_activos: bool = True) -> list:
        q = "SELECT * FROM beneficiarios"
        if solo_activos:
            q += " WHERE activo = 1"
        q += " ORDER BY apellido, nombre"
        with self.con() as c:
            return c.execute(q).fetchall()

    def search_beneficiarios(self, term: str, solo_activos: bool = True) -> list:
        like = f"%{term}%"
        cond = "activo = 1 AND " if solo_activos else ""
        with self.con() as c:
            return c.execute(f"""
                SELECT * FROM beneficiarios
                WHERE {cond}(cedula LIKE ? OR nombre LIKE ? OR apellido LIKE ? OR embarcacion LIKE ?)
                ORDER BY apellido, nombre
            """, (like,) * 4).fetchall()

    def get_beneficiario(self, id_: int):
        with self.con() as c:
            return c.execute("SELECT * FROM beneficiarios WHERE id=?", (id_,)).fetchone()

    def get_beneficiario_by_cedula(self, cedula: str):
        with self.con() as c:
            return c.execute("SELECT * FROM beneficiarios WHERE cedula=?", (cedula,)).fetchone()

    def add_beneficiario(self, cedula, nombre, apellido, telefono,
                         embarcacion, motor, correo="") -> int:
        with self.con() as c:
            cur = c.execute("""
                INSERT INTO beneficiarios
                    (cedula, nombre, apellido, telefono, correo, embarcacion, motor)
                VALUES (?,?,?,?,?,?,?)
            """, (cedula, nombre, apellido, telefono, correo, embarcacion, motor))
            return cur.lastrowid

    def update_beneficiario(self, id_, cedula, nombre, apellido, telefono,
                            embarcacion, motor, correo=""):
        with self.con() as c:
            c.execute("""
                UPDATE beneficiarios SET cedula=?, nombre=?, apellido=?, telefono=?,
                       correo=?, embarcacion=?, motor=?, actualizado_en=? WHERE id=?
            """, (cedula, nombre, apellido, telefono, correo, embarcacion, motor, _now(), id_))

    def toggle_beneficiario(self, id_: int, activo: int):
        with self.con() as c:
            c.execute("UPDATE beneficiarios SET activo=?, actualizado_en=? WHERE id=?",
                      (activo, _now(), id_))

    def stats_beneficiarios(self) -> dict:
        with self.con() as c:
            return {
                "total": c.execute("SELECT COUNT(*) FROM beneficiarios").fetchone()[0],
                "activos": c.execute("SELECT COUNT(*) FROM beneficiarios WHERE activo=1").fetchone()[0],
                "inactivos": c.execute("SELECT COUNT(*) FROM beneficiarios WHERE activo=0").fetchone()[0],
                "con_embarcacion": c.execute(
                    "SELECT COUNT(*) FROM beneficiarios WHERE embarcacion IS NOT NULL AND embarcacion<>''"
                ).fetchone()[0],
            }

    # ════════════════════ INVENTARIO ════════════════════════════
    def get_inventario(self, solo_activos: bool = False) -> list:
        q = "SELECT * FROM inventario"
        if solo_activos:
            q += " WHERE activo=1"
        q += " ORDER BY tipo"
        with self.con() as c:
            return c.execute(q).fetchall()

    def get_inventario_item(self, id_: int):
        with self.con() as c:
            return c.execute("SELECT * FROM inventario WHERE id=?", (id_,)).fetchone()

    def get_inventario_by_tipo(self, tipo: str):
        with self.con() as c:
            return c.execute("SELECT * FROM inventario WHERE tipo=?", (tipo,)).fetchone()

    def add_tipo_combustible(self, tipo, capacidad=20000, minimo_alerta=2000) -> int:
        with self.con() as c:
            cur = c.execute(
                "INSERT INTO inventario (tipo, capacidad, minimo_alerta) VALUES (?,?,?)",
                (tipo, capacidad, minimo_alerta))
            return cur.lastrowid

    def update_tipo_combustible(self, id_, tipo, capacidad, minimo_alerta):
        with self.con() as c:
            c.execute("""UPDATE inventario SET tipo=?, capacidad=?, minimo_alerta=?,
                         actualizado_en=? WHERE id=?""",
                      (tipo, capacidad, minimo_alerta, _now(), id_))

    def toggle_inventario(self, id_: int, activo: int):
        with self.con() as c:
            c.execute("UPDATE inventario SET activo=?, actualizado_en=? WHERE id=?",
                      (activo, _now(), id_))

    def delete_tipo_combustible(self, id_: int) -> bool:
        with self.con() as c:
            usado = c.execute(
                "SELECT 1 FROM despachos WHERE inventario_id=? LIMIT 1", (id_,)
            ).fetchone()
            if usado:
                return False
            c.execute("DELETE FROM inventario WHERE id=?", (id_,))
            return True

    def reabastecer(self, inventario_id: int, litros: float,
                    operador: str = "Sistema", motivo: str = "Reabastecimiento"):
        with self.con() as c:
            c.execute("""UPDATE inventario SET litros_actual = litros_actual + ?,
                         actualizado_en=? WHERE id=?""", (litros, _now(), inventario_id))
            c.execute("""INSERT INTO movimientos_inventario
                         (inventario_id, tipo_movimiento, litros, motivo, operador)
                         VALUES (?, 'entrada', ?, ?, ?)""",
                      (inventario_id, litros, motivo, operador))

    def ajustar(self, inventario_id: int, litros: float, operacion: str,
                operador: str = "Sistema", motivo: str = "Ajuste manual"):
        with self.con() as c:
            if operacion == "add":
                c.execute("""UPDATE inventario SET litros_actual = litros_actual + ?,
                             actualizado_en=? WHERE id=?""", (litros, _now(), inventario_id))
            else:
                c.execute("""UPDATE inventario SET litros_actual = MAX(0, litros_actual - ?),
                             actualizado_en=? WHERE id=?""", (litros, _now(), inventario_id))
            c.execute("""INSERT INTO movimientos_inventario
                         (inventario_id, tipo_movimiento, litros, motivo, operador)
                         VALUES (?, 'ajuste', ?, ?, ?)""",
                      (inventario_id, litros if operacion == "add" else -litros,
                       motivo, operador))

    def get_movimientos(self, inventario_id: int | None = None, limit: int = 200) -> list:
        with self.con() as c:
            if inventario_id:
                return c.execute("""
                    SELECT m.*, i.tipo FROM movimientos_inventario m
                    JOIN inventario i ON i.id = m.inventario_id
                    WHERE m.inventario_id=? ORDER BY m.fecha DESC LIMIT ?
                """, (inventario_id, limit)).fetchall()
            return c.execute("""
                SELECT m.*, i.tipo FROM movimientos_inventario m
                JOIN inventario i ON i.id = m.inventario_id
                ORDER BY m.fecha DESC LIMIT ?
            """, (limit,)).fetchall()

    def stats_inventario(self) -> dict:
        with self.con() as c:
            total = c.execute("SELECT COALESCE(SUM(litros_actual),0) FROM inventario WHERE activo=1").fetchone()[0]
            tipos = c.execute("SELECT COUNT(*) FROM inventario WHERE activo=1").fetchone()[0]
            bajos = c.execute(
                "SELECT COUNT(*) FROM inventario WHERE activo=1 AND litros_actual <= minimo_alerta"
            ).fetchone()[0]
            return {"total_litros": total, "tipos": tipos, "bajo_minimo": bajos}

    # ════════════════════ DESPACHOS ═════════════════════════════
    def add_despacho(self, ben_id: int, inventario_id: int, litros: float,
                     monto: float, operador: str, obs: str = "") -> int:
        with self.con() as c:
            inv = c.execute(
                "SELECT tipo, litros_actual FROM inventario WHERE id=? AND activo=1",
                (inventario_id,),
            ).fetchone()
            if not inv:
                raise ValueError("El tipo de combustible no está disponible.")
            if litros <= 0:
                raise ValueError("Los litros deben ser mayores a cero.")
            if litros > inv["litros_actual"]:
                raise ValueError(
                    f"Inventario insuficiente. Disponible: {inv['litros_actual']:,.0f} L."
                )
            tipo = inv["tipo"]
            cur = c.execute("""
                INSERT INTO despachos
                    (beneficiario_id, inventario_id, tipo, litros, monto_bs, operador, observaciones)
                VALUES (?,?,?,?,?,?,?)
            """, (ben_id, inventario_id, tipo, litros, monto, operador, obs))
            desp_id = cur.lastrowid
            c.execute("""UPDATE inventario SET litros_actual = litros_actual - ?,
                         actualizado_en=? WHERE id=?""", (litros, _now(), inventario_id))
            c.execute("""INSERT INTO movimientos_inventario
                         (inventario_id, tipo_movimiento, litros, referencia_despacho_id,
                          motivo, operador)
                         VALUES (?, 'salida', ?, ?, 'Despacho de combustible', ?)""",
                      (inventario_id, litros, desp_id, operador))
            return desp_id

    def registrar_venta(self, ben_id: int, inventario_id: int, litros: float,
                        monto: float, operador: str, obs: str = "",
                        cobrar_ahora: bool = False, referencia: str = "",
                        metodo_pago_id: int | None = None) -> int:
        """Registra despacho y, opcionalmente, el cobro en una sola operación."""
        from core.business import METODOS_SIN_REFERENCIA
        if monto <= 0:
            raise ValueError("Indique el monto total a cobrar al cliente.")
        with self.con() as c:
            inv = c.execute(
                "SELECT tipo, litros_actual FROM inventario WHERE id=? AND activo=1",
                (inventario_id,),
            ).fetchone()
            if not inv:
                raise ValueError("El tipo de combustible no está disponible.")
            if litros <= 0:
                raise ValueError("Los litros deben ser mayores a cero.")
            if litros > inv["litros_actual"]:
                raise ValueError(
                    f"Inventario insuficiente. Disponible: {inv['litros_actual']:,.0f} L."
                )
            metodo_nombre = None
            if cobrar_ahora:
                if not metodo_pago_id:
                    raise ValueError("Seleccione el método de pago.")
                m = c.execute("SELECT nombre FROM metodos_pago WHERE id=?",
                              (metodo_pago_id,)).fetchone()
                if not m:
                    raise ValueError("Método de pago no válido.")
                metodo_nombre = m["nombre"]
                ref = referencia.strip()
                if metodo_nombre not in METODOS_SIN_REFERENCIA and not ref:
                    raise ValueError(
                        "Indique el número de referencia (transferencia, Biopago, etc.)."
                    )
                if metodo_nombre in METODOS_SIN_REFERENCIA and not ref:
                    ref = "Efectivo"

            tipo = inv["tipo"]
            cur = c.execute("""
                INSERT INTO despachos
                    (beneficiario_id, inventario_id, tipo, litros, monto_bs, operador,
                     observaciones, pagado)
                VALUES (?,?,?,?,?,?,?,?)
            """, (ben_id, inventario_id, tipo, litros, monto, operador, obs,
                  1 if cobrar_ahora else 0))
            desp_id = cur.lastrowid
            c.execute("""UPDATE inventario SET litros_actual = litros_actual - ?,
                         actualizado_en=? WHERE id=?""", (litros, _now(), inventario_id))
            c.execute("""INSERT INTO movimientos_inventario
                         (inventario_id, tipo_movimiento, litros, referencia_despacho_id,
                          motivo, operador)
                         VALUES (?, 'salida', ?, ?, 'Despacho de combustible', ?)""",
                      (inventario_id, litros, desp_id, operador))
            if cobrar_ahora:
                c.execute("""
                    INSERT INTO pagos
                        (despacho_id, beneficiario_id, monto_bs, referencia,
                         metodo_pago_id, metodo, operador)
                    VALUES (?,?,?,?,?,?,?)
                """, (desp_id, ben_id, monto, ref, metodo_pago_id, metodo_nombre, operador))
            return desp_id

    def get_precio_litro(self, tipo_combustible: str) -> float:
        """Precio sugerido por litro según configuración."""
        clave_map = {
            "Gasoil": "precio_litro_gasoil",
            "Gasolina 91": "precio_litro_gasolina_91",
            "Gasolina 95": "precio_litro_gasolina_95",
        }
        clave = clave_map.get(tipo_combustible, "precio_litro_gasoil")
        with self.con() as c:
            row = c.execute(
                "SELECT valor FROM configuracion WHERE clave=?", (clave,)
            ).fetchone()
        try:
            return float(row["valor"]) if row else 0.0
        except (TypeError, ValueError):
            return 0.0

    def get_despachos(self, limit: int = 500, desde: str | None = None,
                      hasta: str | None = None, incluir_anulados: bool = True) -> list:
        params: list = []
        q = """SELECT d.*, b.cedula, b.nombre || ' ' || b.apellido AS beneficiario,
                      b.embarcacion
               FROM despachos d JOIN beneficiarios b ON b.id = d.beneficiario_id"""
        conds = []
        if desde:
            conds.append("d.fecha >= ?"); params.append(desde)
        if hasta:
            conds.append("d.fecha <= ?"); params.append(hasta + " 23:59:59")
        if not incluir_anulados:
            conds.append("d.estado = 'registrado'")
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY d.fecha DESC LIMIT ?"
        params.append(limit)
        with self.con() as c:
            return c.execute(q, params).fetchall()

    def get_despacho(self, id_: int):
        with self.con() as c:
            return c.execute("""
                SELECT d.*, b.cedula, b.nombre || ' ' || b.apellido AS beneficiario
                FROM despachos d JOIN beneficiarios b ON b.id = d.beneficiario_id
                WHERE d.id=?""", (id_,)).fetchone()

    def get_despachos_pendientes(self) -> list:
        with self.con() as c:
            return c.execute("""
                SELECT d.*, b.cedula, b.nombre || ' ' || b.apellido AS beneficiario
                FROM despachos d JOIN beneficiarios b ON b.id = d.beneficiario_id
                WHERE d.pagado = 0 AND d.estado = 'registrado'
                ORDER BY d.fecha DESC""").fetchall()

    def anular_despacho(self, id_: int, motivo: str, operador: str = "Sistema") -> bool:
        with self.con() as c:
            d = c.execute("SELECT * FROM despachos WHERE id=?", (id_,)).fetchone()
            if not d or d["estado"] == "anulado":
                return False
            c.execute("""UPDATE despachos SET estado='anulado', motivo_anulacion=?,
                         actualizado_en=? WHERE id=?""", (motivo, _now(), id_))
            if d["inventario_id"]:
                c.execute("""UPDATE inventario SET litros_actual = litros_actual + ?,
                             actualizado_en=? WHERE id=?""",
                          (d["litros"], _now(), d["inventario_id"]))
                c.execute("""INSERT INTO movimientos_inventario
                             (inventario_id, tipo_movimiento, litros, referencia_despacho_id,
                              motivo, operador)
                             VALUES (?, 'entrada', ?, ?, 'Reverso por anulación de despacho', ?)""",
                          (d["inventario_id"], d["litros"], id_, operador))
            c.execute("""UPDATE pagos SET estado='anulado',
                         motivo_anulacion='Despacho anulado', actualizado_en=?
                         WHERE despacho_id=? AND estado='registrado'""", (_now(), id_))
            return True

    def update_despacho_pendiente(self, id_: int, litros: float, monto_bs: float,
                                  observaciones: str, operador: str = "Sistema") -> bool:
        """Ajusta litros/monto de un despacho no pagado y actualiza inventario."""
        with self.con() as c:
            d = c.execute(
                "SELECT * FROM despachos WHERE id=? AND estado='registrado' AND pagado=0",
                (id_,),
            ).fetchone()
            if not d:
                raise ValueError("Solo se pueden editar despachos pendientes de pago.")
            if not d["inventario_id"]:
                raise ValueError("El despacho no tiene inventario asociado.")
            diff = litros - float(d["litros"])
            if diff != 0:
                inv = c.execute(
                    "SELECT litros_actual FROM inventario WHERE id=?",
                    (d["inventario_id"],),
                ).fetchone()
                if inv["litros_actual"] < diff:
                    falta = diff - inv["litros_actual"]
                    raise ValueError(f"Stock insuficiente: faltan {falta:,.0f} L")
                c.execute(
                    "UPDATE inventario SET litros_actual = litros_actual - ?, actualizado_en=? "
                    "WHERE id=?",
                    (diff, _now(), d["inventario_id"]),
                )
                mov = "salida" if diff > 0 else "entrada"
                c.execute(
                    """INSERT INTO movimientos_inventario
                       (inventario_id, tipo_movimiento, litros, referencia_despacho_id,
                        motivo, operador)
                       VALUES (?, ?, ?, ?, 'Ajuste por edición de despacho', ?)""",
                    (d["inventario_id"], mov, abs(diff), id_, operador),
                )
            c.execute(
                """UPDATE despachos SET litros=?, monto_bs=?, observaciones=?,
                   actualizado_en=? WHERE id=?""",
                (litros, monto_bs, observaciones or None, _now(), id_),
            )
            return True

    def stats_despachos(self, desde: str | None = None, hasta: str | None = None) -> dict:
        params, cond = [], "WHERE estado='registrado'"
        if desde:
            cond += " AND fecha >= ?"; params.append(desde)
        if hasta:
            cond += " AND fecha <= ?"; params.append(hasta + " 23:59:59")
        with self.con() as c:
            r = c.execute(f"""SELECT COUNT(*) n, COALESCE(SUM(litros),0) litros,
                              COALESCE(SUM(monto_bs),0) monto,
                              COALESCE(SUM(pagado),0) pagados
                              FROM despachos {cond}""", params).fetchone()
            return {"n": r["n"], "litros": r["litros"], "monto": r["monto"],
                    "pagados": r["pagados"], "pendientes": r["n"] - r["pagados"]}

    # ════════════════════ MÉTODOS DE PAGO ═══════════════════════
    def get_metodos_pago(self, solo_activos: bool = True) -> list:
        q = "SELECT * FROM metodos_pago"
        if solo_activos:
            q += " WHERE activo=1"
        q += " ORDER BY nombre"
        with self.con() as c:
            return c.execute(q).fetchall()

    # ════════════════════ PAGOS ═════════════════════════════════
    def add_pago(self, despacho_id: int, ben_id: int, monto: float,
                 ref: str, metodo_pago_id: int, operador: str = "Sistema") -> int:
        with self.con() as c:
            m = c.execute("SELECT nombre FROM metodos_pago WHERE id=?",
                          (metodo_pago_id,)).fetchone()
            metodo = m["nombre"] if m else "Biopago"
            cur = c.execute("""
                INSERT INTO pagos
                    (despacho_id, beneficiario_id, monto_bs, referencia,
                     metodo_pago_id, metodo, operador)
                VALUES (?,?,?,?,?,?,?)
            """, (despacho_id, ben_id, monto, ref, metodo_pago_id, metodo, operador))
            c.execute("UPDATE despachos SET pagado=1, actualizado_en=? WHERE id=?",
                      (_now(), despacho_id))
            return cur.lastrowid

    def get_pagos(self, limit: int = 500, incluir_anulados: bool = True) -> list:
        cond = "" if incluir_anulados else "WHERE p.estado='registrado'"
        with self.con() as c:
            return c.execute(f"""
                SELECT p.*, b.cedula, b.nombre || ' ' || b.apellido AS beneficiario
                FROM pagos p JOIN beneficiarios b ON b.id = p.beneficiario_id
                {cond} ORDER BY p.fecha DESC LIMIT ?""", (limit,)).fetchall()

    def get_pago(self, id_: int):
        with self.con() as c:
            return c.execute("""
                SELECT p.*, b.cedula, b.nombre || ' ' || b.apellido AS beneficiario
                FROM pagos p JOIN beneficiarios b ON b.id = p.beneficiario_id
                WHERE p.id=?""", (id_,)).fetchone()

    def anular_pago(self, id_: int, motivo: str, operador: str = "Sistema") -> bool:
        with self.con() as c:
            p = c.execute("SELECT * FROM pagos WHERE id=?", (id_,)).fetchone()
            if not p or p["estado"] == "anulado":
                return False
            c.execute("""UPDATE pagos SET estado='anulado', motivo_anulacion=?,
                         actualizado_en=? WHERE id=?""", (motivo, _now(), id_))
            c.execute("UPDATE despachos SET pagado=0, actualizado_en=? WHERE id=?",
                      (_now(), p["despacho_id"]))
            return True

    def stats_pagos(self, desde: str | None = None, hasta: str | None = None) -> dict:
        params, cond = [], "WHERE estado='registrado'"
        if desde:
            cond += " AND fecha >= ?"; params.append(desde)
        if hasta:
            cond += " AND fecha <= ?"; params.append(hasta + " 23:59:59")
        with self.con() as c:
            total = c.execute(f"SELECT COUNT(*) n, COALESCE(SUM(monto_bs),0) m FROM pagos {cond}",
                              params).fetchone()
            biopago = c.execute(
                f"SELECT COUNT(*) FROM pagos {cond} AND metodo='Biopago'", params
            ).fetchone()[0]
            pend = c.execute(
                "SELECT COUNT(*) FROM despachos WHERE pagado=0 AND estado='registrado'"
            ).fetchone()[0]
            return {"n": total["n"], "recaudado": total["m"], "biopago": biopago,
                    "otros": total["n"] - biopago, "pendientes": pend}

    # ════════════════════ CONFIGURACIÓN ═════════════════════════
    def get_config(self, clave: str, default: str = "") -> str:
        with self.con() as c:
            r = c.execute("SELECT valor FROM configuracion WHERE clave=?", (clave,)).fetchone()
            return r["valor"] if r else default

    def get_all_config(self) -> dict:
        with self.con() as c:
            return {r["clave"]: r["valor"]
                    for r in c.execute("SELECT clave, valor FROM configuracion").fetchall()}

    def set_config(self, clave: str, valor: str):
        with self.con() as c:
            c.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?,?)",
                      (clave, valor))

    # ════════════════════ BITÁCORA ══════════════════════════════
    def log(self, operador_id: int | None, operador: str, modulo: str,
            accion: str, detalle: str = ""):
        with self.con() as c:
            c.execute("""INSERT INTO bitacora
                         (operador_id, operador, modulo, accion, detalle)
                         VALUES (?,?,?,?,?)""",
                      (operador_id, operador, modulo, accion, detalle))

    def get_bitacora(self, limit: int = 300, modulo: str | None = None,
                     desde: str | None = None, hasta: str | None = None) -> list:
        params, conds = [], []
        if modulo:
            conds.append("modulo = ?"); params.append(modulo)
        if desde:
            conds.append("fecha >= ?"); params.append(desde)
        if hasta:
            conds.append("fecha <= ?"); params.append(hasta + " 23:59:59")
        q = "SELECT * FROM bitacora"
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY fecha DESC LIMIT ?"
        params.append(limit)
        with self.con() as c:
            return c.execute(q, params).fetchall()

    # ════════════════════ DASHBOARD / ESTADÍSTICAS ══════════════
    def stats(self) -> dict:
        with self.con() as c:
            inv = c.execute("SELECT COALESCE(SUM(litros_actual),0) FROM inventario WHERE activo=1").fetchone()[0]
            ultimo = c.execute(
                "SELECT MAX(fecha) FROM movimientos_inventario WHERE tipo_movimiento='entrada'"
            ).fetchone()[0]
            return {
                "stock": inv,
                "ultimo_reabast": ultimo,
                "ben_total": c.execute("SELECT COUNT(*) FROM beneficiarios WHERE activo=1").fetchone()[0],
                "desp_total": c.execute("SELECT COUNT(*) FROM despachos WHERE estado='registrado'").fetchone()[0],
                "litros_hoy": c.execute(
                    "SELECT COALESCE(SUM(litros),0) FROM despachos "
                    "WHERE estado='registrado' AND DATE(fecha)=DATE('now','localtime')").fetchone()[0],
                "despachos_hoy": c.execute(
                    "SELECT COUNT(*) FROM despachos "
                    "WHERE estado='registrado' AND DATE(fecha)=DATE('now','localtime')").fetchone()[0],
                "litros_mes": c.execute(
                    "SELECT COALESCE(SUM(litros),0) FROM despachos "
                    "WHERE estado='registrado' AND strftime('%Y-%m',fecha)=strftime('%Y-%m','now','localtime')"
                ).fetchone()[0],
                "pendientes": c.execute(
                    "SELECT COUNT(*) FROM despachos WHERE pagado=0 AND estado='registrado'").fetchone()[0],
                "recaudado": c.execute(
                    "SELECT COALESCE(SUM(monto_bs),0) FROM pagos WHERE estado='registrado'").fetchone()[0],
            }

    def stats_cobros(self) -> dict:
        """Resumen para el módulo de pagos (montos, no conteos del panel de inicio)."""
        pend = self.get_despachos_pendientes()
        with self.con() as c:
            cobrado_hoy = c.execute(
                "SELECT COALESCE(SUM(monto_bs),0) FROM pagos "
                "WHERE estado='registrado' AND DATE(fecha)=DATE('now','localtime')"
            ).fetchone()[0]
        return {
            "monto_pendiente": sum(d["monto_bs"] for d in pend),
            "cobrado_hoy": cobrado_hoy,
        }

    # ── Series temporales para gráficas ──────────────────────────
    def get_series_despachos(self, dias: int = 14) -> list[dict]:
        with self.con() as c:
            rows = c.execute("""
                SELECT DATE(fecha) d, COALESCE(SUM(litros),0) v FROM despachos
                WHERE estado='registrado' AND fecha >= datetime('now','localtime', ?)
                GROUP BY DATE(fecha) ORDER BY d
            """, (f"-{dias} days",)).fetchall()
            return [(r["d"][5:], r["v"]) for r in rows]

    def get_series_pagos(self, dias: int = 14) -> list[dict]:
        with self.con() as c:
            rows = c.execute("""
                SELECT DATE(fecha) d, COALESCE(SUM(monto_bs),0) v FROM pagos
                WHERE estado='registrado' AND fecha >= datetime('now','localtime', ?)
                GROUP BY DATE(fecha) ORDER BY d
            """, (f"-{dias} days",)).fetchall()
            return [(r["d"][5:], r["v"]) for r in rows]

    def get_despachos_tx(self, n: int = 20) -> list[dict]:
        with self.con() as c:
            rows = c.execute("""SELECT id, litros FROM despachos WHERE estado='registrado'
                                ORDER BY id DESC LIMIT ?""", (n,)).fetchall()
            return [(f"#{r['id']}", r["litros"]) for r in reversed(rows)]

    def get_pagos_tx(self, n: int = 20) -> list[dict]:
        with self.con() as c:
            rows = c.execute("""SELECT id, monto_bs FROM pagos WHERE estado='registrado'
                                ORDER BY id DESC LIMIT ?""", (n,)).fetchall()
            return [(f"#{r['id']}", r["monto_bs"]) for r in reversed(rows)]

    def get_series_acumulado_beneficiarios(self, dias: int = 30) -> list[dict]:
        with self.con() as c:
            rows = c.execute("""
                SELECT DATE(creado_en) d, COUNT(*) v FROM beneficiarios
                WHERE creado_en >= datetime('now','localtime', ?)
                GROUP BY DATE(creado_en) ORDER BY d
            """, (f"-{dias} days",)).fetchall()
            acc, out = 0, []
            for r in rows:
                acc += r["v"]
                out.append((r["d"][5:], acc))
            return out

    def get_beneficiarios_tx(self, n: int = 20) -> list[dict]:
        with self.con() as c:
            rows = c.execute("SELECT id FROM beneficiarios ORDER BY id DESC LIMIT ?",
                             (n,)).fetchall()
            return [(f"#{r['id']}", i + 1) for i, r in enumerate(reversed(rows))]
