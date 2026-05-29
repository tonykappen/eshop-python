"""Tests for metrics middleware."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.middleware.metrics_middleware import MetricsMiddleware, add_metrics_middleware


def test_metrics_middleware_skips_health_path() -> None:
    app = FastAPI()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/ping")
    async def ping() -> dict[str, str]:
        return {"pong": "1"}

    app.add_middleware(MetricsMiddleware, exclude_health_checks=True)
    client = TestClient(app)

    assert client.get("/health").status_code == 200
    assert client.get("/api/ping").status_code == 200


def test_add_metrics_middleware_helper() -> None:
    app = FastAPI()
    add_metrics_middleware(app, service_name="test-service")
    assert any(
        middleware.cls is MetricsMiddleware for middleware in app.user_middleware
    )
