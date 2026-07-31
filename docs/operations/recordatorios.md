# Operación de recordatorios

## Comando

```bash
uv run finanzas-reminders
```

El comando evalúa usuarios con alguna preferencia activa, envía los avisos
pendientes a sus dispositivos activos y presenta un resumen sin exponer tokens.

## Programación

Ejecutar cada cinco minutos mediante el scheduler de la plataforma. No se
requiere un proceso permanentemente residente: la restricción única por usuario,
tipo y periodo hace que ejecuciones concurrentes o repetidas no generen una
segunda entrega después del éxito.

## Reintentos

- El estado inicial es `pending`.
- Solo cambia a `delivered` cuando todos los dispositivos activos aceptan el
  mensaje.
- Sin dispositivos o con el adaptador deshabilitado, el aviso permanece
  pendiente.
- Un fallo de un dispositivo se registra en el resultado del lote y conserva el
  aviso para el siguiente intento.

## Despliegue pendiente

El adaptador remoto y sus credenciales deben configurarse en staging. Hasta
entonces, el modo deshabilitado es el valor seguro y el adaptador falso cubre la
regresión automatizada.
