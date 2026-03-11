# Python 3.10 slim 기반
FROM python:3.10-slim

# 시스템 의존성 (OpenCV headless, poppler for PDF)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 의존성 먼저 설치 (캐싱 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY api/ ./api/

# 포트 노출
EXPOSE 9125

# PaddleOCR 로그 최소화
ENV PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

# 실행
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "9125"]
