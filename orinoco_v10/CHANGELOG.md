# CHANGELOG — v9 -> v10

Cada cambio responde a un defecto detectado en la v9.

## Seguridad
- Contraseñas en texto plano -> ahora PBKDF2-HMAC-SHA256 con salt por usuario.
  La migración cifra automáticamente las claves existentes.
- Nueva recuperación de contraseña por pregunta de seguridad (pantalla de acceso)
  y restablecimiento por parte del administrador.

## Base de datos (más clara y completa)
- Tabla "stock" (en inglés) renombrada a "inventario"; eliminado todo el spanglish.
- "inventario" pasa a tener una fila por tipo de combustible (entidad CRUD real).
- Nueva tabla "movimientos_inventario" (kardex): entradas, salidas y ajustes.
- Nueva tabla "metodos_pago" (catálogo) en lugar de textos fijos.
- Nueva tabla "bitacora" (auditoría de acciones de usuarios).
- Nueva tabla "configuracion" (parámetros del sistema).
- Columna ref_biopago (específica) eliminada; el pago guarda referencia y método genéricos.
- Añadidas columnas de auditoría (creado_en / actualizado_en) y de estado.
- Claves foráneas activadas (ON DELETE), índices en fechas y FKs.

## Funcionalidad (CRUD completo por módulo)
- Despachos y pagos: además de crear/listar, ahora se pueden ver en detalle y
  ANULAR (con motivo). La anulación de un despacho devuelve el combustible al
  inventario; la de un pago deja el despacho nuevamente pendiente.
- Operadores: CRUD completo (crear, ver, editar, activar/desactivar) y
  restablecer contraseña.
- Inventario: crear/editar/eliminar tipos, reabastecer, ajustar y ver kardex.
- Reportes: exportación a CSV.

## Roles y permisos
- Permisos reforzados: solo el administrador puede borrar/anular; el operador
  crea, ve y edita pero no borra.
- Módulos exclusivos de administrador: Operadores, Configuración, Bitácora.
- La cuenta del administrador en sesión queda protegida: no puede desactivarse
  a sí mismo (se muestra distintivo "Protegido" en lugar del botón).

## Experiencia de usuario (UI)
- Flujo CRUD por detalle: clic en un registro abre su ficha; desde allí se
  edita o se borra/anula.
- Confirmaciones con motivo para acciones destructivas.
- Navegación lateral por rol con sección "Administración".
- Datos de demostración realistas en instalaciones nuevas.
