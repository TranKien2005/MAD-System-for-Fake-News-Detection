import os
import json
import pandas as pd
import trafilatura
from pathlib import Path
import time
import sys

# Đảm bảo in ra được tiếng Việt
sys.stdout.reconfigure(encoding='utf-8')

# Thiết lập đường dẫn
BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def scrape_article(url: str):
    """Sử dụng trafilatura để lấy nội dung và ngày tháng."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None
            
        # Trích xuất metadata và content
        result = trafilatura.extract(downloaded, output_format='json', include_comments=False, include_date=True)
        if result:
            data = json.loads(result)
            text = data.get('text')
            date = data.get('date')
            title = data.get('title')
            
            if text and len(text.split()) > 50: # Đảm bảo có nội dung đáng kể
                return {
                    "title": title,
                    "text": text,
                    "date": date
                }
    except Exception as e:
        pass
    return None

def main(samples_per_label: int = 10):
    real_path = RAW_DIR / "gossipcop_real.csv"
    fake_path = RAW_DIR / "gossipcop_fake.csv"
    
    if not real_path.exists() or not fake_path.exists():
        print("❌ Thiếu file CSV trong data/raw/")
        return

    out_file = PROCESSED_DIR / "gossipcop_full_content.json"
    results = []

    def process_subset(df, label, target_count):
        count = 0
        processed_data = []
        print(f"\n--- Đang quét nhãn: {label} (Mục tiêu: {target_count}) ---")
        
        # Xáo trộn để lấy mẫu đa dạng
        df_shuffled = df.sample(frac=1).reset_index(drop=True)
        
        for idx, row in df_shuffled.iterrows():
            if count >= target_count:
                break
                
            url = row['news_url']
            title_csv = row['title']
            
            print(f"  [{count+1}/{target_count}] Đang thử URL: {url[:60]}...")
            
            article = scrape_article(url)
            
            if article:
                # Đóng gói thành News Package
                date_str = article['date'] if article['date'] else "Unknown Date"
                # Format này giúp MAD System nhận diện rõ Title, Date và Content
                full_claim = f"[TIMESTAMP: {date_str}]\nTITLE: {article['title'] if article['title'] else title_csv}\nCONTENT: {article['text']}"
                
                processed_data.append({
                    "id": row['id'],
                    "claim": full_claim,
                    "original_title": title_csv,
                    "label": float(label),
                    "date": article['date'],
                    "type": "GossipCop-Full"
                })
                count += 1
                print(f"    ✅ Lấy thành công! (Date: {date_str})")
            else:
                pass
            
            # Nghỉ ngắn để tránh bị chặn
            time.sleep(0.5)
            
        return processed_data

    # Đọc dữ liệu
    df_real = pd.read_csv(real_path)
    df_fake = pd.read_csv(fake_path)

    results.extend(process_subset(df_real, 1.0, samples_per_label))
    results.extend(process_subset(df_fake, 0.0, samples_per_label))

    # Lưu kết quả
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"\n✅ Hoàn tất! Đã lưu {len(results)} mẫu đầy đủ thông tin vào: {out_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scrape đầy đủ nội dung GossipCop.")
    parser.add_argument("--n", type=int, default=10, help="Số lượng mẫu cho mỗi nhãn (mặc định: 10)")
    args = parser.parse_args()
    
    main(args.n)
