# API

## Desarrollo local

```powershell
cd apps/api
uv sync --extra dev
docker compose up -d postgres
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

API:

- Salud: `http://localhost:8000/api/v1/health`
- OpenAPI: `http://localhost:8000/docs`

## Pruebas

```powershell
uv run pytest
uv run ruff check .
```

No copies `.env.example` sobre `.env` sin reemplazar los secretos de ejemplo.

Los ambientes `staging` y `production` rechazan secretos de desarrollo,
credenciales `change-me`, correo local y orígenes CORS locales.

En desarrollo, los correos de verificación y recuperación se escriben en
`tmp/mailbox`, que está excluido de Git.

Si Docker no está disponible, las migraciones pueden inspeccionarse sin conexión:

```powershell
uv run alembic upgrade head --sql
```

El procedimiento de backup y restauración se encuentra en
`docs/operations/backup-restore.md`.
