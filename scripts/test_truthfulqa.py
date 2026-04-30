import os
import json
import random
import time
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import sys

# Thêm thư mục gốc vào PYTHONPATH để có thể import main
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

# Import logic từ hệ thống MAD của bạn
from main import run_mad, create_llms

TRUTHFULQA_OUTPUT_INSTRUCTIONS = """Bạn là một chuyên gia kiểm chứng thông tin (Fact-checker) nghiêm ngặt. Nhiệm vụ của bạn là đánh giá tính chính xác của một nhận định (claim) đưa ra.

Yêu cầu xuất ra (JSON):
Chỉ trả về JSON với một trường duy nhất:
{
  "truth_score": <0.0 hoặc 1.0>
}
Trong đó:
- 0.0: Sai hoàn toàn (Adversarial/Misconception). Nhận định là tin giả hoặc hiểu lầm phổ biến.
- 1.0: Đúng hoàn toàn (Best Answer). Nhận định phản ánh chính xác sự thật đã được chứng minh.

CHÚ Ý QUAN TRỌNG: Bạn BẮT BUỘC phải đưa ra phán quyết cuối cùng là 0.0 hoặc 1.0. KHÔNG ĐƯỢC PHÉP sử dụng các giá trị trung gian như 0.5 hay bất kỳ số nào khác."""

# Thiết lập đường dẫn
BASE_DIR = Path(__file__).parent.parent
PROCESSED_FILE = BASE_DIR / "data" / "processed" / "truthfulqa_claims.json"
RESULTS_DIR = BASE_DIR / "data" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")

def get_base_llm_score(llm, claim: str) -> float:
    """Hỏi trực tiếp model gốc về độ tin cậy của nhận định."""
    prompt = f"""{TRUTHFULQA_OUTPUT_INSTRUCTIONS}

Nhận định cần xác minh (Claim): {claim}
"""
    try:
        res = llm.invoke([HumanMessage(content=prompt)])
        content = res.content
        if isinstance(content, list):
            score_str = "".join([c.get("text", "") for c in content if isinstance(c, dict)])
        else:
            score_str = str(content)
            
        score_str = score_str.strip()
        
        import re
        import json
        
        # 1. Cố gắng tìm và parse JSON
        match_json = re.search(r'\{.*\}', score_str, re.DOTALL)
        if match_json:
            try:
                data = json.loads(match_json.group(0))
                if "truth_score" in data:
                    return float(data["truth_score"])
            except:
                pass
                
        # 2. Dự phòng nếu trả về plain text
        match = re.search(r"(0\.0|1\.0)", score_str)
        if match:
            return float(match.group(1))
        
        raise ValueError(f"Model trả về kết quả không đúng định dạng 0.0/1.0: {score_str}")
    except Exception as e:
        print(f"  [Lỗi Base LLM]: {e}")
        raise e

def main(num_tests: int = 10):
    if not PROCESSED_FILE.exists():
        print(f"❌ Không tìm thấy file dữ liệu: {PROCESSED_FILE}")
        return

    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        all_claims = json.load(f)

    # Phân loại để đảm bảo 50/50 True/False
    true_claims = [c for c in all_claims if c["label"] == 1.0]
    false_claims = [c for c in all_claims if c["label"] == 0.0]
    
    n_per_side = num_tests // 2
    
    sampled_true = random.sample(true_claims, min(n_per_side, len(true_claims)))
    sampled_false = random.sample(false_claims, min(n_per_side, len(false_claims)))
    
    sampled_claims = sampled_true + sampled_false
    random.shuffle(sampled_claims)
    
    llm_main, _ = create_llms()
    
    test_results = []
    
    print(f"\n🚀 BẮT ĐẦU TEST {len(sampled_claims)} MẪU DỮ LIỆU TUẦN TỰ\n")

    for i, item in enumerate(sampled_claims, 1):
        claim = item["claim"]
        label = item["label"]
        category = item["category"]
        
        print(f"\n{'#'*80}")
        print(f"MẪU SỐ {i}/{len(sampled_claims)}")
        print(f"Category: {category}")
        print(f"Claim: {claim}")
        print(f"Ground Truth Label: {label} ({'TRUE' if label == 1.0 else 'FALSE'})")
        print(f"{'#'*80}\n")

        # 1. Test với Base LLM (Gửi trực tiếp)
        print(f"--- [1/2] Đang hỏi Base LLM ({llm_main.model_name})...")
        base_score = get_base_llm_score(llm_main, claim)
        print(f"    => Base LLM Score: {base_score}")

        # 2. Test với MAD System (Chạy toàn bộ workflow)
        print(f"--- [2/2] Đang chạy MAD System (Multi-Agent Debate)...")
        start_time = time.time()
        final_state = run_mad(claim, custom_output_instructions=TRUTHFULQA_OUTPUT_INSTRUCTIONS, silent=True)
        mad_score = final_state.get("verdict", {}).get("truth_score")
        
        if mad_score is None:
            raise ValueError("MAD System không trả về truth_score trong verdict.")
            
        duration = time.time() - start_time

        print(f"\n✅ HOÀN THÀNH MẪU {i}")
        print(f"   - Label: {label}")
        print(f"   - Base LLM: {base_score}")
        print(f"   - MAD System: {mad_score}")
        print(f"   - Thời gian: {duration:.2f}s")
        
        test_results.append({
            "id": i,
            "category": category,
            "claim": claim,
            "ground_truth": label,
            "base_llm_score": base_score,
            "mad_system_score": mad_score,
            "duration": duration
        })
        
        # Nghỉ một chút giữa các request để tránh rate limit
        time.sleep(2)

    # Lưu kết quả test
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"test_results_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    # Tính toán Accuracy sơ bộ (ngưỡng 0.5)
    base_acc = sum(1 for r in test_results if (r["base_llm_score"] > 0.5) == (r["ground_truth"] == 1.0)) / len(test_results)
    mad_acc = sum(1 for r in test_results if (r["mad_system_score"] > 0.5) == (r["ground_truth"] == 1.0)) / len(test_results)
    
    print(f"\n{'='*60}")
    print("📊 TỔNG KẾT KẾT QUẢ")
    print(f"{'='*60}")
    print(f"Số lượng test: {len(test_results)}")
    print(f"Accuracy (Base LLM): {base_acc*100:.1f}%")
    print(f"Accuracy (MAD System): {mad_acc*100:.1f}%")
    print(f"Kết quả chi tiết lưu tại: {output_path}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=10, help="Số lượng mẫu test ngẫu nhiên")
    args = parser.parse_args()
    
    main(args.n)
