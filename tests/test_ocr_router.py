"""
OCR 라우터 — 입력 유효성 검사 테스트 (OCR 모델 목(mock) 처리)
"""

import pytest


# ─────────────────────────────────────────────
# 정상 요청
# ─────────────────────────────────────────────


def test_ocr_image_success(sync_client, tiny_png_bytes):
    """유효한 이미지 + 지원 언어 → 200 및 결과 구조 검증"""
    response = sync_client.post(
        "/api/v1/ocr",
        files={"file": ("test.png", tiny_png_bytes, "image/png")},
        data={"lang": "korean"},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["total_pages"] == 1
    assert body["lang"] == "korean"
    assert isinstance(body["elapsed_ms"], float)
    assert len(body["pages"]) == 1

    page = body["pages"][0]
    assert page["page"] == 1
    assert isinstance(page["texts"], list)
    assert isinstance(page["extracted_text"], str)
    assert "char_count" in page["metrics"]


# ─────────────────────────────────────────────
# 언어 유효성 검사
# ─────────────────────────────────────────────


def test_ocr_unsupported_lang_returns_422(sync_client, tiny_png_bytes):
    """지원하지 않는 언어 → 422"""
    response = sync_client.post(
        "/api/v1/ocr",
        files={"file": ("test.png", tiny_png_bytes, "image/png")},
        data={"lang": "klingon"},
    )
    assert response.status_code == 422


# ─────────────────────────────────────────────
# 파일 타입 유효성 검사
# ─────────────────────────────────────────────


def test_ocr_unsupported_content_type_returns_415(sync_client):
    """지원하지 않는 MIME 타입 → 415"""
    response = sync_client.post(
        "/api/v1/ocr",
        files={"file": ("test.txt", b"hello", "text/plain")},
        data={"lang": "korean"},
    )
    assert response.status_code == 415


# ─────────────────────────────────────────────
# 빈 파일
# ─────────────────────────────────────────────


def test_ocr_empty_file_returns_400(sync_client):
    """빈 파일 → 400"""
    response = sync_client.post(
        "/api/v1/ocr",
        files={"file": ("empty.png", b"", "image/png")},
        data={"lang": "korean"},
    )
    assert response.status_code == 400


# ─────────────────────────────────────────────
# 파일 크기 초과
# ─────────────────────────────────────────────


def test_ocr_file_too_large_returns_413(sync_client, tiny_png_bytes):
    """MAX_UPLOAD_SIZE 초과 파일 → 413"""
    from unittest.mock import patch

    from api.core.config import settings

    # 최대 크기를 1바이트로 낮춰 강제로 초과시킴
    with patch.object(settings, "MAX_UPLOAD_SIZE", 1):
        response = sync_client.post(
            "/api/v1/ocr",
            files={"file": ("big.png", tiny_png_bytes, "image/png")},
            data={"lang": "korean"},
        )
    assert response.status_code == 413
