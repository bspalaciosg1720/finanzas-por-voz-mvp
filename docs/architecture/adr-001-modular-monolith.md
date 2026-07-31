# ADR-001 — Monolito modular para el MVP

- Estado: propuesto.
- Fecha: 30 de julio de 2026.

## Contexto

El producto necesita autenticación, movimientos, voz, presupuestos y reportes,
pero todavía no existe evidencia de escala ni equipos independientes.

## Decisión

Construir una sola API desplegable con módulos delimitados por dominio. Cada
módulo tendrá contratos, casos de uso, persistencia y pruebas propios.

## Consecuencias

- Despliegue y observabilidad más sencillos.
- Transacciones de base de datos directas.
- Menor costo operativo.
- Se requiere disciplina para evitar dependencias cruzadas.
- Un módulo podrá extraerse si aparecen necesidades reales de escala o aislamiento.

## Alternativas descartadas

- Microservicios desde el inicio: añaden coordinación, red y operación sin
  evidencia que justifique el costo.
- Backend como servicio sin capa de dominio: acelera CRUD, pero puede acoplar la
  lógica financiera y de voz al proveedor.

