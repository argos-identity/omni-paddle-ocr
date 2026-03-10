"""
PaddleOCR 한국어 문서 OCR 테스트
4개 테스트 문서에 대해 OCR을 수행하고 결과를 저장한다.
"""

import os
import sys
import time

# PaddleOCR 초기화 로그 최소화
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

from paddleocr import PaddleOCR
from ocr_common import TEST_DOCUMENTS, get_image_path, compute_metrics, save_ocr_result
from ground_truth import evaluate_accuracy

ENGINE_NAME = "paddleocr"


def run_paddleocr_test():
    print("=" * 60)
    print("PaddleOCR 한국어 문서 OCR 테스트")
    print("=" * 60)

    # PaddleOCR 초기화
    print("\n[1/2] PaddleOCR 모델 로딩 (lang=korean)...")
    ocr = PaddleOCR(lang="korean")
    print("  -> 모델 로딩 완료")

    # 테스트 실행
    print(f"\n[2/2] {len(TEST_DOCUMENTS)}개 문서 OCR 테스트 시작\n")
    results = []

    for i, doc in enumerate(TEST_DOCUMENTS, 1):
        print(f"--- [{i}/{len(TEST_DOCUMENTS)}] {doc['filename']} ({doc['doc_type']}, {doc['format']}) ---")

        image_path = get_image_path(doc)
        print(f"  이미지: {os.path.basename(image_path)}")

        # OCR 실행 및 시간 측정
        start_time = time.time()
        result = ocr.predict(image_path)
        elapsed_ms = (time.time() - start_time) * 1000

        # 텍스트 추출 (rec_texts 리스트를 줄바꿈으로 결합)
        all_texts = []
        for page_result in result:
            texts = page_result.get("rec_texts", [])
            all_texts.extend(texts)

        extracted_text = "\n".join(all_texts)

        # 메트릭 계산
        metrics = compute_metrics(extracted_text)
        print(f"  처리 시간: {elapsed_ms:.0f}ms")
        print(f"  텍스트: {metrics['char_count']} chars, {metrics['word_count']} words, {metrics['line_count']} lines")

        # 정확도 평가
        accuracy_result = evaluate_accuracy(doc["id"], extracted_text)
        print(f"  정확도: {accuracy_result['correct']}/{accuracy_result['total']} ({accuracy_result['accuracy']:.1f}%)")

        # 결과 저장
        save_ocr_result(ENGINE_NAME, doc, extracted_text, elapsed_ms, metrics, accuracy_result)

        results.append({
            "doc": doc,
            "text": extracted_text,
            "time_ms": elapsed_ms,
            "metrics": metrics,
            "accuracy": accuracy_result,
        })
        print()

    # 요약
    print("=" * 60)
    print("PaddleOCR 테스트 완료 요약")
    print("=" * 60)
    for r in results:
        doc = r["doc"]
        acc = r["accuracy"]
        print(f"  {doc['id']:25s} | {r['time_ms']:7.0f}ms | {r['metrics']['char_count']:4d} chars | {acc['correct']}/{acc['total']} ({acc['accuracy']:.1f}%)")


if __name__ == "__main__":
    run_paddleocr_test()
