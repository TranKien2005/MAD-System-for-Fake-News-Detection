# Kiến trúc hệ thống MAD

Tài liệu này tóm tắt kiến trúc hiện tại của MAD System for Fake News Detection. Đây là bản ngắn gọn để thay thế tài liệu thiết kế cũ đã lỗi encoding và không còn khớp hoàn toàn với code.

## Mục tiêu hệ thống

MAD System kiểm chứng một claim hoặc đoạn tin bằng quy trình nhiều bước:

1. Chuẩn bị trạng thái ban đầu cho phiên kiểm chứng.
2. Thu thập hoặc nạp bằng chứng.
3. Cho hai tác tử đối kháng tranh luận qua nhiều vòng.
4. Lưu lịch sử nhận định, nguồn và phản biện.
5. Judge tổng hợp bằng chứng và đưa ra verdict cuối cùng.

Điểm cốt lõi của hệ thống là không để một LLM trả lời trực tiếp, mà tổ chức quá trình kiểm chứng thành workflow có vai trò, state và lịch sử tranh luận rõ ràng.

## Luồng tổng quan

```text
User Input
  -> Build Initial MADState
  -> Evidence Search hoặc Initial Context Loading
  -> Source Scoring
  -> Defender Agent
  -> Challenger Agent
  -> Save Round
  -> Loop nếu chưa đủ số vòng
  -> Judge Agent
  -> Verdict
```

## Hai chế độ vận hành

### Search Mode

Dùng khi người dùng nhập một claim/tin tức và hệ thống cần tự tìm bằng chứng bên ngoài.

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

- Search Agent lập truy vấn theo vai trò tranh luận.
- Tavily được ưu tiên nếu có `TAVILY_API_KEY`.
- Nếu không có Tavily, hệ thống fallback sang Wikipedia.
- Nguồn được lưu trong `knowledge_base` với ID như `[S1]`, `[S2]`.
- `source_scores` được dùng để Judge cân nhắc chất lượng nguồn.

### Non-search Mode

Dùng khi evidence/context đã có sẵn, ví dụ benchmark FEVER.

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
- `initial_context` được nạp thành nguồn `[S1]` với trust score `1.0`.
- Phù hợp khi cần đánh giá trên dataset có evidence cố định.

## Các module chính

### `main.py`

- Cung cấp `get_llm()` và `run_mad(...)`.
- Chọn workflow theo `debate_mode`.
- Tạo `MADState` ban đầu.
- Gọi LangGraph workflow và trả về state cuối.

### `app.py`

- Giao diện demo Gradio.
- Stream tiến trình các node của workflow.
- Hiển thị nguồn, claims registry, lịch sử tranh luận và verdict.

### `graph/state.py`

- Định nghĩa `MADState` và các reducer.
- Quản lý các phần quan trọng như:
  - `knowledge_base`
  - `source_scores`
  - `claims_registry`
  - `debate_history`
  - `pending_search_requests`
  - `executed_queries`
  - `round_search_results`

### `graph/workflow.py`

- Xây dựng hai LangGraph workflow: search và non-search.
- Điều phối thứ tự node.
- Lặp qua các vòng tranh luận cho đến khi đủ `max_rounds`, sau đó chuyển sang Judge.

### `agents/search_agent.py`

- Lập kế hoạch truy vấn evidence.
- Gọi Tavily hoặc Wikipedia fallback.
- Lọc, deduplicate và đưa kết quả vào `knowledge_base`.

### `agents/defender.py`

- Tạo lập luận bảo vệ khả năng claim là đúng.
- Sinh các nhận định dạng `D1`, `D2`, ...
- Ghi nhận quan hệ `ASSERT`, `REBUT`, `DEFEND` trong claims registry.

### `agents/challenger.py`

- Tạo lập luận phản biện claim.
- Sinh các nhận định dạng `C1`, `C2`, ...
- Tập trung tìm lỗi factual, logic, thiếu bằng chứng hoặc diễn giải sai.

### `agents/evaluator.py`

- Chứa helper parse JSON, format knowledge base và chấm điểm nguồn.
- `score_sources` đang được nối trong search workflow.
- `evaluate_round` tồn tại nhưng chưa phải node chính trong workflow hiện tại.

### `agents/judge.py`

- Tổng hợp debate history, knowledge base và source scores.
- Gọi Judge prompt để đưa ra verdict cuối.
- Parse JSON verdict một cách robust hơn để giảm lỗi format.

### `prompts/templates.py`

- Chứa prompt contract cho từng vai trò.
- Khi đổi schema output của agent, cần cập nhật parser/UI tương ứng.

### `config/settings.py`

- Đọc model và cấu hình runtime từ môi trường.
- Quản lý số vòng tranh luận, giới hạn tìm kiếm và rate limit.

## State quan trọng

Một phiên kiểm chứng được xoay quanh `MADState`. Các trường quan trọng:

- `original_news`: claim hoặc đoạn tin gốc.
- `knowledge_base`: danh sách evidence nguồn `[S*]`.
- `source_scores`: điểm độ tin cậy nguồn.
- `claims_registry`: lịch sử claim `D*`/`C*` và quan hệ phản biện/bảo vệ.
- `debate_history`: tóm tắt từng vòng tranh luận.
- `current_round`, `max_rounds`: điều khiển vòng lặp.
- `verdict`: kết luận cuối từ Judge.

## Hướng mở rộng sản phẩm

Từ kiến trúc này, hệ thống có thể mở rộng từ kiểm chứng tin giả sang sản phẩm kiểm định đầu ra AI:

```text
Câu hỏi gốc + câu trả lời AI cần kiểm định
  -> Tách các claim chính
  -> Tìm/nạp evidence
  -> Agent ủng hộ phân tích điểm hợp lý
  -> Agent phản biện tìm lỗi và hallucination
  -> Judge chấm audit score
  -> Gợi ý bản trả lời đã sửa
```

Hướng này được mô tả chi tiết hơn trong `docs/product-report-draft.md`.
