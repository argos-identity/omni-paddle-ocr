"""
OCR 서비스 — PaddleOCR 싱글톤 관리 및 비동기 처리
"""

import asyncio
import io
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple

import numpy as np

# PaddleOCR 초기화 로그 최소화
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

from paddleocr import PaddleOCR

from api.core.config import settings
from api.schemas.ocr_schema import PageResult, TextMetrics

logger = logging.getLogger(__name__)


def _compute_metrics(text: str) -> TextMetrics:
    """텍스트 통계 계산"""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    words = text.split()
    return TextMetrics(
        char_count=len(text.replace("\n", "")),
        word_count=len(words),
        line_count=len(lines),
    )


def _decode_image_bytes(data: bytes) -> np.ndarray:
    """bytes → numpy BGR 이미지 (OpenCV 형식)"""
    import cv2

    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(
            "이미지 디코딩 실패: 지원하지 않는 포맷이거나 손상된 파일입니다."
        )
    return img


def _pdf_to_images(data: bytes, dpi: int = settings.PDF_DPI) -> List[np.ndarray]:
    """PDF bytes → 페이지별 numpy BGR 이미지 리스트"""
    import pypdfium2 as pdfium
    import cv2

    pdf = pdfium.PdfDocument(data)
    images = []
    scale = dpi / 72  # pdfium 기본 72dpi 기준 스케일

    for page_index in range(len(pdf)):
        page = pdf[page_index]
        bitmap = page.render(scale=scale, rotation=0)
        pil_img = bitmap.to_pil()

        # PIL → numpy BGR
        img_rgb = np.array(pil_img.convert("RGB"))
        img_bgr = img_rgb[:, :, ::-1].copy()
        images.append(img_bgr)

    pdf.close()
    return images


def _run_ocr_on_image(ocr: PaddleOCR, image: np.ndarray) -> List[str]:
    """단일 이미지에 OCR 실행 → 텍스트 리스트 반환"""
    result = ocr.predict(image)
    texts = []
    for page_result in result:
        texts.extend(page_result.get("rec_texts", []))
    return texts


class OCRService:
    """
    PaddleOCR 서비스 싱글톤.
    언어별 OCR 인스턴스를 캐싱하고 ThreadPoolExecutor로 비동기 처리.
    """

    def __init__(self):
        self._instances: Dict[str, PaddleOCR] = {}
        self._executor = ThreadPoolExecutor(max_workers=settings.OCR_WORKERS)
        self._lock = asyncio.Lock()

    async def _get_ocr(self, lang: str) -> PaddleOCR:
        """언어별 OCR 인스턴스 반환 (없으면 생성)"""
        if lang not in self._instances:
            async with self._lock:
                # double-checked locking
                if lang not in self._instances:
                    logger.info(f"PaddleOCR 모델 로딩: lang={lang}")
                    loop = asyncio.get_event_loop()
                    ocr = await loop.run_in_executor(
                        self._executor,
                        lambda: PaddleOCR(lang=lang, text_detection_model_name=settings.OCR_DET_MODEL, text_recognition_model_name=settings.OCR_REC_MODEL),
                    )
                    self._instances[lang] = ocr
                    logger.info(f"PaddleOCR 모델 로딩 완료: lang={lang}")
        return self._instances[lang]

    async def process_image(
        self, data: bytes, lang: str = settings.DEFAULT_LANG
    ) -> Tuple[List[PageResult], float]:
        """
        이미지 bytes → OCR 실행

        Returns:
            (pages, elapsed_ms)
        """
        ocr = await self._get_ocr(lang)
        loop = asyncio.get_event_loop()

        start = time.time()

        def _run() -> List[str]:
            img = _decode_image_bytes(data)
            return _run_ocr_on_image(ocr, img)

        texts = await loop.run_in_executor(self._executor, _run)
        elapsed_ms = (time.time() - start) * 1000

        extracted = "\n".join(texts)
        page = PageResult(
            page=1,
            texts=texts,
            extracted_text=extracted,
            metrics=_compute_metrics(extracted),
        )
        return [page], elapsed_ms

    async def process_pdf(
        self, data: bytes, lang: str = settings.DEFAULT_LANG
    ) -> Tuple[List[PageResult], float]:
        """
        PDF bytes → 페이지별 OCR 실행

        Returns:
            (pages, elapsed_ms)
        """
        ocr = await self._get_ocr(lang)
        loop = asyncio.get_event_loop()

        start = time.time()

        def _run() -> List[Tuple[int, List[str]]]:
            images = _pdf_to_images(data)
            results = []
            for idx, img in enumerate(images, start=1):
                texts = _run_ocr_on_image(ocr, img)
                results.append((idx, texts))
            return results

        raw_pages = await loop.run_in_executor(self._executor, _run)
        elapsed_ms = (time.time() - start) * 1000

        pages = []
        for page_num, texts in raw_pages:
            extracted = "\n".join(texts)
            pages.append(
                PageResult(
                    page=page_num,
                    texts=texts,
                    extracted_text=extracted,
                    metrics=_compute_metrics(extracted),
                )
            )

        return pages, elapsed_ms

    @property
    def loaded_langs(self) -> List[str]:
        return list(self._instances.keys())

    async def preload(self, lang: str = settings.DEFAULT_LANG) -> None:
        """앱 시작 시 기본 언어 모델 사전 로드"""
        await self._get_ocr(lang)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False)


# 싱글톤 인스턴스
ocr_service = OCRService()
