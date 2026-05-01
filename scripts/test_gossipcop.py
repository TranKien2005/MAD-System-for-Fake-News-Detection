import os
import json
import random
import time
import argparse
import sys
import re
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Đảm bảo import được main.py
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from main import run_mad, create_llms
from utils.rate_limit import safe_invoke

# PROMPT NÂNG CẤP: GIỚI THIỆU CHI TIẾT NGỮ CẢNH
EVALUATION_PROMPT = """Bạn là một chuyên gia thẩm định tin tức (News Verifier) chuyên nghiệp. 
Đầu vào bạn nhận được là một TIÊU ĐỀ BÀO BÁO (News Headline) hoặc một NHẬN ĐỊNH (Claim) lấy từ các trang tin tức giải trí hoặc chính trị.

NHIỆM VỤ:
Bạn phải xác định xem tiêu đề/nhận định này là TIN THẬT (Real News) hay TIN GIẢ (Fake News/Rumor).

YÊU CẦU XUẤT RA (JSON):
Chỉ trả về JSON với định dạng sau:
{
  "truth_score": <CHỈ 1.0 hoặc 0.0>
}

QUY ƯỚC ĐIỂM SỐ:
- 1.0 (REAL): Nhận định phản ánh chính xác sự thật, đã được xác nhận bởi các nguồn tin uy tín.
- 0.0 (FAKE): Nhận định là tin đồn thất thiệt, thông tin bịa đặt hoặc đã bị các bên liên quan bác bỏ.

CẢNH BÁO TỐI CAO (CRITICAL RULE): 
- Hệ thống CHỈ CHẤP NHẬN giá trị nhị phân.
- TUYỆT ĐỐI KHÔNG trả về các giá trị xác suất (ví dụ: 0.99, 0.8, 0.5, 0.1). 
- Nếu bạn tin là đúng, hãy dứt khoát ghi 1.0. Nếu bạn tin là sai, hãy dứt khoát ghi 0.0."""

# Thiết lập đường dẫn
RESULTS_DIR = BASE_DIR / "data" / "results"
DEBATE_LOGS_DIR = RESULTS_DIR / "debate_logs"
DEBATE_LOGS_DIR.mkdir(parents=True, exist_ok=True)
load_dotenv(BASE_DIR / ".env")

def get_base_llm_score(llm, claim: str) -> float:
    """Hỏi trực tiếp model gốc."""
    prompt = f"""{EVALUATION_PROMPT}

Tiêu đề cần thẩm định: "{claim}"
"""
    try:
        res = safe_invoke(llm, [HumanMessage(content=prompt)])
        content = res.content
        if isinstance(content, list):
            score_str = "".join([c.get("text", "") for c in content if isinstance(c, dict)])
        else:
            score_str = str(content)
        
        # Tìm điểm 0.0 hoặc 1.0
        match = re.search(r"(0\.0|1\.0)", score_str)
        if match:
            return float(match.group(1))
            
        # Parse JSON dự phòng
        match_json = re.search(r'\{.*\}', score_str, re.DOTALL)
        if match_json:
            data = json.loads(match_json.group(0))
            raw_score = float(data.get("truth_score", 0.0))
            return 1.0 if raw_score >= 0.5 else 0.0
            
        return 0.0
    except Exception as e:
        print(f"  [Lỗi Base LLM]: {e}")
        return 0.5

def main():
    parser = argparse.ArgumentParser(description="Hệ thống đánh giá hiệu năng MAD (Fake News Detection).")
    parser.add_argument("--file", type=str, default="data/processed/gossipcop_claims.json", help="File dữ liệu processed JSON.")
    parser.add_argument("--n", type=int, default=20, help="Số lượng mẫu test (tổng).")
    args = parser.parse_args()

    input_file = BASE_DIR / args.file
    if not input_file.exists():
        print(f"❌ Không tìm thấy file dữ liệu: {input_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        all_claims = json.load(f)

    # Đảm bảo phân bổ 50/50
    true_list = [c for c in all_claims if c["label"] == 1.0]
    false_list = [c for c in all_claims if c["label"] == 0.0]
    
    n_half = args.n // 2
    sampled = random.sample(true_list, min(n_half, len(true_list))) + \
              random.sample(false_list, min(n_half, len(false_list)))
    random.shuffle(sampled)

    llm_main, _ = create_llms()
    summary_results = []
    
    print(f"\n================================================================================")
    print(f"🚀 KHỞI CHẠY ĐÁNH GIÁ HỆ THỐNG MAD (Fake News Detection)")
    print(f"📂 Dữ liệu: {input_file.name} | Số lượng: {len(sampled)} mẫu")
    print(f"================================================================================\n")

    mad_correct = 0
    base_correct = 0

    for i, item in enumerate(sampled, 1):
        claim = item["claim"]
        label = item["label"]
        item_id = item.get("id", f"sample-{i}")
        
        print(f"--- MẪU {i}/{len(sampled)} [{item_id}] ---")
        print(f"Claim: {claim}")
        print(f"Label: {'REAL' if label == 1.0 else 'FAKE'} ({label})")

        # 1. Base LLM
        print(f"--- [1/2] Đang hỏi Base LLM ({llm_main.model_name})...")
        base_score = get_base_llm_score(llm_main, claim)
        print(f"    => Base LLM Score: {base_score}")

        # 2. MAD System
        print(f"--- [2/2] Đang chạy MAD System...")
        start_t = time.time()
        final_state = run_mad(claim, custom_output_instructions=EVALUATION_PROMPT, silent=True)
        duration = time.time() - start_t
        
        raw_mad_score = float(final_state.get("verdict", {}).get("truth_score", 0.0))
        mad_score = 1.0 if raw_mad_score >= 0.5 else 0.0

        # Thống kê
        is_base_correct = (base_score == label)
        is_mad_correct = (mad_score == label)
        if is_base_correct: base_correct += 1
        if is_mad_correct: mad_correct += 1

        print(f"✅ Xong: Base={base_score} ({'Đúng' if is_base_correct else 'Sai'}) | MAD={mad_score} ({'Đúng' if is_mad_correct else 'Sai'}) | {duration:.1f}s\n")

        # LƯU CHI TIẾT TRANH LUẬN (AUDIT LOG)
        log_data = {
            "metadata": {
                "id": item_id,
                "label": label,
                "type": item.get("type", "GossipCop"),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "input": {
                "news_headline": claim
            },
            "base_llm_result": {
                "score": base_score,
                "is_correct": is_base_correct
            },
            "mad_system_result": {
                "score": mad_score,
                "is_correct": is_mad_correct,
                "duration_seconds": duration,
                "final_verdict": final_state.get("verdict", {})
            },
            "debate_history": final_state.get("debate_history", []),
            "knowledge_base": final_state.get("knowledge_base", [])
        }
        
        log_filename = DEBATE_LOGS_DIR / f"log_{item_id}_{int(time.time())}.json"
        with open(log_filename, "w", encoding="utf-8") as lf:
            json.dump(log_data, lf, indent=2, ensure_ascii=False)

        summary_results.append({
            "id": item_id,
            "claim": claim,
            "label": label,
            "base": base_score,
            "mad": mad_score
        })
        
        time.sleep(2)

    # TỔNG KẾT
    total = len(summary_results)
    if total > 0:
        print(f"\n" + "="*80)
        print(f"📊 BÁO CÁO HIỆU NĂNG TỔNG QUÁT")
        print("="*80)
        print(f"✅ Tổng mẫu đã test: {total}")
        print(f"🎯 Accuracy Base LLM:  {(base_correct/total)*100:.1f}%")
        print(f"🔥 Accuracy MAD System: {(mad_correct/total)*100:.1f}%")
        print(f"📈 Độ lệch cải thiện:  {((mad_correct - base_correct)/total)*100:+.1f}%")
        print("-" * 80)
        print(f"📂 Toàn bộ lịch sử tranh luận được lưu tại: {DEBATE_LOGS_DIR}")
        print("="*80 + "\n")

if __name__ == "__main__":
    main()
