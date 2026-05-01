import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import json
import random
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
# Không dùng datasets/pyarrow nữa, tải trực tiếp CSV
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import sys
from utils.rate_limit import safe_invoke
sys.stdout.reconfigure(encoding='utf-8')

# Thiết lập đường dẫn thư mục
BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Đảm bảo các thư mục tồn tại
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Nạp biến môi trường để dùng LLM API
load_dotenv(BASE_DIR / ".env")

def get_llm():
    """Khởi tạo mô hình LLM thông qua NineRouter (dùng model nhỏ/nhanh)."""
    api_key = os.getenv("NINEROUTER_API_KEY")
    base_url = os.getenv("NINEROUTER_BASE_URL")
    
    # Bạn có thể đổi sang gpt-4o-mini hoặc gemini-1.5-flash tùy cấu hình
    return ChatOpenAI(
        model="gemini-3-flash",
        temperature=0.1,
        api_key=api_key,
        base_url=base_url,
    )

def transform_to_claim(llm, question: str, answer: str) -> str:
    """Sử dụng LLM để ghép câu hỏi và câu trả lời thành 1 câu khẳng định."""
    prompt = f"""Bạn là một trợ lý ngôn ngữ AI. 
Nhiệm vụ: Gộp CÂU HỎI và CÂU TRẢ LỜI tiếng Anh dưới đây thành MỘT CÂU KHẲNG ĐỊNH (declarative statement) hoàn chỉnh, tự nhiên bằng tiếng Anh.
YÊU CẦU QUAN TRỌNG: 
- KHÔNG giải thích.
- KHÔNG thêm thông tin bên ngoài.
- CHỈ trả về đúng 1 câu khẳng định ngắn gọn.

Câu hỏi: {question}
Câu trả lời: {answer}

Câu khẳng định:"""
    try:
        res = safe_invoke(llm, [HumanMessage(content=prompt)])
        return res.content.strip().strip('"')
    except Exception as e:
        print(f"  [Lỗi LLM]: {e}")
        # Fallback tạo câu thủ công nếu LLM lỗi
        return f"Regarding '{question}', the answer is: {answer}"

def main(num_samples: int = 10):
    print("1. Đang tải TruthfulQA dataset thông qua thư viện datasets...")
    raw_file_path = RAW_DIR / "truthfulqa.csv"
    
    try:
        if raw_file_path.exists():
            print(f"  Đã tìm thấy bản cache tại {raw_file_path}")
            df = pd.read_csv(raw_file_path)
        else:
            # Tải trực tiếp CSV từ HuggingFace (không cần thư viện datasets)
            csv_url = "https://hf-mirror.com/datasets/domenicrosati/TruthfulQA/resolve/main/TruthfulQA.csv"
            print(f"  Đang tải từ {csv_url}...")
            df = pd.read_csv(csv_url)
            df.to_csv(raw_file_path, index=False)
            print(f"  Đã lưu backup tại {raw_file_path}")
    except Exception as e:
        print(f"❌ Lỗi tải dữ liệu: {e}")
        return

    print("2. Đang lọc và lấy mẫu (Sampling)...")
    # Lọc chỉ lấy Type == 'Adversarial' theo yêu cầu
    df_adv = df[df['Type'] == 'Adversarial'].copy()
    
    # Lấy danh sách các Category để phân bổ đều
    categories = df_adv['Category'].unique()
    sampled_indices = []
    
    cat_idx = 0
    # Vòng lặp lấy mẫu đều đặn từ các category khác nhau
    while len(sampled_indices) < num_samples and len(sampled_indices) < len(df_adv):
        cat = categories[cat_idx % len(categories)]
        # Tìm các câu hỏi thuộc category này mà chưa được bốc
        cat_rows = df_adv[(df_adv['Category'] == cat) & (~df_adv.index.isin(sampled_indices))]
        
        if not cat_rows.empty:
            # Chọn ngẫu nhiên 1 câu từ category này
            sampled_indices.append(random.choice(cat_rows.index.tolist()))
            
        cat_idx += 1
        # Đề phòng lặp vô hạn nếu số câu hỏi < num_samples
        if cat_idx > len(categories) * 5: 
            break

    sampled_df = df_adv.loc[sampled_indices]
    
    print(f"3. Khởi tạo LLM và sinh Claims (1 Đúng - 2 Sai) cho {len(sampled_df)} mẫu...")
    llm = get_llm()
    results = []

    for idx, row in sampled_df.iterrows():
        question = row['Question']
        category = row['Category']
        
        print(f"\n- Đang xử lý: {question} (Cat: {category})")
        
        # Parse danh sách các câu trả lời (chia tách bởi dấu chấm phẩy)
        # TruthfulQA có cột Best Answer và Correct Answers. Ta gộp lại để lấy câu đúng
        correct_list = str(row.get('Best Answer', '')).split(';') + str(row.get('Correct Answers', '')).split(';')
        incorrect_list = str(row.get('Incorrect Answers', '')).split(';')
        
        # Làm sạch chuỗi trắng
        correct_list = [a.strip() for a in correct_list if a.strip()]
        incorrect_list = [a.strip() for a in incorrect_list if a.strip()]
        
        if not correct_list or not incorrect_list:
            print("  -> Bỏ qua vì thiếu dữ liệu trả lời.")
            continue
            
        # Sử dụng set để đảm bảo không sinh ra các nhận định trùng lặp về ngữ nghĩa
        generated_claims = set()
        
        # 1. Tạo Claim ĐÚNG (Ưu tiên dùng Best Answer)
        best_ans = str(row.get('Best Answer', '')).strip()
        if not best_ans:
            best_ans = random.choice(correct_list) # Fallback nếu Best Answer trống
            
        claim_true = transform_to_claim(llm, question, best_ans)
        
        results.append({
            "original_question": question,
            "category": category,
            "claim": claim_true,
            "label": 1.0,  # Tin Thật
            "type": "TruthfulQA-Adversarial"
        })
        generated_claims.add(claim_true.lower().strip())
        print(f"  [+] TRUE (Best): {claim_true}")
        
        # 2. Tạo tối đa 2 Claim SAI
        # Sắp xếp các câu trả lời sai theo độ dài giảm dần (heuristic cho việc chọn câu 'khó' và chi tiết)
        incorrect_list.sort(key=len, reverse=True)
        
        fail_count = 0
        for i_ans in incorrect_list:
            if len([r for r in results if r["original_question"] == question and r["label"] == 0.0]) >= 2:
                break # Đã đủ 2 câu sai
                
            claim_false = transform_to_claim(llm, question, i_ans)
            claim_key = claim_false.lower().strip()
            
            if claim_key not in generated_claims:
                results.append({
                    "original_question": question,
                    "category": category,
                    "claim": claim_false,
                    "label": 0.0,  # Tin Giả
                    "type": "TruthfulQA-Adversarial"
                })
                generated_claims.add(claim_key)
                print(f"  [-] FALSE: {claim_false}")
            else:
                print(f"  [!] Bỏ qua nhận định trùng: {claim_false}")
                fail_count += 1
                if fail_count > 5: # Tránh lặp quá nhiều nếu tập data quá hẹp
                    break

    # Ghi dữ liệu ra file processed
    out_file = PROCESSED_DIR / "truthfulqa_claims.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"\n4. Hoàn tất! Đã lưu {len(results)} câu khẳng định (Claims) vào: {out_file}")
    print("Bạn có thể viết script để load file này đưa vào MAD System.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tạo tập dữ liệu Claims từ TruthfulQA.")
    parser.add_argument("--samples", type=int, default=10, help="Số lượng câu hỏi gốc muốn lấy mẫu (mặc định: 10)")
    args = parser.parse_args()
    
    # Đặt seed để dễ debug nếu muốn (tùy chọn)
    random.seed(42)
    main(args.samples)
