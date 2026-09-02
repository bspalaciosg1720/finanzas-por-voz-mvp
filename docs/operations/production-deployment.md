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

## Crear los recursos con Render Blueprint

El repositorio incluye `render.yaml`, que declara la API y PostgreSQL en la misma región,
bloquea el acceso público directo a la base, genera los secretos internos y ejecuta las
migraciones como tarea previa al despliegue.

En Render selecciona **New → Blueprint**, conecta este repositorio y revisa el costo antes
de confirmar. La configuración gratuita solicita `DATABASE_USER` y `DATABASE_PASSWORD`;
introdúcelos en el formulario de secretos y nunca dentro del repositorio.

## Despliegue personal gratuito

El `render.yaml` está preparado para una prueba personal sin costo inicial:

- API en una instancia web gratuita de Render.
- PostgreSQL externo gratuito (recomendado: Supabase), porque PostgreSQL gratuito de
  Render expira después de 30 días.
- La conexión se configura en campos separados para evitar errores con caracteres
  especiales. El backend construye una URL segura y exige TLS automáticamente.
- Las migraciones se ejecutan antes de iniciar Uvicorn en la única instancia gratuita,
  ya que el comando `preDeploy` de Render requiere un plan pago.
- El correo usa el adaptador local y, por tanto, verificación y recuperación por correo
  quedan deshabilitadas en la práctica. Render gratuito bloquea los puertos SMTP comunes.

Esta modalidad es apropiada para probar la aplicación con una cuenta personal. El
servicio puede tardar cerca de un minuto en despertar después de 15 minutos sin tráfico.
Antes de incorporar más usuarios se debe habilitar correo transaccional por HTTPS,
backups y un procedimiento de migración que no se ejecute dentro del proceso web.

Pasos:

1. Crear un proyecto gratuito en Supabase y abrir los datos de conexión de
   `Session pooler`. No compartirlos ni guardarlos en Git.
2. Crear un Blueprint de Render desde este repositorio.
3. Introducir por separado el usuario en `DATABASE_USER` y la contraseña en
   `DATABASE_PASSWORD`. El host, puerto, nombre y TLS ya están configurados.
4. Confirmar que el servicio seleccionado sea `Free` antes de crearlo.
5. Esperar a que el log muestre la migración completa y el inicio de Uvicorn.
6. Comprobar `https://<servicio>.onrender.com/api/v1/health`.

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
