# Orinoco v10 — Sistema de Información

Sistema de escritorio para la gestión de los procesos administrativos de la
Estación Fluvial Orinoco C.A. (Barrancas del Orinoco, Estado Monagas).
Desarrollado en Python + CustomTkinter con base de datos SQLite.

## Requisitos
- Python 3.10 o superior
- Dependencia: customtkinter  (pip install customtkinter)

## Cómo ejecutar
    pip install customtkinter
    python main.py

Al iniciar por primera vez se crea automáticamente la base de datos orinoco.db
con datos de demostración. Credenciales por defecto: admin / admin123

Migración automática: si coloca una base de datos orinoco.db de la versión 9
junto a main.py, al ejecutar el sistema se migra sola sin perder datos:
renombra stock -> inventario, cifra las contraseñas existentes, crea las
tablas nuevas y mapea despachos y pagos.

## Roles de usuario
- Operador: crear, ver y editar registros en todos los módulos operativos
  (beneficiarios, inventario, despachos, pagos, reportes) y administrar su
  propia cuenta. NO puede borrar ni anular.
- Administrador: todo lo del operador y además: borrar/anular registros,
  gestionar operadores, configuración y bitácora. Su propia cuenta está
  protegida (no puede desactivarse a sí mismo).

Flujo CRUD: al hacer clic en cualquier registro de una lista se abre su
detalle; desde allí se edita y (solo administrador) se borra/anula. Borrar
siempre exige ver primero el detalle.

## Módulos
1. Inicio - indicadores y despachos recientes.
2. Beneficiarios - CRUD de pescadores (baja lógica).
3. Inventario - combustible por tipo, reabastecer, ajustar y kardex.
4. Despacho - registro de entregas (descuenta inventario), anulación con reverso.
5. Pagos - cobro de despachos (catálogo de métodos), anulación.
6. Reportes - filtros por período y exportación a CSV.
7. Operadores (admin) - CRUD de cuentas, roles y restablecer contraseña.
8. Configuración (admin) - parámetros del sistema.
9. Bitácora (admin) - registro de actividad de los usuarios.
10. Mi cuenta - cambio de contraseña e información del sistema.

## Base de datos (SQLite)
Tablas: operadores, beneficiarios, inventario, movimientos_inventario,
despachos, pagos, metodos_pago, bitacora, configuracion.
- Contraseñas cifradas con PBKDF2-HMAC-SHA256 + salt por usuario.
- Claves foráneas activas, índices en fechas y FKs.
- Los registros financieros se anulan (no se borran) para conservar trazabilidad.
