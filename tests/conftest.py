"""
pytest 공통 픽스처 및 설정
"""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from api.main import app
from api.schemas.ocr_schema import PageResult, TextMetrics


# ─────────────────────────────────────────────
# 공통 픽스처
# ─────────────────────────────────────────────


@pytest.fixture(scope="session")
def mock_ocr_page() -> PageResult:
    """가짜 OCR 결과 단일 페이지"""
    return PageResult(
        page=1,
        texts=["안녕하세요", "테스트입니다"],
        extracted_text="안녕하세요\n테스트입니다",
        metrics=TextMetrics(char_count=12, word_count=2, line_count=2),
    )


@pytest.fixture(scope="session")
def tiny_png_bytes() -> bytes:
    """1×1 픽셀 PNG (유효한 이미지 바이트) — Pillow로 생성"""
    from PIL import Image
    import io
    img = Image.new("RGB", (1, 1), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
def sync_client(mock_ocr_page):
    """OCR 서비스를 목(mock)으로 대체한 동기 TestClient"""
    elapsed = 42.0

    with (
        patch(
            "api.services.ocr_service.ocr_service.process_image",
            new_callable=AsyncMock,
            return_value=([mock_ocr_page], elapsed),
        ),
        patch(
            "api.services.ocr_service.ocr_service.preload",
            new_callable=AsyncMock,
        ),
    ):
        with TestClient(app, raise_server_exceptions=True) as client:
            yield client


@pytest.fixture()
async def async_client(mock_ocr_page):
    """OCR 서비스를 목(mock)으로 대체한 비동기 AsyncClient"""
    elapsed = 42.0

    with (
        patch(
            "api.services.ocr_service.ocr_service.process_image",
            new_callable=AsyncMock,
            return_value=([mock_ocr_page], elapsed),
        ),
        patch(
            "api.services.ocr_service.ocr_service.preload",
            new_callable=AsyncMock,
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client
