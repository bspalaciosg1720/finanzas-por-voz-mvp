# ADR-002 — Interpretar y confirmar antes de persistir

- Estado: propuesto, pendiente de validar fatiga de confirmación.
- Fecha: 30 de julio de 2026.

## Contexto

Un error de monto o tipo puede alterar el saldo y reducir la confianza. La salida
de Speech-to-Text y la clasificación automática son probabilísticas.

## Decisión

Separar el proceso en dos operaciones:

1. crear una interpretación temporal;
2. confirmar valores finales y crear el movimiento.

La confirmación utiliza idempotencia y nunca confía ciegamente en los valores
temporales enviados previamente.

## Consecuencias

- El usuario controla lo que se guarda.
- Es posible medir correcciones por campo.
- La interpretación puede expirar y eliminar su audio.
- El flujo añade una interacción que debe validarse en usabilidad.

