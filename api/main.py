"""
PaddleOCR FastAPI 애플리케이션 진입점
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import settings
from api.routers.ocr import router as ocr_router
from api.services.ocr_service import ocr_service

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리: 시작 시 기본 모델 사전 로드, 종료 시 executor 정리"""
    logger.info(f"서버 시작: {settings.APP_NAME} v{settings.APP_VERSION}")
    preload_langs = [
        lang.strip() for lang in settings.PRELOAD_LANGS.split(",") if lang.strip()
    ]
    logger.info(f"언어 모델 사전 로딩: {preload_langs}")
    failed_langs = []
    for lang in preload_langs:
        try:
            await ocr_service.preload(lang)
        except Exception as exc:
            logger.error(
                f"모델 로딩 실패 (lang={lang}): {exc} — 요청 시점에 재시도합니다."
            )
            failed_langs.append(lang)
    if failed_langs:
        logger.warning(f"사전 로딩 실패 언어: {failed_langs}. 서버는 계속 기동됩니다.")
    else:
        logger.info("모든 모델 로딩 완료. 서버 준비됨.")
    yield
    logger.info("서버 종료 중...")
    ocr_service.shutdown()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "PaddleOCR 기반 한국어/다국어 OCR API. "
        "이미지(JPEG, PNG, BMP, TIFF, WebP) 및 PDF를 지원합니다."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(ocr_router)
