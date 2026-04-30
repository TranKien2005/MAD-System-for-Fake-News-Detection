import os
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import sys
import time

# Thiết lập đường dẫn
BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

load_dotenv(BASE_DIR / ".env")

def get_llm():
    """Khởi tạo Gemini Flash thông qua NineRouter."""
    api_key = os.getenv("NINEROUTER_API_KEY")
    base_url = os.getenv("NINEROUTER_BASE_URL")
    return ChatOpenAI(
        model="gemini-3-flash", # Theo yêu cầu của bạn
        temperature=0,
        api_key=api_key,
        base_url=base_url,
    )

def is_valid_claim(llm, title: str) -> bool:
    """Sử dụng LLM để xác định xem title có phù hợp làm dữ liệu benchmark hay không."""
    if not title or len(title.split()) < 4:
        return False
        
    prompt = f"""Bạn là bộ lọc dữ liệu cho hệ thống kiểm chứng tin tức. Xác định xem tiêu đề bài báo dưới đây có PHÙ HỢP làm dữ liệu kiểm chứng (benchmark) hay không.

=== TIÊU CHÍ LOẠI BỎ (Trả về 'NO') ===

1. KHÔNG PHẢI NHẬN ĐỊNH: Chỉ là tên riêng, tên phim, tên bài hát, tên sự kiện, hoặc cụm từ rời rạc không chứa khẳng định sự việc.
   Ví dụ loại bỏ: "Golden Globes 2018", "Quinn Perkins", "Bachelor in Paradise"

2. THỜI GIAN TƯƠNG ĐỐI: Chứa các mốc thời gian không cố định, sẽ bị sai lệch khi kiểm chứng ở thời điểm khác.
   Ví dụ loại bỏ: "this year", "next month", "coming April", "tuần tới", "năm nay"

3. TRẠNG THÁI THAY ĐỔI THEO THỜI GIAN: Khẳng định về trạng thái quan hệ, tình trạng sức khỏe, vị trí công việc, nơi ở... mà KHÔNG kèm mốc thời gian cụ thể (ngày/tháng/năm). Những thông tin này có thể đúng lúc viết bài nhưng sai ở hiện tại.
   Ví dụ loại bỏ: "Jack and Roxy are dating", "Tom is living in LA", "She is pregnant"
   Ví dụ CHẤP NHẬN (có mốc thời gian cụ thể): "Jack and Roxy got engaged in December 2018"

4. CÂU HỎI TU TỪ / CLICKBAIT KHÔNG KHẲNG ĐỊNH: Chỉ đặt câu hỏi mà không đưa ra khẳng định sự việc.
   Ví dụ loại bỏ: "Is she the next big star?", "What happened to their marriage?"

=== TIÊU CHÍ CHẤP NHẬN (Trả về 'YES') ===

1. Chứa một KHẲNG ĐỊNH SỰ VIỆC CỤ THỂ có thể kiểm chứng ĐÚNG hoặc SAI dựa trên bằng chứng.
2. Sự việc được khẳng định là KHÔNG PHỤ THUỘC THỜI ĐIỂM đọc — tức là nếu đúng thì luôn đúng, nếu sai thì luôn sai (hoặc có mốc thời gian cụ thể đi kèm).
   Ví dụ chấp nhận: "Chrissy Teigen offers to pay $100,000 fine for McKayla Maroney"
   Ví dụ chấp nhận: "Brad Pitt secretly apologized to Jennifer Aniston at the 2020 SAG Awards"

=== ĐÁNH GIÁ ===
Tiêu đề: "{title}"
Trả lời (CHỈ 'YES' hoặc 'NO'):"""
    
    try:
        res = llm.invoke([HumanMessage(content=prompt)])
        content = res.content
        if isinstance(content, list):
            answer = "".join([c.get("text", "") for c in content if isinstance(c, dict)])
        else:
            answer = str(content)
        return "YES" in answer.strip().upper()
    except Exception as e:
        print(f"  [Lỗi LLM]: {e}")
        return False

def main(samples_per_label: int = 50):
    real_path = RAW_DIR / "gossipcop_real.csv"
    fake_path = RAW_DIR / "gossipcop_fake.csv"
    
    if not real_path.exists() or not fake_path.exists():
        print("❌ Thiếu file CSV trong data/raw/")
        return

    print(f"1. Đang đọc dữ liệu từ CSV...")
    df_real = pd.read_csv(real_path)
    df_fake = pd.read_csv(fake_path)
    
    llm = get_llm()
    results = []

    def process_subset(df, label, target_count):
        count = 0
        processed_data = []
        print(f"   --- Đang xử lý nhóm nhãn: {label} ---")
        
        # Xáo trộn ngẫu nhiên để lấy mẫu đa dạng
        df_shuffled = df.sample(frac=1).reset_index(drop=True)
        
        for _, row in df_shuffled.iterrows():
            if count >= target_count:
                break
                
            title = str(row['title']).strip()
            if is_valid_claim(llm, title):
                processed_data.append({
                    "id": row['id'],
                    "claim": title,
                    "label": float(label),
                    "type": "GossipCop"
                })
                count += 1
                if count % 10 == 0:
                    print(f"      > Đã lọc được {count}/{target_count} mẫu...")
            
            # Tránh rate limit nếu cần
            # time.sleep(0.1)
            
        return processed_data

    # Xử lý cả hai nhóm để đảm bảo 50/50
    results.extend(process_subset(df_real, 1.0, samples_per_label))
    results.extend(process_subset(df_fake, 0.0, samples_per_label))

    # Lưu kết quả
    out_file = PROCESSED_DIR / "gossipcop_claims.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"\n✅ Hoàn tất! Đã lưu {len(results)} mẫu vào: {out_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Chuẩn bị dữ liệu GossipCop cho MAD System.")
    parser.add_argument("--n", type=int, default=20, help="Số lượng mẫu cho mỗi nhãn (mặc định: 20)")
    args = parser.parse_args()
    
    main(args.n)
