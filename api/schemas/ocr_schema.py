"""
OCR API Pydantic 스키마
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class TextMetrics(BaseModel):
    """텍스트 통계"""

    char_count: int = Field(..., description="문자 수")
    word_count: int = Field(..., description="단어 수")
    line_count: int = Field(..., description="줄 수")


class PageResult(BaseModel):
    """페이지별 OCR 결과"""

    page: int = Field(..., description="페이지 번호 (1부터 시작)")
    texts: List[str] = Field(..., description="인식된 텍스트 목록")
    extracted_text: str = Field(..., description="줄바꿈으로 합친 전체 텍스트")
    metrics: TextMetrics = Field(..., description="텍스트 통계")


class OCRResponse(BaseModel):
    """OCR API 응답"""

    pages: List[PageResult] = Field(..., description="페이지별 결과")
    total_pages: int = Field(..., description="총 페이지 수")
    elapsed_ms: float = Field(..., description="처리 시간 (밀리초)")
    lang: str = Field(..., description="사용된 언어")
    filename: Optional[str] = Field(None, description="업로드된 파일명")


class HealthResponse(BaseModel):
    """헬스 체크 응답"""

    status: str = Field(..., description="서버 상태")
    loaded_langs: List[str] = Field(..., description="로드된 OCR 언어 목록")
    version: str = Field(..., description="API 버전")


class ErrorResponse(BaseModel):
    """에러 응답"""

    detail: str = Field(..., description="에러 메시지")
    code: Optional[str] = Field(None, description="에러 코드")
