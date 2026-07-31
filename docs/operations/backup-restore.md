# Backup y restauración de PostgreSQL

## Objetivo

Respaldar datos sin incluir credenciales en archivos o argumentos visibles y
probar periódicamente que el respaldo puede restaurarse.

## Política inicial

- Backup administrado diario.
- Retención diaria: 14 días.
- Retención semanal: 8 semanas.
- Cifrado en tránsito y reposo.
- Acceso limitado al servicio y responsables de operación.
- Prueba de restauración mensual en una base aislada.
- Nunca restaurar directamente sobre producción durante una prueba.

## Backup manual controlado

Configurar las credenciales mediante un mecanismo seguro del proveedor o
`PGPASSFILE`. No escribir la contraseña dentro del comando.

```powershell
pg_dump `
  --host $env:PGHOST `
  --username $env:PGUSER `
  --dbname $env:PGDATABASE `
  --format custom `
  --no-owner `
  --file finanzas-backup.dump
```

## Restauración de prueba

Crear primero una base vacía y aislada:

```powershell
createdb `
  --host $env:PGHOST `
  --username $env:PGUSER `
  finanzas_restore_test

pg_restore `
  --host $env:PGHOST `
  --username $env:PGUSER `
  --dbname finanzas_restore_test `
  --no-owner `
  --no-privileges `
  finanzas-backup.dump
```

Validar:

- versión de migración;
- número de categorías del sistema;
- integridad de claves foráneas;
- lectura de usuarios y sesiones;
- ausencia de errores en logs.

Eliminar la base de prueba únicamente después de verificar que el nombre resuelto
es exactamente `finanzas_restore_test`.

## Automatización

El CI crea una base `finanzas_restore`, restaura el backup recién generado y
verifica las 11 categorías del sistema. Los backups de producción deben utilizar
el mecanismo administrado del proveedor y almacenamiento con retención bloqueada.

## Recuperación

Antes de una restauración real:

1. Declarar incidente y responsable.
2. Identificar punto de recuperación.
3. Suspender escrituras si corresponde.
4. Restaurar primero en un ambiente aislado.
5. Validar integridad y versión.
6. Documentar pérdida estimada de datos.
7. Obtener autorización antes de cambiar producción.

