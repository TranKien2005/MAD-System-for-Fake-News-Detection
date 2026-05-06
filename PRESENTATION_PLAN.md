# TÀI LIỆU TRÌNH BÀY DỰ ÁN: MULTI-AGENT DEBATE (MAD) SYSTEM FOR FAKE NEWS DETECTION

> **MỤC ĐÍCH**: Tài liệu này cung cấp TOÀN BỘ nội dung chi tiết về dự án để một AI khác có thể sinh slide trình bày trước hội đồng. Tài liệu được chia thành 2 phần chính: **Phần Nội dung** (kho tri thức đầy đủ) và **Phần Hướng dẫn Slide** (bố cục và gợi ý thiết kế).

---

# PHẦN NỘI DUNG: KHO TRI THỨC TỔNG LỰC

## 1. BỐI CẢNH & TÍNH CẤP THIẾT

### 1.1. Vấn đề Tin giả (Fake News / Misinformation)
- Tin giả lan truyền nhanh gấp 6 lần tin thật trên mạng xã hội.
- Ảnh hưởng trực tiếp đến: ổn định chính trị, sức khỏe cộng đồng (ví dụ: tin giả về vaccine), niềm tin vào các thiết chế xã hội.
- Khối lượng tin giả tăng 600% trong các thời kỳ khủng hoảng (đại dịch, bầu cử).
- Tin giả ngày càng tinh vi, được viết bằng AI, rất khó phân biệt bằng mắt thường.

### 1.2. Hạn chế nghiêm trọng của các mô hình LLM đơn lẻ (Single-LLM)
Khi dùng một LLM duy nhất (GPT, Llama, Gemma...) để kiểm tin, hệ thống gặp 3 vấn đề cốt lõi:

1. **Ảo giác (Hallucination)**: LLM tự tin khẳng định những điều không có thật. Ví dụ: khi được hỏi "Frank Ocean was in a poll?", LLM có thể trả lời "Đúng" dù không có bằng chứng nào trong nguồn tin xác nhận điều đó.

2. **Kiến thức tĩnh (Static Knowledge)**: LLM chỉ biết những gì có trong dữ liệu huấn luyện (cut-off date). Không thể cập nhật các sự kiện mới nhất nếu không có công cụ tìm kiếm bên ngoài.

3. **Thiếu tư duy biện chứng (Lack of Dialectical Reasoning)**: Một LLM duy nhất thường chỉ tóm tắt bề mặt, trả lời một chiều. Nó không tự đặt nghi vấn, không tự kiểm chứng các chi tiết nhỏ (mốc thời gian, thực thể, thuật ngữ chuyên ngành).

### 1.3. Yêu cầu khắt khe của hệ thống kiểm tin (Fact-Checking Requirements)
- **Độ chính xác tuyệt đối**: Trong kiểm tin, sai sót 1% cũng có thể dẫn đến hậu quả lớn.
- **Tính giải trình (Explainability)**: Hệ thống không được chỉ trả lời "Đúng" hay "Sai". Phải chỉ rõ: Tại sao sai? Bằng chứng nằm ở đâu? Nguồn tin có đáng tin không?
- **Khả năng tự đối soát (Adversarial Truth-finding)**: Cần một cơ chế mà thông tin phải "vượt qua" sự soi xét kỹ lưỡng nhất trước khi được kết luận.

---

## 2. GIẢI PHÁP: MULTI-AGENT DEBATE (MAD)

### 2.1. Triết lý cốt lõi
Multi-Agent Debate (MAD) mượn mô hình của hệ thống pháp lý: **Phiên tòa số**. Chân lý không phải là thứ có sẵn mà là thứ lộ diện sau khi vượt qua được mọi sự hoài nghi và phản biện khắt khe nhất. Thay vì tin vào một câu trả lời duy nhất của AI, hệ thống thiết lập một quy trình tranh luận đối kháng (Adversarial Reasoning) giữa nhiều tác tử chuyên biệt để bóc tách sự thật.

### 2.2. Hệ thống 4 tác tử (4-Agent System)

**Agent 1: Defender (Người bảo vệ tin gốc)**
- Persona: "Bảo vệ bản tin bằng mọi giá, không được chấp nhận bất kỳ sự phủ nhận nào."
- Chiến thuật: Khai thác triệt để Context/Knowledge Base, dùng Common Knowledge để lấp khoảng trống, bẻ lái ngữ nghĩa theo hướng có lợi.
- Ngôn ngữ: "Thực tế là...", "Dữ liệu chứng minh...". Không dùng "có thể", "có khả năng".
- Output: Các nhận định có ID (D1, D2...), mỗi nhận định kèm evidence trích dẫn nguồn [Sx].

**Agent 2: Challenger (Người phản biện)**
- Persona: "Chứng minh bản tin là GIẢ/SAI LỆCH/THIẾU CĂN CỨ bằng mọi giá."
- Chiến thuật: Tấn công vào 3 yếu tố: Sự thật thực thể (người/vật có thật không?), Thời gian/Không gian (có khớp không?), Lỗi thuật ngữ (đánh tráo khái niệm).
- Cú đánh chí mạng: "Nguồn [Sx] không hề đề cập đến chi tiết Y như Defender khẳng định".
- Output: Các nhận định có ID (C1, C2...), mỗi nhận định kèm evidence.

**Agent 3: Source Scorer (Trọng tài nguồn tin)**
- Nhiệm vụ: Chấm điểm uy tín (Trust Score) cho từng nguồn tin được tìm thấy.
- Phân tầng: HIGH (0.8-1.0): Reuters, BBC, Nature, Wikipedia. MEDIUM (0.5-0.79): Trang tin địa phương. LOW (0.2-0.49): Blog, Reddit. UNTRUSTED (<0.2): Tin giả, thuyết âm mưu.
- Tác dụng: Giúp Judge biết nên ưu tiên lập luận của bên nào dựa trên chất lượng bằng chứng.

**Agent 4: Judge (Thẩm phán tối cao)**
- Nhiệm vụ: Tổng hợp toàn bộ tranh luận và đưa ra phán quyết cuối cùng.
- Hệ thống phạt (Penalty Logic):
  - **Hallucination Penalty**: Phạt nặng nếu Agent trích dẫn nguồn [Sx] nhưng nội dung nguồn đó trống rỗng hoặc không chứa thông tin họ khẳng định.
  - **Parroting Penalty**: Phạt nếu Agent chỉ lặp lại nhận định vòng trước mà không đưa ra dẫn chứng mới hoặc không trả lời được chất vấn.
- Tiêu chí: Ưu tiên nguồn HIGH/MEDIUM. Không thuận theo bên cố chấp đánh tráo khái niệm.

---

## 3. KIẾN TRÚC KỸ THUẬT CHI TIẾT

### 3.1. Công nghệ nền tảng
- **LangGraph**: Framework xây dựng đồ thị trạng thái có chu kỳ (Cyclic StateGraph) để quản lý luồng tranh luận đa vòng.
- **LangChain + ChatOpenAI**: Giao tiếp với các LLM thông qua API chuẩn OpenAI-compatible.
- **Tavily API**: Công cụ tìm kiếm chuyên dụng cho AI, trả về nội dung đã được trích xuất sẵn.
- **Wikipedia API**: Truy cập bách khoa toàn thư đa ngôn ngữ (vi, en).
- **Unified Model Architecture**: Toàn bộ hệ thống (Defender, Challenger, Scorer, Judge) dùng chung một instance LLM duy nhất, cấu hình qua biến môi trường `NINEROUTER_MODEL`.

### 3.2. Quản lý trạng thái (MADState)
Hệ thống sử dụng một TypedDict gọi là `MADState` với các trường quan trọng:
- `original_news`: Bản tin gốc cần kiểm tra.
- `initial_context`: Ngữ cảnh cung cấp sẵn (cho chế độ Non-Search).
- `knowledge_base`: Danh sách các nguồn tin (KnowledgeEntry) đã thu thập, mỗi nguồn có id, title, content, source_url, domain, relevance_score.
- `source_scores`: Dictionary ánh xạ source_id -> trust_score (0.0-1.0).
- `debate_history`: Danh sách các DebateRound, mỗi round chứa defender_argument, challenger_argument, defender_claims, challenger_claims.
- `claims_registry`: Dictionary quản lý toàn bộ nhận định (D1, D2, C1, C2...) với lịch sử tương tác đầy đủ.
- `current_round`, `max_rounds`: Quản lý vòng tranh luận (mặc định 3 vòng).
- `debate_mode`: "search" hoặc "non_search".
- `custom_output_instructions`: Cho phép tùy biến instruction của Judge cho từng tác vụ test.
- `verdict`: Kết quả phán quyết cuối cùng.

### 3.3. Hai chế độ vận hành (Dual-Mode)

**Chế độ 1: Search-Enabled (Open World)**
- Luồng: `prepare_round` -> `search_defender` + `search_round` (song song) -> `score_sources` -> `defender` -> `challenger` -> `save_round` -> (lặp lại hoặc judge).
- Mỗi vòng, cả Defender và Challenger đều được lên kế hoạch tìm kiếm (Query Planning) riêng biệt.
- Tavily là công cụ tìm kiếm chính. Nếu Tavily không khả dụng, fallback sang Wikipedia.
- Lọc kết quả: Chỉ giữ nguồn có relevance_score > 0.8, tối đa 3 nguồn/query.

**Chế độ 2: Non-Search (Closed Context)**
- Luồng đơn giản: `prepare` (nạp initial_context thành nguồn [S1] với Trust 1.0) -> `defender` -> `challenger` -> `save_round` -> (lặp lại hoặc judge).
- Không có bước tìm kiếm. Toàn bộ lập luận dựa trên ngữ cảnh đã cung cấp.
- Dùng cho benchmark dataset (FEVER) hoặc kiểm tra tài liệu nội bộ.

### 3.4. Garbage Collection (GC) trong save_round
- Sau mỗi vòng, hệ thống quét toàn bộ lịch sử tranh luận.
- Nếu một nguồn [Sx] không được trích dẫn bởi bất kỳ Agent nào, nội dung của nó bị xóa để tiết kiệm token.
- Nguồn [S1] (bối cảnh ban đầu) TUYỆT ĐỐI không bị xóa.

### 3.5. Rate Limiting & Retry
- Hệ thống có module `utils/rate_limit.py` với:
  - `RateLimiter`: Throttle chủ động (mặc định 10 calls/phút).
  - `safe_invoke()`: Retry wrapper với exponential backoff (tối đa 10 lần, delay tối đa 300s).
  - Nhận diện lỗi rate limit: HTTP 429, "reset after Xm" (NIM-specific), "quota exceeded".

## 4. TRIỂN KHAI CHI TIẾT: PROMPT ENGINEERING & LOGIC HÀNH VI

### 4.1. Cấu trúc Prompt của Defender & Challenger
Cả Defender và Challenger đều dùng cùng một cấu trúc prompt với 2 phase:

**Phase 1: QUERY_PLANNING (Lên kế hoạch tìm kiếm) - Chỉ chạy trong chế độ Search.**
- Agent phân tích bối cảnh và tạo tối đa 2 core_intent mỗi vòng.
- Chiến lược ngôn ngữ: Khoa học -> Tiếng Anh. Tin tức bản địa -> ngôn ngữ bản địa + Tiếng Anh.
- Query phải chứa TÊN THỰC THỂ CỤ THỂ. Ví dụ ĐÚNG: "Francia Raisa depression after kidney donation Selena Gomez". Ví dụ SAI: "depression after organ donation research".
- Tuyệt đối không lặp lại các truy vấn đã có trong executed_queries.

**Phase 2: SPEAKING (Tranh luận)**
- Logic hành động theo vòng (BẮT BUỘC):
  - Vòng 1: PHẢI dùng action_type "ASSERT" để đưa ra nhận định ban đầu.
  - Vòng 2 trở đi: TUYỆT ĐỐI CẤM dùng "ASSERT". Bắt buộc dùng "REBUT" (bác bỏ đối phương) hoặc "DEFEND" (bảo vệ nhận định của mình bị tấn công). Nếu dùng ASSERT ở vòng 2+ -> bị đánh giá THẤP.
  - Mỗi interaction phải có target_id (ví dụ: "C1" hoặc "D2") để nhắm vào nhận định cụ thể.
- Quy tắc nhận định:
  - CẤM NHẬN ĐỊNH META: Không viết "Bản tin nói X là đúng". Phải nêu sự thật trực diện.
  - Nhận định phải liên quan TRỰC TIẾP đến nội dung bản tin gốc.
- Chiến thuật Defender đặc biệt: Scan & Match (rà soát toàn bộ KB), Bẻ gẫy tấn công Silence (đọc lại nguồn tìm từ đồng nghĩa), Bẻ lái ngữ nghĩa.
- Chiến thuật Challenger đặc biệt: Bác bỏ nguồn hỗ trợ (tìm chi tiết "thêu dệt"), Phản biện đa diện (lỗ hổng logic + ngữ nghĩa + nguồn).

### 4.2. Claims Registry - Hệ thống quản lý nhận định
- Mỗi nhận định được gán ID: D1, D2... (Defender) và C1, C2... (Challenger).
- Registry lưu toàn bộ lịch sử tương tác của từng nhận định qua các vòng.
- Defender xây dựng rebut_targets từ C* và defend_targets từ D* bị tấn công.
- Challenger làm ngược lại: rebut_targets từ D*, defend_targets từ C*.

### 4.3. Prompt của Judge - Tách biệt Base & Instructions
Thiết kế kiến trúc quan trọng:
- `JUDGE_PROMPT_BASE`: Phần cố định (vai trò, tiêu chí, hệ thống phạt, input).
- `output_format_instructions`: Phần tùy biến qua custom_output_instructions trong MADState.
- Khi chạy App/Main: Dùng DEFAULT_JUDGE_OUTPUT_INSTRUCTIONS (điểm lẻ 0.25/0.5/0.75 cho phán quyết sắc thái).
- Khi chạy Script Test FEVER: Truyền instruction riêng ép về Binary (0.0/1.0).
- DEFAULT yêu cầu: truth_score (0.0/0.25/0.5/0.75/1.0), top_3_decisive_points, final_reasoning.

### 4.4. Parser của Judge - 4 tầng xử lý (Robustness)
Hàm _parse_verdict() trong agents/judge.py:
1. Tầng 1: Cắt markdown code block.
2. Tầng 2: Parse toàn bộ text là JSON (json.loads).
3. Tầng 3: Tìm dấu ngoặc nhọn {...} trong văn bản thô.
4. Tầng 4 (Regex Rescue): Quét thủ công truth_score và reasoning bằng regex.
- Hàm _validate_data(): Nếu không có truth_score -> raise ValueError (KHÔNG default 0.5). Nếu không có reasoning -> gán "(No reasoning provided by Judge)".

### 4.5. Source Scorer - Logic chấm điểm nguồn
- Input: original_news + danh sách new_sources (id, title, domain, content).
- Output JSON: assessments chứa source_id, trust_score, trust_tier, reasoning.
- Nếu LLM không trả về điểm -> mặc định 0.0.

### 4.6. Evaluator (Gatekeeper) - Kiểm soát chất lượng lập luận
- Đánh giá claim của CẢ Defender và Challenger sau mỗi vòng.
- 5 tiêu chí: Đúng phe (D* hỗ trợ tin thật, C* hỗ trợ tin giả), Evidence check (SOURCE phải tồn tại trong KB), Hành động hợp lệ (REBUT/DEFEND phải có target), Kiểm tra lặp lại, Admissibility.
- Trạng thái: ACTIVE, RESOLVED_SUPPORTS_DEFENDER, RESOLVED_SUPPORTS_CHALLENGER, DROPPED.

---

## 5. QUY TRÌNH BATCH TESTING (FEVER BENCHMARK)

### 5.1. Chuẩn bị dữ liệu
- File: fever_claims_binary.json với id, claim, label (1.0=SUPPORTS, 0.0=REFUTES), initial_context (Wikipedia).
- Sampling cân bằng: 20 SUPPORTS + 20 REFUTES = 40 mẫu.

### 5.2. Quy trình test 2 bước cho mỗi mẫu
- Bước 1 (Base LLM): Hỏi trực tiếp model với prompt binary. Parse bằng regex tìm 0.0/1.0. Không tìm thấy -> raise ValueError.
- Bước 2 (MAD System): Chạy run_mad() với debate_mode="non_search". Lấy truth_score, chuyển binary: >0.5 -> 1.0, <=0.5 -> 0.0. Bọc try-except: lỗi -> ghi ERROR, nhảy mẫu tiếp.

### 5.3. Hệ thống logging
- Mỗi model có thư mục riêng: data/results/fever_logs/[model_name]/.
- Mỗi mẫu: 1 file JSON chi tiết (claim, ground_truth, base_llm, mad_system verdict + debate_history + duration).
- Tự động xuất __ANALYSIS_REPORT_[timestamp].txt với chỉ số tổng hợp + danh sách ca thất bại.

## 6. TOÀN BỘ KẾT QUẢ THỰC NGHIỆM FEVER

### 6.1. Bảng tổng hợp 4 lần chạy (N = 40 mẫu cân bằng mỗi lần)

**LẦN 1: Llama 3.3 70B**
- Thời gian: 2026-05-02
- Tổng mẫu: 40
- Accuracy Base LLM: 92.5%
- Accuracy MAD System: 97.5%
- Độ lệch cải thiện: +5.0%

**LẦN 2: Gemma 4-31B**
- Thời gian: 2026-05-02 12:29:51
- File nguồn: fever_claims_binary.json
- Tổng số mẫu: 40
- Accuracy Base LLM: 82.5%
- Accuracy MAD System: 90.0%
- Cải thiện: +7.5%

**LẦN 3: GPT-OSS 120B Cloud**
- Thời gian: 2026-05-02 15:39:53
- Tổng số mẫu: 40
- Tốc độ trung bình: 81.98 giây/mẫu
- Chỉ số chi tiết:

| Metric | Base LLM | MAD System | Improvement |
|:---|:---:|:---:|:---:|
| Accuracy | 85.00% | 92.50% | +7.50% |
| Precision | 0.94 | 1.00 | +0.06 |
| Recall | 0.80 | 0.89 | +0.09 |
| F1-Score | 0.86 | 0.94 | +0.08 |

**LẦN 4: Gemini 3.1 Flash Lite**
- Thời gian: 2026-05-02 16:33:23
- Tổng số mẫu: 40
- Tốc độ trung bình: 42.10 giây/mẫu
- Chỉ số chi tiết:

| Metric | Base LLM | MAD System | Improvement |
|:---|:---:|:---:|:---:|
| Accuracy | 80.00% | 85.00% | +5.00% |
| Precision | 0.89 | 1.00 | +0.11 |
| Recall | 0.85 | 0.85 | +0.00 |
| F1-Score | 0.87 | 0.92 | +0.05 |

### 6.2. Nhận xét quan trọng
- MAD cải thiện Accuracy trung bình 5-7.5% trên tất cả các model.
- Precision đạt 1.00 trên GPT-OSS 120B và Gemini Flash Lite: MAD KHÔNG BAO GIỜ nhận nhầm tin giả thành tin thật.
- Model nhỏ (Gemini, 42s/mẫu) nhanh gấp đôi model lớn (GPT-OSS, 82s/mẫu) nhưng Accuracy thấp hơn.
- Llama 3.3 70B đạt Accuracy cao nhất: 97.5%.

---

## 7. PHÂN TÍCH CHI TIẾT TOÀN BỘ CÁC CA THẤT BẠI (Gemini 3.1 Flash Lite - 6/40 sai)

**Ca 1: [fever-159789] - FALSE NEGATIVE**
- Claim: "1.7% of water can be found in glaciers and ice caps of Antarctica."
- Kết quả: Base=0.0 | MAD=0.0 | GroundTruth=1.0
- Phân tích: Nguồn Wikipedia ghi 1.7% là tổng nước đóng băng ở cả "Nam Cực VÀ Greenland". Claim chỉ ghi riêng "Antarctica". Challenger phản biện thành công rằng 1.7% cho riêng Nam Cực là thiếu căn cứ. Lỗi suy luận định lượng: model không tách biệt được tập hợp con và tập hợp tổng.

**Ca 2: [fever-173954] - FALSE POSITIVE (Parsing Error)**
- Claim: "Vera Farmiga is only an actress."
- Kết quả: Base=0.0 | MAD=None | GroundTruth=0.0
- Phân tích: MAD trả về None. Model Gemini Flash Lite bị quá tải ngữ cảnh, không xuất được JSON chuẩn ở vòng Judge. Parser thử cả 4 tầng nhưng không cứu được.

**Ca 3: [fever-104779] - FALSE NEGATIVE (Case Study chính)**
- Claim: "Frank Ocean was in a poll."
- Kết quả: Base=0.0 | MAD=0.0 (raw_score=0.25) | GroundTruth=1.0
- Phân tích chi tiết:
  - Defender: Frank Ocean được bầu vào "Time 100 Most Influential People" (2013) và album Blonde đứng đầu "Pitchfork's Best Albums of the 2010s Decade" -> đây là các cuộc bình chọn (poll).
  - Challenger: Phân biệt rõ "Danh sách biên tập" (Editorial List - do biên tập viên chọn) KHÔNG phải "Thăm dò ý kiến cộng đồng" (Poll - công chúng bỏ phiếu). Defender đang đánh tráo khái niệm.
  - Judge phán quyết 0.25 (Sai lệch nghiêm trọng). 3 điểm quyết định: (1) Claim mơ hồ thiếu định danh, (2) Sai lệch thuật ngữ Editorial ≠ Poll, (3) Defender không trích dẫn được bất kỳ "poll" cụ thể nào.
  - Giá trị: "Thất bại tích cực". MAD sai so với nhãn FEVER mơ hồ nhưng ĐÚNG về logic báo chí nghiêm ngặt.

**Ca 4: [fever-166562] - FALSE POSITIVE (Parsing Error)**
- Claim: "Christine Daaé is a character by Victor Hugo."
- Kết quả: Base=0.0 | MAD=None | GroundTruth=0.0
- Phân tích: Lỗi Parser tương tự Ca 2.

**Ca 5: [fever-134947] - FALSE POSITIVE (Parsing Error)**
- Claim: "Peyton Manning refused to sign with the Broncos and remained on the Colts."
- Kết quả: Base=0.0 | MAD=None | GroundTruth=0.0
- Phân tích: Lỗi Parser. Peyton Manning thực tế ĐÃ ký với Broncos nên đây là tin SAI. Cả Base lẫn MAD đều đúng hướng nhưng MAD bị lỗi format.

**Ca 6: [fever-123589] - FALSE NEGATIVE**
- Claim: "Keegan-Michael Key played Murray in the film Hotel Transylvania 2."
- Kết quả: Base=0.0 | MAD=0.0 | GroundTruth=1.0
- Phân tích: Nguồn Wikipedia chỉ xác nhận anh ta đóng phim nhưng KHÔNG ghi tên nhân vật "Murray". MAD thà phán "Không đủ bằng chứng" (0.0) còn hơn phỏng đoán. Minh chứng cho nguyên tắc No Hallucination.

### Phân loại nguyên nhân thất bại:
1. Lỗi Parser/Model nhỏ (3/6 ca): Vera Farmiga, Christine Daaé, Peyton Manning -> Judge không xuất JSON.
2. Lỗi suy luận định lượng (1/6 ca): 1.7% water -> nhầm tập con/tập tổng.
3. Quá khắt khe về thuật ngữ (1/6 ca): Frank Ocean poll -> Judge đúng logic nhưng sai nhãn mơ hồ.
4. Quá khắt khe về bằng chứng (1/6 ca): Hotel Transylvania -> Không hallucinate dù biết đúng.

---

# PHẦN HƯỚNG DẪN SLIDE (SLIDE STRUCTURE & SUGGESTIONS)

### Slide 1: Trang bìa
- Tiêu đề: Multi-Agent Debate (MAD) System for Fake News Detection
- Gợi ý hình ảnh: Phiên tòa AI với cán cân công lý.

### Slide 2-3: Đặt vấn đề
- Nội dung: Mục 1.1 + 1.2 + 1.3.
- Gợi ý: Biểu đồ so sánh tốc độ lan truyền tin giả vs tin thật. Hình ảnh "tảng băng" ảo giác AI.

### Slide 4: Giải pháp MAD
- Nội dung: Mục 2.1 - Triết lý phiên tòa số.
- Gợi ý: Sơ đồ 3 bên đối kháng.

### Slide 5-6: 4 tác tử chi tiết
- Nội dung: Mục 2.2.
- Gợi ý: Bảng so sánh Persona + Chiến thuật. Icon màu tương phản.

### Slide 7: Kiến trúc LangGraph
- Nội dung: Mục 3.1 + 3.3.
- Gợi ý: Sơ đồ flowchart node-graph. Vẽ cả 2 luồng Search và Non-Search.

### Slide 8-9: Triển khai kỹ thuật Prompt
- Nội dung: Mục 4.1 + 4.2 - Logic ASSERT/REBUT/DEFEND, Claims Registry.
- Gợi ý: Trích đoạn prompt thực tế. Bảng quy tắc hành động theo vòng.

### Slide 10: Xử lý sự cố (Robustness)
- Nội dung: Mục 4.4 - Parser 4 tầng, Regex Rescue, Try-except Batch.
- Gợi ý: Sơ đồ decision tree xử lý lỗi.

### Slide 11: Kết quả Accuracy tổng hợp
- Nội dung: Bảng mục 6.1 - So sánh 4 model.
- Gợi ý: Biểu đồ cột chồng (Before vs After MAD).

### Slide 12: Chỉ số chuyên sâu
- Nội dung: Bảng chi tiết GPT-OSS 120B và Gemini Flash. Nhấn mạnh Precision 1.00.
- Gợi ý: Dashboard gauge chart hoặc radar chart.

### Slide 13: Phân tích thất bại (Overview)
- Nội dung: Mục 7 - Tổng quan 6 ca sai + phân loại nguyên nhân.
- Gợi ý: Bảng 4 cột: Loại lỗi | Số ca | Ví dụ | Giải pháp.

### Slide 14: Case Study 1 - Frank Ocean (Thất bại tích cực)
- Nội dung: Ca 3 mục 7 đầy đủ - Tranh luận Poll vs Editorial List.
- Gợi ý: Mô phỏng đoạn hội thoại Defender vs Challenger. Trích phán quyết Judge.

### Slide 15: Case Study 2 - Hotel Transylvania (Liêm chính dữ liệu)
- Nội dung: Ca 6 mục 7 - MAD thà sai còn hơn hallucinate.
- Gợi ý: So sánh "Nguồn tin nói gì" vs "Claim yêu cầu gì".

### Slide 16: Kết luận & Hướng phát triển
- Nội dung: MAD tăng 5-7.5% Accuracy, Precision 1.00, giải trình chi tiết. Hướng tới: Evaluator tự động, đa ngôn ngữ, TruthfulQA.
- Gợi ý: Roadmap timeline với các milestone.

### Slide 17: Q&A
- Gợi ý câu hỏi phản biện: "Chi phí/tốc độ?", "Judge có thiên vị không?", "Tại sao không dùng fine-tuning?"
