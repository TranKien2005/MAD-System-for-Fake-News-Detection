import os
import json
import random
import time
import argparse
import sys
import re
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Đảm bảo import được main.py
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from main import run_mad, get_llm
from utils.rate_limit import safe_invoke

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv(BASE_DIR / ".env")

# PROMPT NÂNG CẤP cho FEVER (Binary)
EVALUATION_PROMPT = """Bạn là một máy thẩm định tin tức tự động.
NHIỆM VỤ: Xác định nhận định là ĐÚNG (1.0) hay SAI (0.0).

QUY ĐỊNH NGHIÊM NGẶT:
- CHỈ trả về duy nhất một khối JSON.
- KHÔNG viết lời dẫn, KHÔNG giải thích ngoài khối JSON.
- KHÔNG dùng dấu gạch đầu dòng.

ĐỊNH DẠNG JSON BẮT BUỘC:
{
  "truth_score": <1.0 hoặc 0.0>,
  "reasoning": "Giải thích ngắn gọn 1-2 câu"
}
"""

# Thiết lập đường dẫn
RESULTS_DIR = BASE_DIR / "data" / "results"
DEBATE_LOGS_DIR = RESULTS_DIR / "fever_logs"
DEBATE_LOGS_DIR.mkdir(parents=True, exist_ok=True)

def get_base_llm_score(llm, claim: str) -> float:
    """Hỏi trực tiếp model gốc."""
    prompt = f"""{EVALUATION_PROMPT}

Nhận định cần thẩm định: "{claim}"
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
        # Nếu không tìm thấy bằng regex và JSON, tung lỗi
        raise ValueError(f"Base LLM không trả về điểm số hợp lệ (0.0/1.0). Nội dung: {score_str[:200]}...")
            
    except Exception as e:
        # Re-raise để script test chính bắt được và ghi nhận ERROR
        raise ValueError(f"Lỗi khi lấy điểm từ Base LLM: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Test hệ thống MAD trên tập dữ liệu FEVER (Non-Search).")
    parser.add_argument("--file", type=str, default="data/processed/fever_claims_binary.json", help="File dữ liệu FEVER binary.")
    parser.add_argument("--n", type=int, default=40, help="Số lượng mẫu test (mặc định: 10).")
    args = parser.parse_args()

    input_file = BASE_DIR / args.file
    if not input_file.exists():
        print(f"❌ Không tìm thấy file dữ liệu: {input_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        all_claims = json.load(f)

    # Lấy mẫu cân bằng
    supports = [c for c in all_claims if c["label"] == 1.0]
    refutes = [c for c in all_claims if c["label"] == 0.0]
    
    per_label = args.n // 2
    sampled = (random.sample(supports, min(per_label, len(supports))) + 
               random.sample(refutes, min(args.n - per_label, len(refutes))))
    random.shuffle(sampled)

    llm_main = get_llm()
    
    # Tạo thư mục log riêng cho từng model để dễ đối chiếu
    sanitized_model_name = llm_main.model_name.replace("/", "_").replace(":", "_")
    CURRENT_LOGS_DIR = DEBATE_LOGS_DIR / sanitized_model_name
    CURRENT_LOGS_DIR.mkdir(parents=True, exist_ok=True)

    summary_results = []
    
    print(f"\n================================================================================")
    print(f"🚀 KHỞI CHẠY TEST FEVER (Chế độ: NON-SEARCH)")
    print(f"🤖 Model: {llm_main.model_name}")
    print(f"📂 Dữ liệu: {input_file.name} | Số lượng: {len(sampled)} mẫu")
    print(f"================================================================================\n")

    mad_correct = 0
    base_correct = 0

    for i, item in enumerate(sampled, 1):
        claim = item["claim"]
        label = item["label"]
        context = item.get("initial_context", "")
        item_id = item.get("id", f"fever-sample-{i}")
        
        print(f"--- MẪU {i}/{len(sampled)} [{item_id}] ---")
        print(f"Claim: {claim}")
        print(f"Label gốc: {item['original_label']} ({label})")
        print(f"Context Length: {len(context)} chars")

        # 1. Base LLM
        print(f"--- [1/2] Đang hỏi Base LLM ({llm_main.model_name})...")
        base_score = get_base_llm_score(llm_main, claim)
        is_base_correct = (base_score == label)
        print(f"    => Base LLM Score: {base_score}")

        # 2. MAD System
        print(f"--- [2/2] Đang chạy MAD System...")
        start_mad = time.time()
        try:
            final_state = run_mad(
                news_text=claim,
                initial_context=context,
                debate_mode="non_search",
                silent=True
            )
            duration = time.time() - start_mad
            
            verdict = final_state.get("verdict", {})
            raw_score = verdict.get("truth_score", 0.5)
            pred_label = 1.0 if raw_score > 0.5 else 0.0
            is_mad_correct = (pred_label == label)
            
            if is_mad_correct:
                mad_correct += 1
            if is_base_correct:
                base_correct += 1

            print(f"⚖️ Kết quả: Base={base_score} ({'Đúng' if is_base_correct else 'Sai'}) | MAD={pred_label} ({'Đúng' if is_mad_correct else 'Sai'})")
            print(f"⏱️ Thời gian: {duration:.1f}s\n")

            # Lưu vào danh sách tổng hợp
            summary_results.append({
                "id": item_id,
                "claim": claim,
                "ground_truth": label,
                "base_score": base_score,
                "mad_label": pred_label,
                "is_mad_correct": is_mad_correct,
                "is_base_correct": is_base_correct,
                "duration": duration,
                "status": "SUCCESS"
            })

            # Lưu log chi tiết
            log_data = {
                "id": item_id,
                "claim": claim,
                "ground_truth": label,
                "base_llm": {
                    "score": base_score,
                    "is_correct": is_base_correct
                },
                "mad_system": {
                    "score": pred_label,
                    "raw_score": raw_score,
                    "is_correct": is_mad_correct,
                    "verdict": verdict
                },
                "context_used": context,
                "debate_history": final_state.get("debate_history", []),
                "duration": duration
            }
            
            log_filename = CURRENT_LOGS_DIR / f"test_{item_id}_{int(time.time())}.json"
            with open(log_filename, "w", encoding="utf-8") as lf:
                json.dump(log_data, lf, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"❌ LỖI tại mẫu {item_id}: {str(e)}")
            summary_results.append({
                "id": item_id,
                "claim": claim,
                "ground_truth": label,
                "base_score": base_score,
                "mad_label": None,
                "is_mad_correct": False,
                "is_base_correct": is_base_correct,
                "duration": time.time() - start_mad,
                "status": f"ERROR: {str(e)}"
            })
            continue

    # TỔNG KẾT
    total = len(sampled)
    if total > 0:
        # TÍNH TOÁN CHỈ SỐ CHI TIẾT (MAD)
        tp_mad = sum(1 for r in summary_results if r['ground_truth'] == 1.0 and r['mad_label'] == 1.0)
        tn_mad = sum(1 for r in summary_results if r['ground_truth'] == 0.0 and r['mad_label'] == 0.0)
        fp_mad = sum(1 for r in summary_results if r['ground_truth'] == 0.0 and r['mad_label'] == 1.0)
        fn_mad = sum(1 for r in summary_results if r['ground_truth'] == 1.0 and r['mad_label'] == 0.0)
        
        precision_mad = tp_mad / (tp_mad + fp_mad) if (tp_mad + fp_mad) > 0 else 0
        recall_mad = tp_mad / (tp_mad + fn_mad) if (tp_mad + fn_mad) > 0 else 0
        f1_mad = 2 * (precision_mad * recall_mad) / (precision_mad + recall_mad) if (precision_mad + recall_mad) > 0 else 0
        
        # TÍNH TOÁN CHỈ SỐ CHI TIẾT (BASE)
        tp_base = sum(1 for r in summary_results if r['ground_truth'] == 1.0 and r['base_score'] == 1.0)
        fp_base = sum(1 for r in summary_results if r['ground_truth'] == 0.0 and r['base_score'] == 1.0)
        fn_base = sum(1 for r in summary_results if r['ground_truth'] == 1.0 and r['base_score'] == 0.0)
        
        precision_base = tp_base / (tp_base + fp_base) if (tp_base + fp_base) > 0 else 0
        recall_base = tp_base / (tp_base + fn_base) if (tp_base + fn_base) > 0 else 0
        f1_base = 2 * (precision_base * recall_base) / (precision_base + recall_base) if (precision_base + recall_base) > 0 else 0

        avg_speed = sum(r['duration'] for r in summary_results) / total
        mad_acc = (mad_correct / total) * 100
        base_acc = (base_correct / total) * 100

        # XUẤT FILE BÁO CÁO PHÂN TÍCH CHI TIẾT
        timestamp = int(time.time())
        report_filename = CURRENT_LOGS_DIR / f"__ANALYSIS_REPORT_{timestamp}.txt"
        
        with open(report_filename, "w", encoding="utf-8") as rf:
            rf.write("================================================================================\n")
            rf.write("🧪 BÁO CÁO PHÂN TÍCH HIỆU NĂNG MÔ HÌNH (MAD VS BASE)\n")
            rf.write("================================================================================\n\n")
            rf.write(f"⏰ Thời gian chạy: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            rf.write(f"🤖 Model: {llm_main.model_name}\n")
            rf.write(f"📊 Tổng số mẫu: {total}\n")
            rf.write(f"⚡ Tốc độ trung bình: {avg_speed:.2f} giây/mẫu\n\n")

            rf.write("--- CHỈ SỐ CHI TIẾT ---\n")
            rf.write(f"{'Metric':<15} | {'Base LLM':<15} | {'MAD System':<15} | {'Improvement':<15}\n")
            rf.write("-" * 65 + "\n")
            rf.write(f"{'Accuracy':<15} | {base_acc:>14.2f}% | {mad_acc:>14.2f}% | {mad_acc-base_acc:>14.2f}%\n")
            rf.write(f"{'Precision':<15} | {precision_base:>14.2f}  | {precision_mad:>14.2f}  | {precision_mad-precision_base:>14.2f}\n")
            rf.write(f"{'Recall':<15} | {recall_base:>14.2f}  | {recall_mad:>14.2f}  | {recall_mad-recall_base:>14.2f}\n")
            rf.write(f"{'F1-Score':<15} | {f1_base:>14.2f}  | {f1_mad:>14.2f}  | {f1_mad-f1_base:>14.2f}\n\n")

            rf.write("--- PHÂN TÍCH THẤT BẠI (MAD FAILED CASES) ---\n")
            rf.write("Dưới đây là các câu mà MAD System đã phán quyết SAI so với nhãn gốc:\n\n")
            
            failures = [r for r in summary_results if not r['is_mad_correct']]
            if not failures:
                rf.write("🎉 Tuyệt vời! MAD System không đoán sai câu nào trong lượt test này.\n")
            else:
                for idx, f in enumerate(failures, 1):
                    type_str = "FALSE POSITIVE (Lẽ ra là SAI)" if f['ground_truth'] == 0.0 else "FALSE NEGATIVE (Lẽ ra là ĐÚNG)"
                    rf.write(f"{idx}. [ID: {f['id']}] - {type_str}\n")
                    rf.write(f"   📝 Claim: {f['claim']}\n")
                    # Lấy reasoning từ file log tương ứng (vì summary_results không lưu reasoning)
                    # Chúng ta sẽ in ra label cho nhanh, bạn có thể xem log chi tiết để thấy lý do
                    rf.write(f"   ⚖️ Kết quả: Base={f['base_score']} | MAD={f['mad_label']} | GroundTruth={f['ground_truth']}\n")
                    rf.write("-" * 40 + "\n")

            rf.write("\n" + "="*80 + "\n")
            rf.write(f"Log chi tiết từng mẫu được lưu tại: {CURRENT_LOGS_DIR}\n")

        # In ra console các chỉ số chính
        print(f"\n" + "="*80)
        print(f"📊 KẾT QUẢ ĐÃ SẴN SÀNG")
        print(f"🎯 Accuracy MAD: {mad_acc:.2f}% (F1: {f1_mad:.3f})")
        print(f"⚡ Tốc độ: {avg_speed:.2f}s/item")
        print(f"📂 Báo cáo phân tích chi tiết: {report_filename}")
        print("="*80 + "\n")

if __name__ == "__main__":
    main()
