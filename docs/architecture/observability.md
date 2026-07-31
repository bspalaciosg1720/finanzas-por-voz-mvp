# Observabilidad inicial

## Request ID

La API acepta `X-Request-ID` cuando contiene entre 1 y 80 caracteres seguros:
letras, números, punto, guion y guion bajo. Si está ausente o es inválido, genera
un UUID.

El identificador aparece en:

- respuesta HTTP;
- errores `application/problem+json`;
- logs de acceso;
- logs de excepciones.

## Logs

La salida utiliza JSON con:

```json
{
  "timestamp": "2026-07-30T16:00:00+00:00",
  "level": "INFO",
  "logger": "api.request",
  "message": "request_completed",
  "request_id": "mobile-request-123",
  "method": "GET",
  "path": "/api/v1/health",
  "status_code": 200,
  "duration_ms": 4.2
}
```

No registrar:

- contraseñas;
- tokens;
- audio o transcripciones;
- descripciones financieras;
- montos exactos;
- cuerpo completo de solicitudes.

## Errores

Los errores esperados, validaciones y fallos inesperados utilizan
`application/problem+json`. Los errores 500 devuelven un mensaje genérico y
conservan el detalle únicamente en logs protegidos.

