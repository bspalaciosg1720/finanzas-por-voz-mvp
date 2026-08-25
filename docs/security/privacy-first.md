# Privacidad y protección de datos

## Garantías por defecto

- `PRIVACY_MODE=strict` impide enviar resúmenes financieros al proveedor de IA.
- `FINANCIAL_AI_ENABLED=false` mantiene las explicaciones basadas en reglas locales.
- `INBOUND_EMAIL_ENABLED=false` evita habilitar direcciones y webhooks de correo financiero.
- La transcripción remota de audio no está configurada; el adaptador activo devuelve
  “no disponible” sin transmitir el archivo.
- Las respuestas de la API usan `Cache-Control: no-store` y cabeceras de seguridad.
- Los tokens móviles se guardan con Expo SecureStore, no en AsyncStorage.
- Los tokens de sesión y de recuperación se almacenan como hashes en el servidor.
- El usuario puede borrar su cuenta con `DELETE /api/v1/me`, confirmando su contraseña
  y enviando `confirmation: "ELIMINAR"`. Las claves foráneas eliminan sus datos asociados.
- Los intentos fallidos de acceso se limitan. La tabla de control guarda una huella HMAC
  del correo y la dirección del cliente, no esos valores en texto.

## Datos que permanecen en el servidor propio

Perfil, movimientos, categorías, presupuestos, deudas, metas, fondo de emergencia,
calendario, configuraciones, alertas y cálculos de salud financiera se procesan en la
API y PostgreSQL propios. Los cálculos financieros son deterministas en código.

## Funciones que pueden compartir datos si se habilitan deliberadamente

- IA financiera: envía indicadores y recomendaciones ya calculados, nunca credenciales;
  utiliza `store: false`. Requiere cambiar a `PRIVACY_MODE=standard`, activar
  `FINANCIAL_AI_ENABLED` y configurar la clave del proveedor.
- Correo entrante: el proveedor de correo procesa el mensaje reenviado antes de llamar
  al webhook. Requiere activar `INBOUND_EMAIL_ENABLED`.
- Notificaciones push y correo de cuenta requieren sus proveedores respectivos y deben
  limitarse al contenido mínimo necesario.

No se deben habilitar estas integraciones sin consentimiento informado y una política
de privacidad que identifique al proveedor, los datos enviados y la finalidad.

## Requisitos de infraestructura antes de producción

1. Usar HTTPS para la API y TLS para PostgreSQL; no publicar directamente el puerto de
   la base de datos.
2. Elegir una base administrada con cifrado en reposo, copias cifradas y región adecuada.
3. Guardar secretos únicamente en el gestor de secretos del hosting. Nunca incluirlos
   en Git, Expo `extra`, código móvil, logs ni capturas.
4. Generar valores únicos y aleatorios para `JWT_SECRET` e `INBOUND_EMAIL_SECRET`.
5. Restringir `CORS_ORIGINS` al dominio real y conservar la documentación API apagada.
6. Configurar el proxy para aceptar encabezados reenviados solamente desde proxies de
   confianza; esto protege la identificación usada por el limitador de acceso.
7. Probar restauración de copias, eliminación de cuenta y revocación de sesiones.
8. Definir periodos de retención para logs y copias. Los logs no deben contener cuerpos,
   tokens, correos, descripciones ni valores financieros.

## Revisión antes de publicar en GitHub

Ejecutar desde la raíz:

```bash
git status --short
git ls-files | rg '(^|/)\.env($|\.)|\.pem$|\.p8$|\.p12$|\.jks$|credentials\.json$'
git log --all -- apps/api/.env apps/mobile/.env
```

El resultado esperado del segundo comando contiene solamente archivos `.env.example`;
el tercero no debe mostrar commits. Además, ejecutar un escáner de secretos sobre todo
el historial antes de cambiar el repositorio a público.

## Límites actuales

- El cifrado en reposo depende del proveedor de PostgreSQL y del almacenamiento de
  copias; debe verificarse al contratarlo.
- HTTPS depende del hosting y del dominio; HSTS se activa cuando `APP_ENV=production`.
- Borrar una cuenta no elimina instantáneamente copias históricas. La política de
  retención debe indicar cuándo expiran y cómo se atiende una solicitud de borrado.
- La eliminación ya puede iniciarse desde Perfil y exige contraseña más confirmación
  explícita antes de borrar definitivamente los datos.
