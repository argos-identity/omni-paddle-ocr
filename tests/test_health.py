"""
헬스 체크 엔드포인트 테스트
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture()
def client():
    with patch(
        "api.services.ocr_service.ocr_service.preload",
        return_value=None,
    ):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


def test_health_returns_ok(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert isinstance(body["loaded_langs"], list)
