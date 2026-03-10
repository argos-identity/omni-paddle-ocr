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
    PORT: int = 8000

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

    # PDF 렌더링 DPI
    PDF_DPI: int = 200


settings = Settings()
