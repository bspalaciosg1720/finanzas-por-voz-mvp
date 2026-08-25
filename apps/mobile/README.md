# Aplicación móvil

Aplicación Expo/React Native del MVP.

```bash
npm ci
npm run mobile:start
```

Incluye autenticación, dashboard, movimientos manuales y por voz, salud
financiera explicable, confirmación editable, presupuestos, metas de ahorro,
reportes, exportaciones, recordatorios y registro de dispositivos para
notificaciones.

La sección Salud también ofrece fondo de emergencia, calendario financiero,
simulaciones de solo lectura, historial del puntaje y un asistente explicativo.
La IA es opcional y el backend utiliza reglas locales cuando está desactivada.

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

## Compilar para un iPhone

Después de vincular el proyecto con una cuenta Expo y configurar
`EXPO_PUBLIC_API_URL` en EAS para que apunte a la API HTTPS:

```bash
npx eas-cli build:configure
npx eas-cli build --platform ios --profile preview
```

El perfil `preview` crea una distribución interna. Para TestFlight/App Store:

```bash
npx eas-cli build --platform ios --profile production
npx eas-cli submit --platform ios --profile production
```

No guardes claves de App Store Connect ni certificados dentro del repositorio.
