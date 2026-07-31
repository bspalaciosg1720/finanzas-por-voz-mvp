# Fase 5 — Reportes, exportaciones y recordatorios

Estado: implementación interna completada. La entrega remota conserva una
validación externa pendiente con scheduler, credenciales y dispositivo físico.

## Bloque 1 — Reportes

- [x] Definir periodos diario, semanal, mensual y anual.
- [x] Resumir ingresos, gastos, balance y cantidad de movimientos.
- [x] Agrupar gastos por categoría.
- [x] Añadir series temporales y comparación con el periodo anterior.
- [x] Implementar la pantalla móvil.

## Bloque 2 — Exportaciones

- [x] Exportar CSV.
- [x] Exportar Excel.
- [x] Exportar PDF.
- [x] Aplicar filtros, zona horaria y moneda de forma consistente.

## Bloque 3 — Recordatorios

- [x] Preferencias y consentimiento por usuario.
- [x] Recordatorio de gastos diarios.
- [x] Recordatorio de ingresos semanales.
- [x] Alertas de presupuesto mediante el canal push preparado.
- [x] Evaluación idempotente y respetuosa de la zona horaria.
- [x] Ejecutar la evaluación mediante un worker invocable por scheduler.

## Criterios de salida

- Todos los periodos usan la zona horaria del usuario.
- Los reportes ignoran movimientos eliminados o no confirmados.
- Los datos no se mezclan entre usuarios ni monedas.
- Las exportaciones coinciden con los filtros visibles.
- Los recordatorios son configurables, revocables y no se duplican.
