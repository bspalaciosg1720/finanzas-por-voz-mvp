# Fase 3 — Registro por voz

Estado: en curso. Contrato e interpretación determinista inicial completados.

## Objetivo

Permitir registrar ingresos y gastos mediante lenguaje natural, con una
confirmación clara cuando falte información o exista ambigüedad.

## Bloque 1 — Contrato de interpretación

- [x] Definir esquema de transcripción e interpretación.
- [x] Normalizar montos expresados en español.
- [x] Inferir ingreso o gasto.
- [x] Resolver categorías del sistema y del usuario.
- [x] Extraer descripción, fecha y hora.
- [x] Calcular confianza heurística por campo.

## Bloque 2 — Servicio de voz

- [x] Capturar audio en el dispositivo.
- [x] Implementar contrato intercambiable con adaptadores deshabilitado y falso.
- [ ] Implementar y habilitar el proveedor Speech-to-Text real.
- [x] Aplicar límites de 15 segundos y 5 MB.
- [x] Mantener en caché y eliminar audio al cancelar o cerrar.
- [x] Gestionar permisos, errores y cancelación.

## Bloque 3 — Confirmación

- [x] Mostrar y corregir la transcripción.
- [x] Mostrar monto, tipo, categoría, fecha y descripción interpretados.
- [x] Corregir tipo, monto, categoría, descripción y fecha.
- [x] Exigir confirmación antes de guardar.
- [x] Guardar mediante la API idempotente de movimientos.

## Bloque 4 — Calidad

- [x] Pruebas unitarias iniciales del parser.
- [x] Dataset sintético de 150 expresiones colombianas integrado en pytest.
- [x] Pruebas iniciales de ambigüedad y montos extremos.
- [x] Métricas de éxito, corrección y abandono sin contenido financiero.
- [ ] Pruebas de accesibilidad y privacidad.

## Criterios de salida

- El flujo feliz requiere hablar, confirmar y guardar.
- Nunca se guarda silenciosamente una interpretación ambigua.
- Los reintentos de red no duplican movimientos.
- El audio no se conserva sin consentimiento explícito.
- La precisión se mide con el dataset acordado en la Fase 0.
