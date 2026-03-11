# omni-paddle-ocr

PaddleOCR 기반 FastAPI OCR API 서버.  
한국어 문서(PDF/이미지) OCR에 최적화되어 있으며, Docker로 배포합니다.

---

## 확정 구성 (Confirmed Configuration)

| 항목 | 값 | 비고 |
|------|-----|------|
| OCR Detection 모델 | `PP-OCRv5_mobile_det` | EC2 8GB 안정 (~2.5 GiB 피크) |
| OCR Recognition 모델 | `korean_PP-OCRv5_mobile_rec` / `en_PP-OCRv5_mobile_rec` | 언어별 자동 선택 |
| PDF 렌더링 DPI | `300` | 한국어 인식률 최적화 (DPI 200 대비 대폭 향상) |
| 포트 | `9125` | |
| 권장 서버 메모리 | **8GB 이상** | korean+en 동시 로딩 시 대기 ~1.6 GiB |

> **메모리 실측 결과**  
> `server_det` 계열은 처리 중 최대 **17 GiB** 까지 치솟아 EC2 8/16GB 모두 OOM.  
> `mobile_det + DPI 300` 조합이 정확도·메모리 균형점.

---

## API 명세 (Swagger)

서버 기동 후 아래 주소에서 확인:

```
http://<Server-IPAddress>:9125/docs
```

예시: `http://192.168.0.10:9125/docs`

---

## 엔드포인트 요약

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/api/v1/health` | 헬스체크, 로딩된 언어 확인 |
| `POST` | `/api/v1/ocr` | PDF/이미지 OCR 처리 |

---

### GET `/api/v1/health`

**응답 예시**

```json
{
  "status": "ok",
  "loaded_langs": ["korean"],
  "version": "1.0.0"
}
```

---

### POST `/api/v1/ocr`

**요청**

```bash
curl -X POST http://<Server-IPAddress>:9125/api/v1/ocr \
  -F "file=@document.pdf" \
  -F "lang=korean"
```

지원 언어: `korean`, `en`, `ch`, `japan`

**응답 예시**

```json
{
  "pages": [
    {
      "page": 1,
      "texts": [
        "국세청",
        "사업자등록증명",
        "주식회사에코아이",
        "...(인식된 텍스트 배열)"
      ],
      "extracted_text": "국세청\n사업자등록증명\n주식회사에코아이\n...",
      "metrics": {
        "char_count": 1677,
        "word_count": 348,
        "line_count": 106
      }
    }
  ],
  "total_pages": 1,
  "elapsed_ms": 21785.75,
  "lang": "korean",
  "filename": "document.pdf"
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `pages` | `array` | 페이지별 OCR 결과 목록 |
| `pages[].page` | `integer` | 페이지 번호 (1부터 시작) |
| `pages[].texts` | `string[]` | 인식된 텍스트 라인 배열 |
| `pages[].extracted_text` | `string` | 전체 텍스트 (줄바꿈 구분) |
| `pages[].metrics.char_count` | `integer` | 총 문자 수 |
| `pages[].metrics.word_count` | `integer` | 총 단어 수 |
| `pages[].metrics.line_count` | `integer` | 총 라인 수 |
| `total_pages` | `integer` | 처리된 전체 페이지 수 |
| `elapsed_ms` | `number` | OCR 처리 시간 (ms) |
| `lang` | `string` | 사용된 OCR 언어 |
| `filename` | `string \| null` | 업로드된 파일명 (없으면 `null`) |
---

## Docker 빌드 및 실행

### 1. 이미지 빌드

```bash
docker build -t omni-paddle-ocr .
```

### 2. 단독 컨테이너 실행

```bash
docker run -d \
  --name omni-paddle-ocr \
  -p 9125:9125 \
  -v paddleocr-models:/root/.paddlex \
  -e DEFAULT_LANG=korean \
  -e OCR_WORKERS=2 \
  omni-paddle-ocr
```

> 최초 기동 시 모델 자동 다운로드 (~90초 소요).  
> 볼륨(`paddleocr-models`)에 캐시되므로 재기동 시 즉시 시작.

### 3. 기동 확인

```bash
# 헬스체크
curl http://localhost:9125/api/v1/health

# 로그 확인
docker logs -f omni-paddle-ocr
```

---

## docker-compose.yml

```yaml
services:
  omni-paddle-ocr:
    build: .
    container_name: omni-paddle-ocr
    ports:
      - "9125:9125"
    environment:
      - DEFAULT_LANG=korean
      - OCR_WORKERS=2
      - DEBUG=false
      - FLAGS_use_mkldnn=0  # oneDNN 비활성화 (ConvertPirAttribute2RuntimeAttribute 에러 방지)
    volumes:
      # PaddleOCR 모델 캐시 유지 (재시작 시 재다운로드 방지)
      - paddleocr-models:/root/.paddlex
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9125/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s  # 모델 로딩 시간 고려

volumes:
  paddleocr-models:
```

### docker-compose 실행

```bash
# 빌드 + 기동
docker compose up -d --build

# 로그 확인
docker compose logs -f

# 중지
docker compose down
```

---

## 빌드 후 테스트 방법

### 방법 1 — curl (호스트에서)

```bash
# 헬스체크
curl http://localhost:9125/api/v1/health

# PDF OCR 테스트
curl -X POST http://localhost:9125/api/v1/ocr \
  -F "file=@/path/to/document.pdf" \
  -F "lang=korean"
```

### 방법 2 — Python httpx (컨테이너 내부에서)

```bash
# PDF 파일을 컨테이너에 복사
docker cp /path/to/document.pdf omni-paddle-ocr:/tmp/test.pdf

# 컨테이너 내부에서 테스트
docker exec omni-paddle-ocr python -c "
import httpx

with open('/tmp/test.pdf', 'rb') as f:
    resp = httpx.post(
        'http://localhost:9125/api/v1/ocr',
        files={'file': ('test.pdf', f, 'application/pdf')},
        data={'lang': 'korean'},
        timeout=120
    )

data = resp.json()
print(f'페이지 수: {len(data[\"pages\"])}')
print(f'처리 시간: {data[\"elapsed_ms\"]:.0f}ms')
print(data['pages'][0]['extracted_text'])
"
```

### 방법 3 — Swagger UI

브라우저에서 `http://localhost:9125/docs` 접속 후 직접 파일 업로드 테스트.

---

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DEFAULT_LANG` | `korean` | 기본 OCR 언어 (lang 파라미터 미지정 시 사용) |
| `PRELOAD_LANGS` | `korean,en` | 서버 시작 시 사전 로딩할 언어 목록 (쉼표 구분) |
| `OCR_WORKERS` | `2` | ThreadPoolExecutor 워커 수 |
| `DEBUG` | `false` | 디버그 모드 |
| `PDF_DPI` | `300` | PDF 렌더링 해상도 (높을수록 정확도↑, 속도↓) |
| `MAX_UPLOAD_SIZE` | `52428800` | 최대 업로드 크기 (기본 50MB) |
| `FLAGS_use_mkldnn` | `0` | oneDNN 비활성화 (CPU 환경 필수) |

### PRELOAD_LANGS 설정 방법

**docker-compose.yml**
```yaml
environment:
  - PRELOAD_LANGS=korean,en
```

**docker run**
```bash
docker run -e PRELOAD_LANGS=korean,en omni-paddle-ocr
```

**로컬 개발 (환경변수 직접 설정)**
```bash
export PRELOAD_LANGS=korean,en
uvicorn api.main:app --host 0.0.0.0 --port 9125 --reload
```

> **메모리 참고**  
> `korean,en` 동시 로딩 시 대기 메모리 ~1.6 GiB (언어당 ~800 MiB).  
> 한국어만 필요하면 `PRELOAD_LANGS=korean`으로 절약 가능.

---

## 로컬 개발 환경 (Conda)

```bash
# conda 환경 생성 (Python 3.10)
conda create -n omni-paddle-ocr python=3.10 -y
conda activate omni-paddle-ocr

# 의존성 설치
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov

# 개발 서버 실행
uvicorn api.main:app --host 0.0.0.0 --port 9125 --reload

# 테스트 실행
pytest tests/ -v
```

---

## 성능 지표 (EC2 기준 실측)

| 지표 | 값 |
|------|-----|
| 모델 최초 로딩 | ~20초 (캐시 후) |
| PDF 1페이지 OCR | ~21초 |
| 대기 중 메모리 | ~800 MiB |
| OCR 처리 중 피크 | ~2.5 GiB |
| 권장 인스턴스 | t3.large (8GB) 이상 |
