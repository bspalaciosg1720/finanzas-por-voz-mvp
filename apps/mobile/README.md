# Aplicación móvil

Aplicación Expo/React Native del MVP.

```bash
npm ci
npm run mobile:start
```

Incluye autenticación, dashboard, movimientos manuales y por voz, confirmación
editable, presupuestos, metas de ahorro, reportes, exportaciones, recordatorios
y registro de dispositivos para notificaciones.

La captura de audio solicita permisos y lo envía a la API. Para obtener una
transcripción real, el backend aún necesita un proveedor Speech-to-Text y sus
credenciales; sin él se mantiene la alternativa editable.

## API

Crear `.env` a partir de `.env.example`. En un dispositivo físico, reemplazar
`localhost` por una dirección accesible desde el teléfono.

Los access y refresh tokens se almacenan con Expo SecureStore y nunca en
AsyncStorage.

Las rutas privadas redirigen al login cuando no existe sesión. Si un access token
expira, el cliente rota el refresh token, persiste el nuevo par y reintenta la
solicitud una sola vez.
