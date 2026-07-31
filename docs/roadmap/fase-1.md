# Fase 1 — Fundamentos

Estado: completada el 30 de julio de 2026.

## Objetivo

Establecer una base ejecutable, segura, comprobable y modular para la API y la
aplicación móvil.

## Completado

- [x] Registrar el cierre condicional de la Fase 0.
- [x] Crear monorepo con workspaces móvil y API.
- [x] Configurar Python mediante `uv`.
- [x] Inicializar FastAPI con factoría de aplicación.
- [x] Añadir configuración por ambiente.
- [x] Crear formato base de errores.
- [x] Implementar endpoint de salud.
- [x] Crear pruebas iniciales de API.
- [x] Configurar Ruff y pytest.
- [x] Inicializar Expo SDK 56 y Expo Router.
- [x] Crear pantalla inicial móvil.
- [x] Centralizar tokens de diseño.
- [x] Validar TypeScript.
- [x] Aprobar 21 comprobaciones de Expo Doctor.
- [x] Auditar dependencias.
- [x] Probar aislamiento de categorías entre usuarios.
- [x] Verificar que refresh tokens no se almacenen en texto plano.
- [x] Listar y revocar sesiones por dispositivo.
- [x] Probar que un usuario no puede revocar sesiones ajenas.
- [x] Implementar verificación de correo con tokens de un solo uso.
- [x] Implementar recuperación de contraseña y revocación global.
- [x] Configurar entrega local y SMTP por ambiente.
- [x] Implementar pantallas móviles de login, registro y recuperación.
- [x] Guardar tokens móviles con SecureStore.
- [x] Proteger rutas y renovar automáticamente la sesión.
- [x] Añadir enlaces profundos de verificación y cambio de contraseña.

## Pendiente

- [x] Configurar CI.
- [x] Añadir Docker Compose con PostgreSQL.
- [x] Configurar SQLAlchemy y Alembic.
- [x] Crear modelo de usuario.
- [x] Crear categorías base.
- [x] Implementar registro e inicio de sesión.
- [x] Implementar rotación y revocación de tokens.
- [x] Añadir logs estructurados y request ID.
- [x] Añadir configuración y validaciones de staging.
- [x] Añadir una prueba CI de backup y restauración en PostgreSQL aislado.

## Criterios de salida

- API y móvil ejecutan desde un entorno limpio.
- Migraciones de base de datos suben y bajan.
- Registro, login, refresh y logout tienen pruebas.
- Los datos de dos usuarios permanecen aislados.
- CI ejecuta lint, tipos y pruebas.
- No existen vulnerabilidades altas o críticas sin decisión formal.
