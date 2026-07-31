# Decisión de salida — Fase 1

- Fecha: 30 de julio de 2026.
- Resultado: aprobada para iniciar Fase 2.

## Criterios

| Criterio | Evidencia | Estado |
|---|---|---|
| API y móvil instalables | `uv.lock`, `package-lock.json`, documentación | Cumple |
| Migraciones suben y bajan | Alembic offline, SQLite temporal y CI PostgreSQL | Cumple |
| Autenticación probada | Registro, login, refresh, logout y recuperación | Cumple |
| Aislamiento | Categorías y sesiones entre dos usuarios | Cumple |
| Calidad automatizada | Ruff, pytest, TypeScript, Expo Doctor | Cumple |
| CI definido | Backend, mobile, validación, PostgreSQL y backup | Cumple |
| Sin vulnerabilidades altas/críticas | Auditoría npm documentada | Cumple |

## Resultado integrado

- 24 pruebas del backend.
- 6 pruebas del parser.
- 3 pruebas del analizador de investigación.
- TypeScript sin errores.
- Ruff sin errores.
- Expo Doctor 21/21 en la última revisión de configuración.
- Contrato OpenAPI estructuralmente válido.

## Excepción operativa

El workflow remoto, staging y la restauración PostgreSQL del CI no se han
ejecutado porque el repositorio todavía no está publicado y Docker no está
instalado localmente.

Esto no bloquea el desarrollo de Fase 2, pero sí bloquea cualquier despliegue a
producción. Antes de desplegar:

1. publicar el repositorio;
2. ejecutar CI completo;
3. crear staging;
4. validar migraciones y restauración;
5. resolver cualquier fallo.

## Riesgo heredado

La validación con usuarios de la Fase 0 sigue pendiente según la aceptación de
riesgo registrada. Debe ejecutarse antes de invertir en funciones posteriores al
núcleo del MVP.

