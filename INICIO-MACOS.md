# Continuar el proyecto en macOS

## Requisitos

- macOS con Xcode Command Line Tools.
- Python 3.12 o 3.13.
- Node.js LTS y npm.
- `uv`.
- Docker Desktop, recomendado para PostgreSQL.
- Xcode y Android Studio solo si se usarán sus simuladores.

## Instalación

Desde la carpeta descomprimida:

```bash
uv sync --package finanzas-api --extra dev
npm ci
cp apps/api/.env.example apps/api/.env
cp apps/mobile/.env.example apps/mobile/.env
```

Los archivos `.env` reales no viajan en el ZIP. Completa sus valores localmente
y no los subas al repositorio.

## Base de datos y API

```bash
docker compose up -d
cd apps/api
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

La documentación de la API estará en `http://localhost:8000/docs`.

## Aplicación móvil

En otra terminal, desde la raíz:

```bash
npm run mobile:start
```

Para un iPhone físico, `EXPO_PUBLIC_API_URL` debe usar la IP local del Mac, no
`localhost`, por ejemplo:

```text
EXPO_PUBLIC_API_URL=http://192.168.1.20:8000/api/v1
```

El iPhone y el Mac deben estar en la misma red y el firewall debe permitir la
conexión.

## Verificación inicial

```bash
uv run --package finanzas-api ruff check apps/api
uv run --package finanzas-api pytest apps/api/tests
npm run mobile:typecheck
npx expo-doctor
```

La línea base al crear este paquete era de 217 pruebas backend aprobadas,
TypeScript limpio y Expo Doctor 21/21.

## Funciones que requieren credenciales externas

- Transcripción remota de voz.
- Expo/EAS y entrega push real.
- SMTP de staging/producción.
- Publicación en App Store o Play Store.

Mantén esas credenciales fuera del código y de los archivos comprimidos.
