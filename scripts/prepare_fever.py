import sys
import json
import random
import time
import wikipedia
from pathlib import Path
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Thiết lập đường dẫn
BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Cấu hình Wikipedia tiếng Anh
wikipedia.set_lang("en")

def get_wikipedia_content(page_titles):
    """Lấy nội dung từ Wikipedia cho danh sách các tiêu đề trang."""
    unique_titles = list(set(page_titles))
    combined_content = []
    
    for title in unique_titles:
        if not title: continue
        clean_title = title.replace("-LRB-", "(").replace("-RRB-", ")").replace("_", " ")
        
        try:
            page = wikipedia.page(clean_title, auto_suggest=False)
            content = page.summary
            if content.strip():
                combined_content.append(f"--- Source: {clean_title} ---\n{content}")
            time.sleep(0.3)
        except Exception:
            pass
            
    return "\n\n".join(combined_content).strip()

def main(total_samples: int = 40):
    input_file = RAW_DIR / "FEVER.jsonl"
    if not input_file.exists():
        print(f"❌ Không tìm thấy file: {input_file}")
        return

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"1. Đang đọc dữ liệu từ {input_file.name} (Chỉ lấy SUPPORTS & REFUTES)...", flush=True)
    
    data_by_label = {
        "SUPPORTS": [],
        "REFUTES": []
    }

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            label = item.get("label")
            if label in data_by_label:
                if item.get("verifiable") == "VERIFIABLE":
                    data_by_label[label].append(item)

    # Mục tiêu cho mỗi nhãn (Chia đôi)
    target_per_label = total_samples // 2
    remainder = total_samples % 2
    
    label_map = {"SUPPORTS": 1.0, "REFUTES": 0.0}
    final_results = []

    print(f"2. Đang lọc và tra cứu Wikipedia (Chỉ lấy mẫu có nội dung)...", flush=True)
    
    for label in ["SUPPORTS", "REFUTES"]:
        count_needed = target_per_label + (1 if remainder > 0 else 0)
        if remainder > 0: remainder -= 1
        
        print(f"   --- Nhóm {label} (Cần {count_needed} mẫu) ---", flush=True)
        
        candidates = data_by_label[label]
        random.shuffle(candidates)
        
        count_found = 0
        idx = 0
        while count_found < count_needed and idx < len(candidates):
            item = candidates[idx]
            idx += 1
            
            page_titles = []
            if item.get("evidence"):
                for evidence_set in item["evidence"]:
                    for piece in evidence_set:
                        if len(piece) >= 3 and piece[2]:
                            page_titles.append(piece[2])
            
            evidence_text = get_wikipedia_content(page_titles)
            
            if evidence_text:
                final_results.append({
                    "id": f"fever-{item['id']}",
                    "claim": item["claim"],
                    "label": label_map[label],
                    "original_label": label,
                    "initial_context": evidence_text,
                    "type": "FEVER"
                })
                count_found += 1
                print(f"      [{count_found}/{count_needed}] OK: {item['claim'][:50]}...", flush=True)

    random.shuffle(final_results)

    out_file = PROCESSED_DIR / "fever_claims_binary.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)
        
    print(f"\n✅ Hoàn tất! Đã lưu {len(final_results)} mẫu (Binary) vào: {out_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Chuẩn bị dữ liệu FEVER Binary (SUPPORTS/REFUTES).")
    parser.add_argument("--n", type=int, default=40, help="Số lượng mẫu (mặc định: 40)")
    args = parser.parse_args()
    
    random.seed(42)
    main(args.n)
