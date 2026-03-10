"""
OCR 라우터
"""

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from api.core.config import settings
from api.schemas.ocr_schema import HealthResponse, OCRResponse
from api.services.ocr_service import ocr_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["OCR"])


@router.post(
    "/ocr",
    response_model=OCRResponse,
    summary="이미지 / PDF OCR",
    description=(
        "업로드된 이미지(JPEG, PNG, BMP, TIFF, WebP) 또는 PDF를 OCR 처리하여 "
        "텍스트를 추출합니다. PDF는 페이지별로 결과가 반환됩니다."
    ),
)
async def run_ocr(
    file: UploadFile = File(..., description="이미지 또는 PDF 파일"),
    lang: str = Form(
        default=settings.DEFAULT_LANG,
        description=f"OCR 언어. 지원: {settings.SUPPORTED_LANGS}",
    ),
) -> OCRResponse:
    # 언어 유효성 검사
    if lang not in settings.SUPPORTED_LANGS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"지원하지 않는 언어: '{lang}'. 지원 언어: {settings.SUPPORTED_LANGS}",
        )

    # Content-Type 유효성 검사
    content_type = file.content_type or ""
    if content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"지원하지 않는 파일 타입: '{content_type}'. 지원 타입: {settings.ALLOWED_CONTENT_TYPES}",
        )

    # 파일 크기 검사 (스트림으로 읽기)
    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"파일 크기 초과: {len(data) / 1024 / 1024:.1f}MB. 최대 허용: {settings.MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB",
        )

    if len(data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="빈 파일입니다.",
        )

    logger.info(
        f"OCR 요청: filename={file.filename}, content_type={content_type}, "
        f"size={len(data) / 1024:.1f}KB, lang={lang}"
    )

    try:
        if content_type == "application/pdf":
            pages, elapsed_ms = await ocr_service.process_pdf(data, lang=lang)
        else:
            pages, elapsed_ms = await ocr_service.process_image(data, lang=lang)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"OCR 처리 중 오류 발생: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OCR 처리 중 내부 오류가 발생했습니다.",
        )

    logger.info(f"OCR 완료: pages={len(pages)}, elapsed_ms={elapsed_ms:.0f}ms")

    return OCRResponse(
        pages=pages,
        total_pages=len(pages),
        elapsed_ms=round(elapsed_ms, 2),
        lang=lang,
        filename=file.filename,
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="헬스 체크",
    description="서버 상태 및 로드된 OCR 모델 언어 목록을 반환합니다.",
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        loaded_langs=ocr_service.loaded_langs,
        version=settings.APP_VERSION,
    )
