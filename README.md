# MAD System for Fake News Detection

MAD System for Fake News Detection là hệ thống kiểm chứng tin giả dựa trên mô hình Multi-Agent Debate. Thay vì hỏi một LLM duy nhất rồi nhận một câu trả lời trực tiếp, hệ thống tổ chức quá trình kiểm chứng thành nhiều bước: truy xuất bằng chứng, đánh giá độ tin cậy nguồn, tranh luận giữa hai tác tử đối kháng và tổng hợp phán quyết cuối cùng.

Dự án được xây dựng bằng Python, LangGraph và LangChain ChatOpenAI với API tương thích OpenAI/NineRouter. Hệ thống hỗ trợ hai chế độ vận hành: chế độ có tìm kiếm bằng chứng bên ngoài và chế độ không tìm kiếm dùng ngữ cảnh đầu vào, phù hợp cho đánh giá trên các bộ dữ liệu như FEVER.

## Mục tiêu chính

- Kiểm chứng một bản tin, tiêu đề hoặc claim văn bản bằng quy trình nhiều bước có khả năng truy vết.
- Kết hợp bằng chứng bên ngoài với lập luận phản biện đa tác tử.
- Lưu lại lịch sử tranh luận, nguồn bằng chứng, điểm tin cậy nguồn và phán quyết cuối cùng.
- So sánh hiệu quả của MAD với cách hỏi trực tiếp một LLM nền trên benchmark FEVER.

## Ý tưởng hệ thống

Hệ thống mô phỏng một phiên tranh biện số gồm các vai trò chính:

- Defender Agent: bảo vệ khả năng bản tin là đúng, tạo các nhận định dạng D1, D2, ... dựa trên bằng chứng hiện có.
- Challenger Agent: phản biện bản tin, tạo các nhận định dạng C1, C2, ... nhằm tìm lỗi thực thể, thời gian, logic, diễn giải hoặc thiếu bằng chứng.
- Search/Query Planning Module: lập kế hoạch truy vấn cho từng phía, ưu tiên Tavily nếu có khóa API và dùng Wikipedia làm phương án dự phòng.
- Source Scorer: chấm điểm độ tin cậy của nguồn bằng chứng đã thu thập.
- Claims Registry: lưu lịch sử các nhận định D*/C* qua nhiều vòng, giúp tranh luận nhắm vào claim cụ thể thay vì lan man.
- Judge Agent: tổng hợp knowledge base, source scores và debate history để sinh verdict cuối cùng.

Luồng tổng quát:

```text
User Input
  -> Query Planning
  -> Evidence Search
  -> Source Scoring
  -> Defender / Challenger Debate
  -> Save Round & Update MADState
  -> Judge
  -> Verdict
```

## Hai chế độ vận hành

### Search Mode

Chế độ này dùng khi cần kiểm chứng một bản tin trong bối cảnh mở.

Luồng chính trong `graph/workflow.py`:

```text
prepare_round
  -> search_defender + search_round
  -> score_sources
  -> defender
  -> challenger
  -> save_round
  -> judge
```

Đặc điểm:

- Mỗi vòng tranh luận có thể tạo truy vấn tìm kiếm riêng cho Defender và Challenger.
- Tavily được ưu tiên nếu có `TAVILY_API_KEY`.
- Nếu Tavily không khả dụng, hệ thống fallback sang Wikipedia.
- Nguồn bằng chứng được lưu vào `knowledge_base` với mã như `[S1]`, `[S2]`, ...
- `source_scores` hỗ trợ Judge cân nhắc chất lượng nguồn.

### Non-search Mode

Chế độ này dùng khi bằng chứng đã được cung cấp sẵn, ví dụ trong đánh giá FEVER.

Luồng chính:

```text
prepare
  -> defender
  -> challenger
  -> save_round
  -> judge
```

Đặc điểm:

- Không gọi tìm kiếm web.
- `initial_context` được nạp thành nguồn `[S1]` với trust score bằng `1.0`.
- Phù hợp cho benchmark có claim và evidence cố định.

## Cấu trúc thư mục

```text
.
├── agents/                  # Các tác tử và module xử lý chính
│   ├── defender.py           # Defender Agent
│   ├── challenger.py         # Challenger Agent
│   ├── search_agent.py       # Query planning và evidence search
│   ├── evaluator.py          # Source scoring, parser và helper định dạng
│   └── judge.py              # Tổng hợp phán quyết cuối cùng
├── graph/
│   ├── state.py              # MADState và state reducers
│   └── workflow.py           # LangGraph workflows cho search/non-search mode
├── prompts/                  # Prompt templates ở mức hệ thống
├── config/                   # Cấu hình model, search và debate
├── utils/                    # Rate limiting và retry wrapper
├── scripts/                  # Chuẩn bị dữ liệu và chạy benchmark
├── data/                     # Raw data, processed data và kết quả đánh giá
├── docs/                     # Tài liệu kiến trúc và định hướng sản phẩm
├── main.py                   # Entry point CLI và hàm run_mad
├── app.py                    # Gradio demo UI
└── README.md
```

## Cài đặt

### Tạo môi trường Python

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### Cài dependencies

```bash
pip install -r requirements.txt
```

## Cấu hình môi trường

Tạo file `.env` ở thư mục gốc dự án. Không commit file này lên Git vì có chứa khóa API.

Ví dụ:

```env
NINEROUTER_API_KEY=nr_xxxxxxxxxxxxxxxxxxxxxxxx
NINEROUTER_BASE_URL=https://your-ninerouter-base-url
NINEROUTER_MODEL=llama3

# Tùy chọn. Nếu không có, hệ thống dùng Wikipedia fallback.
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxxxx
```

Các biến chính:

| Biến | Bắt buộc | Ý nghĩa |
| --- | --- | --- |
| `NINEROUTER_API_KEY` | Có | Khóa API cho provider tương thích OpenAI/NineRouter |
| `NINEROUTER_BASE_URL` | Có | Base URL của provider |
| `NINEROUTER_MODEL` | Có/khuyến nghị | Tên model dùng cho các tác tử |
| `TAVILY_API_KEY` | Không | Bật tìm kiếm Tavily trong Search Mode |

## Chạy hệ thống

### Chạy thử bằng CLI

```bash
python main.py
```

`main.py` hiện chạy một ví dụ kiểm chứng mẫu và in verdict cuối cùng ra terminal.

### Gọi từ code Python

```python
from main import run_mad

result = run_mad(
    news_text="Nội dung bản tin hoặc claim cần kiểm chứng",
    debate_mode="search",
)

print(result["verdict"])
```

Ví dụ dùng Non-search Mode:

```python
from main import run_mad

result = run_mad(
    news_text="Claim cần kiểm chứng",
    initial_context="Bằng chứng hoặc ngữ cảnh đã có sẵn",
    debate_mode="non_search",
)

print(result["verdict"])
```

## Chuẩn bị dữ liệu và đánh giá

### FEVER

Chuẩn bị dữ liệu FEVER nhị phân:

```bash
python scripts/prepare_fever.py --n 40
```

Chạy benchmark FEVER:

```bash
python scripts/test_fever.py --file data/processed/fever_claims_binary.json --n 40
```

Kết quả và log chi tiết được lưu trong `data/results/fever_logs/`.

### GossipCop và TruthfulQA

Dự án có script chuẩn bị dữ liệu cho GossipCop và TruthfulQA. Tuy nhiên, một số script đánh giá mở rộng có thể cần đồng bộ lại với API hiện tại của `main.py` trước khi chạy, vì hệ thống hiện dùng `get_llm()` và `run_mad()` thay cho cấu trúc nhiều model cũ.

## Kết quả thực nghiệm đã ghi nhận

Theo các lần chạy FEVER trong tài liệu dự án, MAD cải thiện độ chính xác so với Base LLM trên nhiều model:

| Model | Base LLM | MAD System | Cải thiện |
| --- | ---: | ---: | ---: |
| Llama 3.3 70B | 92.5% | 97.5% | +5.0% |
| Gemma 4-31B | 82.5% | 90.0% | +7.5% |
| GPT-OSS 120B | 85.0% | 92.5% | +7.5% |
| Gemini 3.1 Flash Lite | 80.0% | 85.0% | +5.0% |

Các kết quả này dùng mẫu FEVER nhị phân SUPPORTS/REFUTES và nên được hiểu trong phạm vi thiết lập thử nghiệm của dự án.

## Tài liệu dự án

Các tài liệu cần giữ được gom trong thư mục `docs/`:

- `docs/architecture.md`: tóm tắt kiến trúc hiện tại của hệ thống MAD.
- `docs/product-report-draft.md`: bản nháp báo cáo sản phẩm theo hướng VeriAI / AI Output Auditor.

Các file báo cáo LaTeX, slide và hình minh họa cũ đã được loại bỏ khỏi repo sau khi hoàn tất phần viết báo cáo.

## Trạng thái hiện tại và lưu ý kỹ thuật

- Workflow chính trong code hiện dùng một LLM instance cấu hình qua `NINEROUTER_MODEL`.
- `score_sources` đang được dùng trong Search Mode để chấm nguồn.
- Hàm đánh giá vòng tranh luận trong `agents/evaluator.py` có tồn tại nhưng chưa được nối trực tiếp vào workflow chính.
- `app.py` là demo UI Gradio, nhưng có thể cần đồng bộ thêm nếu cấu hình model hoặc chữ ký hàm workflow đã thay đổi.

## Hướng phát triển

- Đồng bộ Gradio UI với workflow hiện tại.
- Ổn định JSON output bằng schema hoặc tool calling.
- Tích hợp chặt hơn evaluator/gatekeeper nếu muốn đánh giá từng vòng tranh luận.
- Mở rộng benchmark sang GossipCop và TruthfulQA sau khi đồng bộ script.
- Tối ưu chi phí và tốc độ bằng model routing hoặc cấu hình model theo vai trò.
- Mở rộng sang kiểm chứng đa ngôn ngữ và đa phương tiện.
