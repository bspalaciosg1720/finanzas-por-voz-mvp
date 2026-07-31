# Movimientos financieros

## Decisiones del dominio

- Los montos se reciben y almacenan como enteros positivos en la unidad mínima
  de la moneda (`amount_minor`). No se usa punto flotante.
- El signo contable se deriva del tipo `income` o `expense`; nunca se guarda un
  monto negativo.
- La moneda usa tres letras mayúsculas. La primera versión admite cualquier
  código con ese formato y podrá incorporar un catálogo ISO formal más adelante.
- La fecha del movimiento exige zona horaria. Los filtros por día se convierten
  desde la zona horaria del usuario a límites UTC.
- Una categoría es válida si pertenece al sistema o al usuario autenticado.
- La eliminación es lógica mediante `deleted_at` y puede revertirse.

## Idempotencia

`POST /api/v1/transactions` exige el encabezado `Idempotency-Key` con un UUID.
La combinación de usuario y clave es única.

- Repetir la misma solicitud devuelve el movimiento existente.
- Reutilizar la clave con otro contenido devuelve conflicto.
- La comparación utiliza una huella SHA-256 del contenido normalizado.

Esto permite reintentar solicitudes móviles después de una interrupción sin
duplicar ingresos o gastos.

## Listado y filtros

El listado usa un cursor opaco construido con `occurred_at` e `id`. Ese segundo
campo mantiene un orden determinista cuando varios movimientos tienen la misma
fecha.

Los filtros disponibles son:

- rango de fechas locales inclusivo;
- tipo;
- categoría;
- búsqueda parcial en la descripción.

Todos los accesos comienzan por `user_id`. Un recurso de otro usuario se
presenta como inexistente para no revelar su presencia.

## Índices

La migración crea índices compuestos para los principales recorridos:

- usuario, fecha e identificador;
- usuario, categoría y fecha;
- usuario, tipo y fecha.

## Verificación

La cobertura automatizada comprueba montos y fechas, aislamiento entre usuarios,
idempotencia, conflicto de claves, edición, borrado, restauración, filtros,
búsqueda, categorías inválidas y paginación por cursor.
