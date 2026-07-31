# Fase 4 — Presupuestos, alertas y metas

Estado: implementación interna completada. La entrega push conserva una
validación externa pendiente con credenciales, build y dispositivo físico. La
Fase 3 también conserva validaciones externas pendientes.

## Bloque 1 — Presupuestos

- [x] Modelo y migración de presupuestos mensuales.
- [x] CRUD por categoría.
- [x] Progreso del mes en la zona horaria del usuario.
- [x] Estados normal, advertencia y excedido.
- [x] Aislamiento entre usuarios.
- [x] Pantalla móvil de presupuestos.

## Bloque 2 — Alertas

- [x] Detectar el umbral configurable, inicialmente 80 %.
- [x] Evitar alertas duplicadas por presupuesto, mes y nivel.
- [x] Mostrar estados de alerta dentro de la aplicación.
- [x] Preparar registro revocable de dispositivos y adaptadores de entrega push.

## Bloque 3 — Metas de ahorro

- [x] Crear, editar y eliminar metas.
- [x] Registrar y retirar aportes.
- [x] Calcular avance y completar/reactivar automáticamente.
- [x] Mostrar fecha objetivo.
- [x] Pantalla móvil de metas.

## Criterios de salida

- Los gastos del mes coinciden con los movimientos confirmados.
- Los presupuestos no mezclan usuarios, categorías ni monedas.
- Las alertas no se repiten para el mismo umbral y periodo.
- Los aportes a metas usan montos enteros.
- Presupuestos y metas tienen estados vacíos, carga y error.

## Validación externa pendiente

- Configurar el `projectId` y las credenciales de Expo/EAS.
- Crear un build de desarrollo; Expo Go no cubre la entrega push remota.
- Registrar un dispositivo físico iOS o Android mediante consentimiento
  explícito.
- Enviar una notificación real y comprobar recepción, apertura y revocación.

Estas pruebas no invalidan la implementación interna, pero son obligatorias
antes de habilitar notificaciones en producción.
