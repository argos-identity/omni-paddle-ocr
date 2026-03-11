"""
PDF OCR 수동 테스트 스크립트
사용법: python tests/run_pdf_ocr.py tests/docs/A1_Ecoeye_Certificate_of_Business_Registration.pdf
"""

import sys
import time
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from paddleocr import PaddleOCR

from api.services.ocr_service import _compute_metrics, _pdf_to_images, _run_ocr_on_image


def run(pdf_path: str, lang: str = "korean") -> None:
    path = Path(pdf_path)
    if not path.exists():
        print(f"[ERROR] 파일 없음: {pdf_path}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"  파일  : {path.name}")
    print(f"  언어  : {lang}")
    print(f"{'=' * 60}\n")

    # 모델 로드
    print("[1/3] PaddleOCR 모델 로딩 중...")
    t0 = time.time()
    ocr = PaddleOCR(lang=lang)
    print(f"      완료 ({(time.time() - t0) * 1000:.0f}ms)\n")

    # PDF → 이미지
    print("[2/3] PDF → 이미지 변환 중...")
    t1 = time.time()
    data = path.read_bytes()
    images = _pdf_to_images(data)
    print(f"      페이지 수: {len(images)}  ({(time.time() - t1) * 1000:.0f}ms)\n")

    # OCR 실행
    print("[3/3] OCR 처리 중...\n")
    total_start = time.time()

    for idx, img in enumerate(images, start=1):
        t_page = time.time()
        texts = _run_ocr_on_image(ocr, img)
        elapsed = (time.time() - t_page) * 1000
        extracted = "\n".join(texts)
        metrics = _compute_metrics(extracted)

        print(
            f"┌─ 페이지 {idx} / {len(images)}  ({elapsed:.0f}ms) ─────────────────────"
        )
        print(
            f"│  문자 수: {metrics.char_count}  단어 수: {metrics.word_count}  줄 수: {metrics.line_count}"
        )
        print("│")
        for line in extracted.splitlines():
            print(f"│  {line}")
        print("└" + "─" * 55 + "\n")

    total_ms = (time.time() - total_start) * 1000
    print(f"{'=' * 60}")
    print(f"  총 처리 시간: {total_ms:.0f}ms")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    pdf = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "tests/docs/A1_Ecoeye_Certificate_of_Business_Registration.pdf"
    )
    lang = sys.argv[2] if len(sys.argv) > 2 else "korean"
    run(pdf, lang)
