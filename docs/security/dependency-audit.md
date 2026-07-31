# Auditoría inicial de dependencias

- Fecha: 30 de julio de 2026.
- Backend: `uv sync` con lockfile.
- Mobile: npm workspaces con Expo SDK 56.

## Resultado

### Python

La instalación se resolvió correctamente y las pruebas/lint se ejecutaron con el
entorno bloqueado por `uv.lock`.

### npm

`npm audit` informó:

- 0 críticas;
- 0 altas;
- 10 moderadas;
- 0 bajas.

Las alertas son transitivas dentro de la cadena de herramientas Expo, incluyendo
`@expo/cli`, configuración, plugins, Xcode y una versión transitiva de `uuid`.

## Decisión

No ejecutar `npm audit fix --force`. La solución propuesta por npm degrada Expo a
la versión 46, incompatible con React Native 0.85 y el proyecto SDK 56.

`expo-doctor` aprobó 21 de 21 verificaciones. Se mantendrá SDK 56 y se revisarán
las alertas cuando Expo publique actualizaciones compatibles.

## Controles

- Mantener `package-lock.json` versionado.
- Ejecutar `npm audit` en CI sin corrección forzada.
- Bloquear despliegue ante vulnerabilidades altas o críticas.
- Revisar alertas moderadas antes de cada versión.
- No utilizar directamente las APIs vulnerables de `uuid` transitivo.
- Actualizar Expo solamente mediante el proceso oficial de upgrade.

