# Fase 2 — Movimientos financieros

Estado: completada el 30 de julio de 2026.

## Objetivo

Permitir registrar, consultar, editar y eliminar ingresos y gastos con exactitud,
aislamiento por usuario e idempotencia.

## Bloque 1 — Dominio y persistencia

- [x] Crear modelo y migración de movimientos.
- [x] Almacenar montos como enteros positivos.
- [x] Validar moneda ISO de tres letras.
- [x] Asociar categorías propias o del sistema.
- [x] Añadir borrado lógico.
- [x] Añadir índices por usuario, fecha, tipo y categoría.
- [x] Añadir clave de idempotencia única por usuario.

## Bloque 2 — API

- [x] Crear movimiento.
- [x] Obtener detalle.
- [x] Listar mediante cursor.
- [x] Filtrar por fecha, tipo y categoría.
- [x] Buscar por descripción.
- [x] Editar movimiento.
- [x] Eliminar y restaurar.
- [x] Impedir acceso entre usuarios.

## Bloque 3 — Aplicación móvil

- [x] Lista de movimientos.
- [x] Formulario manual compacto.
- [x] Detalle y edición.
- [x] Confirmación de eliminación.
- [x] Búsqueda y filtros por tipo, fecha y categoría.
- [x] Paginación móvil mediante cursor.
- [x] Estados vacío, carga, error y sin conexión.

## Bloque 4 — Dashboard

- [x] Saldo actual.
- [x] Ingresos y gastos del mes.
- [x] Categoría de mayor gasto.
- [x] Movimientos recientes.
- [x] Comparación equivalente con el mes anterior.

## Evidencia de cierre

- 32 pruebas backend aprobadas.
- Lint de la API aprobado.
- TypeScript móvil aprobado.
- Cálculos aislados por usuario, moneda principal y zona horaria.
- Movimientos eliminados excluidos de agregados y actividad reciente.
- Pantallas móviles conectadas a la API, sin cifras simuladas.

La ejecución contra PostgreSQL real permanece cubierta por CI, debido a que
Docker no está disponible en el equipo local.

## Criterios de salida

- CRUD completo probado.
- Dos usuarios no pueden observar ni mutar datos ajenos.
- Reintentos no duplican movimientos.
- Los cálculos monetarios no utilizan punto flotante.
- Filtros y paginación son deterministas.
- Aplicación móvil completa el registro manual.
- Dashboard coincide con consultas de base de datos.
