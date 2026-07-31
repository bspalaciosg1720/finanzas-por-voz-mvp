# Automatización del análisis de sesiones

La herramienta transforma el registro de sesiones en un informe calculado. No
rellena ni simula datos faltantes.

## Uso

1. Completar `docs/investigacion/03-registro-sesiones.csv`.
2. Desde la raíz ejecutar:

```powershell
python research/analyze_sessions.py
```

3. Revisar `docs/investigacion/07-resultados-calculados.md`.

## Valores aceptados

- Éxito: `yes`, `true`, `1`, `si` o `sí`.
- Tiempo: segundos, por ejemplo `4.8`.
- Confianza: número entre 1 y 5.
- Preferencia: `voice` o `voz` si prefiere dictado.

Las filas vacías del CSV se ignoran.

