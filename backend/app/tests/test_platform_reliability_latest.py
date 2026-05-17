from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.modules.platform.rate_limiter import enforce_registration_rate_limit
from app.modules.websocket.manager import WebSocketManager


def test_metrics_endpoint_exposes_prometheus_text() -> None:
    client = TestClient(app)

    client.get("/health")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "crsp_http_requests_total" in response.text


def test_websocket_channel_parser_reads_section_id() -> None:
    manager = WebSocketManager()

    assert manager._section_id_from_channel("section:42:availability") == 42
    assert manager._section_id_from_channel("bad:42:availability") is None


def test_disabled_rate_limit_allows_request(monkeypatch) -> None:
    monkeypatch.setattr(settings, "REGISTRATION_RATE_LIMIT_ENABLED", False)

    enforce_registration_rate_limit(123)
