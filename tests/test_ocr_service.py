"""
OCR 서비스 유닛 테스트 (PaddleOCR 목(mock) 처리)
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from api.services.ocr_service import _compute_metrics, _decode_image_bytes


# ─────────────────────────────────────────────
# _compute_metrics
# ─────────────────────────────────────────────


def test_compute_metrics_basic():
    metrics = _compute_metrics("안녕하세요\n테스트입니다")
    assert metrics.line_count == 2
    assert metrics.word_count == 2
    assert metrics.char_count > 0


def test_compute_metrics_empty():
    metrics = _compute_metrics("")
    assert metrics.char_count == 0
    assert metrics.word_count == 0
    assert metrics.line_count == 0


def test_compute_metrics_single_line():
    metrics = _compute_metrics("Hello World")
    assert metrics.line_count == 1
    assert metrics.word_count == 2


# ─────────────────────────────────────────────
# _decode_image_bytes
# ─────────────────────────────────────────────


def test_decode_image_bytes_valid(tiny_png_bytes):
    img = _decode_image_bytes(tiny_png_bytes)
    assert isinstance(img, np.ndarray)
    assert img.ndim == 3  # H×W×C


def test_decode_image_bytes_invalid():
    with pytest.raises(ValueError, match="이미지 디코딩 실패"):
        _decode_image_bytes(b"not-an-image")


# ─────────────────────────────────────────────
# OCRService.process_image (PaddleOCR 목 처리)
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_process_image_returns_page_result(tiny_png_bytes):
    """PaddleOCR를 목으로 대체해 process_image 로직만 검증"""
    mock_ocr = MagicMock()
    mock_ocr.predict.return_value = [{"rec_texts": ["테스트", "OCR"]}]

    from api.services.ocr_service import OCRService

    svc = OCRService()

    # _get_ocr 와 _decode_image_bytes 를 목 시 파이토피 회피
    with patch.object(svc, "_get_ocr", return_value=mock_ocr), \
         patch("api.services.ocr_service._decode_image_bytes") as mock_decode:
        mock_decode.return_value = np.zeros((10, 10, 3), dtype=np.uint8)
        pages, elapsed = await svc.process_image(tiny_png_bytes, lang="korean")

    assert len(pages) == 1
    assert pages[0].page == 1
    assert "테스트" in pages[0].texts
    assert elapsed >= 0
