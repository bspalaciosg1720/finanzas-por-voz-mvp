# Despliegue privado de producción

## Arquitectura

- Aplicación iOS distribuida por EAS/TestFlight.
- API FastAPI ejecutada desde el `Dockerfile` de la raíz.
- PostgreSQL administrado accesible solamente por la API.
- HTTPS terminado por el proveedor de hosting.

No se necesita que el Mac permanezca encendido ni que el teléfono comparta su red.

## Variables obligatorias de la API

Configurar en el gestor de secretos del proveedor, nunca en Git:

```text
APP_ENV=production
DATABASE_URL=postgresql+psycopg://...
JWT_SECRET=<valor aleatorio de al menos 32 caracteres>
CORS_ORIGINS=["https://dominio-real-de-la-app.example"]
PUBLIC_APP_URL=https://dominio-real-de-la-app.example
EMAIL_DELIVERY_MODE=smtp
EMAIL_FROM=...
SMTP_HOST=...
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
INBOUND_EMAIL_SECRET=<valor aleatorio distinto>
INBOUND_EMAIL_ENABLED=false
PRIVACY_MODE=strict
FINANCIAL_AI_ENABLED=false
```

Para una aplicación exclusivamente nativa, `CORS_ORIGINS` sigue siendo una lista
cerrada y no debe usar `*`. Puede apuntar al dominio público reservado para enlaces de
verificación, recuperación y política de privacidad.

## Orden del primer despliegue

1. Crear PostgreSQL con cifrado en reposo, TLS y backups administrados.
2. Crear el servicio de API desde el `Dockerfile`.
3. Cargar las variables en el gestor de secretos.
4. Ejecutar como tarea previa al despliegue:

   ```bash
   cd apps/api
   /app/.venv/bin/alembic upgrade head
   ```

5. Publicar la API y comprobar `GET /api/v1/health` mediante HTTPS.
6. Confirmar que `/docs` devuelve 404 en producción y que HTTP redirige a HTTPS.
7. Configurar en EAS `EXPO_PUBLIC_API_URL=https://api.example/api/v1`.
8. Generar primero un build iOS `preview`; solo después crear el de producción.

No se deben ejecutar migraciones desde cada réplica al arrancar. El hosting debe usar
una única tarea previa para evitar carreras entre instancias.

## Verificación posterior

- Registrar una cuenta de prueba y cerrar sesión.
- Comprobar rotación y revocación de sesión.
- Registrar ingreso, gasto, presupuesto, deuda y meta.
- Confirmar que las recomendaciones coinciden con los cálculos de la API.
- Eliminar la cuenta desde Perfil y verificar que no puede volver a iniciar sesión.
- Realizar y restaurar un backup en una base aislada.
- Revisar logs para confirmar que no contienen correo, tokens, cuerpos ni cifras.
