import json
import logging

import pytest
from app.core.config import Settings
from app.core.logging import JsonFormatter, request_id_context
from app.main import create_app
from fastapi import APIRouter
from fastapi.testclient import TestClient


def test_request_id_is_echoed(client: TestClient) -> None:
    response = client.get(
        "/api/v1/health",
        headers={"X-Request-ID": "mobile-request-123"},
    )
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "mobile-request-123"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_invalid_request_id_is_replaced(client: TestClient) -> None:
    response = client.get(
        "/api/v1/health",
        headers={"X-Request-ID": "invalid request id with spaces"},
    )
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "invalid request id with spaces"


def test_validation_errors_use_problem_json(client: TestClient) -> None:
    response = client.post("/api/v1/auth/register", json={"email": "invalid"})
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["type"].endswith("/validation-error")
    assert body["trace_id"] == response.headers["X-Request-ID"]
    assert body["errors"]


def test_unexpected_errors_do_not_expose_exception() -> None:
    application = create_app()
    router = APIRouter()

    @router.get("/test-error")
    def fail() -> None:
        raise RuntimeError("sensitive database detail")

    application.include_router(router)
    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/test-error")

    assert response.status_code == 500
    assert "sensitive database detail" not in response.text
    assert response.json()["type"].endswith("/internal-error")


def test_json_formatter_includes_request_id() -> None:
    formatter = JsonFormatter()
    token = request_id_context.set("request-456")
    try:
        payload = json.loads(formatter.format(logging.makeLogRecord({"msg": "hello"})))
    finally:
        request_id_context.reset(token)
    assert payload["message"] == "hello"
    assert payload["request_id"] == "request-456"


def test_staging_rejects_development_secrets() -> None:
    with pytest.raises(ValueError):
        Settings(app_env="staging")
