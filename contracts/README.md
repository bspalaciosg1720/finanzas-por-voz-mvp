# Contratos preliminares de API

`openapi.yaml` define la primera frontera entre aplicación móvil y backend.

## Decisiones incorporadas

- Versionado `/api/v1`.
- JWT Bearer.
- Idempotencia obligatoria al crear movimientos y confirmar voz.
- Dinero expresado como enteros.
- Confirmación de voz separada de la interpretación.
- Errores con `application/problem+json`.
- Paginación mediante cursor.
- Borrado lógico de movimientos.
- Respuestas `404` que no revelan recursos de otros usuarios.

## Validar

```powershell
python contracts/validate_openapi.py
```

El contrato es preliminar y puede cambiar después de la Fase 0.

La validación local actual comprueba estructura y elementos obligatorios. La
validación semántica completa de OpenAPI debe añadirse al CI de la Fase 1.
