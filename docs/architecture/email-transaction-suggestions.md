# Sugerencias de movimientos desde correo

## Objetivo

Convertir los avisos de transacciones enviados por entidades financieras en
sugerencias que el usuario debe confirmar o descartar. El correo nunca crea un
movimiento contable automáticamente.

## Flujo

1. La aplicación obtiene una dirección personal desde
   `GET /api/v1/transaction-suggestions/inbox`.
2. El usuario configura el reenvío de alertas financieras hacia esa dirección.
3. Un proveedor de correo entrante entrega el mensaje al webhook
   `POST /api/v1/transaction-suggestions/inbound-email`.
4. La API valida `X-Inbound-Email-Secret`, identifica al usuario por el alias,
   extrae tipo, valor, comercio y fecha, y guarda una sugerencia.
5. La pantalla de inicio pregunta si se debe registrar o descartar.
6. Al confirmar, la API crea una transacción con origen `integration`.

El identificador del mensaje se resume con SHA-256 y la restricción única por
usuario evita registrar dos veces una misma alerta.

## Privacidad y seguridad

- No se persiste el cuerpo completo ni el asunto del correo.
- Se almacenan únicamente los datos financieros extraídos, el dominio remitente
  y un hash de deduplicación.
- El alias contiene un token aleatorio de 192 bits.
- El webhook se autentica con un secreto diferente de los tokens de usuario.
- Las consultas, confirmaciones y descartes verifican siempre la pertenencia al
  usuario autenticado.

## Configuración pendiente para producción

Se requiere un dominio de correo y un proveedor de recepción entrante (por
ejemplo, Postmark, Mailgun o Amazon SES) que transforme su evento al siguiente
JSON:

```json
{
  "recipient": "movimientos+TOKEN@inbound.ejemplo.com",
  "sender": "alertas@entidad.com",
  "subject": "Compra aprobada",
  "text": "Compra por $42.900 en MERCADO CENTRAL",
  "message_id": "identificador-del-proveedor",
  "received_at": "2026-08-03T10:15:00-05:00"
}
```

Variables obligatorias:

- `INBOUND_EMAIL_DOMAIN`: dominio que recibirá los correos.
- `INBOUND_EMAIL_SECRET`: secreto de al menos 32 caracteres que el adaptador
  enviará en `X-Inbound-Email-Secret`.

Antes de producción también se debe verificar la firma nativa del proveedor en
el adaptador, limitar solicitudes al webhook y ampliar las pruebas del parser
con plantillas anonimizadas de las entidades soportadas.
