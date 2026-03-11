"""
애플리케이션 설정
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # 앱 정보
    APP_NAME: str = "PaddleOCR API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 서버
    HOST: str = "0.0.0.0"
    PORT: int = 9125

    # OCR 설정
    DEFAULT_LANG: str = "korean"
    SUPPORTED_LANGS: List[str] = ["korean", "en", "ch", "japan"]

    # 파일 업로드 제한 (bytes) — 기본 50MB
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024

    # 지원 MIME 타입
    ALLOWED_CONTENT_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/bmp",
        "image/tiff",
        "image/webp",
        "application/pdf",
    ]

    # ThreadPoolExecutor worker 수 (CPU bound OCR)
    OCR_WORKERS: int = 2

    # OCR 감지 모델 — mobile(저메모리/EC2 8GB 권장)
    # PP-OCRv5_mobile_det : ~886 MiB  (EC2 8GB 안정)
    # PP-OCRv5_server_det : ~17 GiB 피크 (EC2 비구널)
    OCR_DET_MODEL: str = "PP-OCRv5_mobile_det"

    # OCR 인식 모델 — 한국어 특화 mobile_rec
    OCR_REC_MODEL: str = "korean_PP-OCRv5_mobile_rec"

    # PDF 렌더링 DPI
    # PDF 렌더링 DPI — 높을수록 해상도↑ 한국어 인식률↑ (메모리/속도 트레이드오프)
    # 150: 빠름/저데이터 | 200: 기본값 | 300: 고해상도 한국어 최적화
    PDF_DPI: int = 300


settings = Settings()
