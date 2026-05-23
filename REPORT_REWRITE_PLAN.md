# Kế hoạch viết lại báo cáo đồ án MAD System

## Nguyên tắc viết

- Báo cáo là báo cáo đồ án, không phải slide, README hay ghi chú kỹ thuật ngắn.
- Không viết quá ngắn; mỗi ý cần có giải thích, liên hệ, lý do thiết kế và vai trò trong hệ thống.
- Không viết cả một chương trong một lần cập nhật. Mỗi lượt chỉ tập trung vào một vài mục nhỏ để đảm bảo đủ chi tiết.
- Trọng tâm của báo cáo là flow hệ thống: dữ liệu đi qua đâu, các module phối hợp thế nào, đầu vào/đầu ra từng thành phần là gì, vì sao thiết kế đó phù hợp với fake news detection.
- Không đi quá sâu vào prompt cụ thể trong code. Chỉ mô tả prompt engineering ở mức thiết kế: vai trò, ràng buộc đầu ra, structured output, kiểm soát hành vi tác tử.
- Mô tả hệ thống theo hướng chuyên nghiệp, có chiều sâu, thể hiện độ phức tạp và đầu tư của đồ án.
- Khi cần hình ảnh, chỉ để ghi chú trong LaTeX bằng comment `% GHI CHÚ HÌNH ẢNH: ...`; không tự tạo ảnh.
- Giữ trang bìa hiện tại và `logo.png` của UET.
- Nếu code hiện tại có điểm chưa đồng bộ, tránh trình bày như tính năng hoàn chỉnh nếu không chắc; có thể viết ở mức thiết kế/định hướng hoặc ghi nhận trong hạn chế.

## Bố cục báo cáo cuối cùng

### Phần đầu

1. Trang bìa
   - Giữ logo UET `logo.png`.
   - Giữ thông tin trường, đề tài, sinh viên, giảng viên, năm.

2. Lời cảm ơn
   - Viết trang trọng, ngắn vừa phải.

3. Lời cam đoan
   - Viết theo chuẩn báo cáo.

4. Tóm tắt
   - Bài toán phát hiện tin giả/fact-checking bằng LLM.
   - Hạn chế của single-LLM: hallucination, kiến thức tĩnh, thiếu phản biện.
   - Giải pháp: Multi-Agent Debate gồm Defender, Challenger, Source Scorer, Judge.
   - Điểm chính: tìm kiếm bằng chứng, tranh luận nhiều vòng, chấm điểm nguồn, truth_score.
   - Kết quả: MAD cải thiện accuracy so với Base LLM trên FEVER.

5. Mục lục, danh mục hình, danh mục bảng.

---

## Chương 1. Giới thiệu đề tài

### 1.1. Bối cảnh và động lực

Cần viết chi tiết, có liên hệ tới:
- Tin giả trong xã hội số.
- Tốc độ lan truyền thông tin và khó khăn khi người dùng tự kiểm chứng.
- Tác động trong y tế, chính trị, tài chính, cộng đồng.
- LLM có tiềm năng hỗ trợ phân tích và kiểm chứng thông tin.
- Nhưng single-LLM dễ hallucinate, trả lời một chiều, thiếu bằng chứng.
- Lý do cần một cơ chế có phản biện và truy xuất bằng chứng.

Không sa đà vào số liệu xã hội nếu không có nguồn học thuật rõ ràng.

### 1.2. Các hướng tiếp cận liên quan

Mục này nên được thêm để làm báo cáo có nền tảng hơn:
- Phân loại văn bản dựa trên đặc trưng ngôn ngữ.
- Phương pháp dựa trên lan truyền mạng xã hội.
- Fact-checking dựa trên truy xuất bằng chứng.
- Hỏi trực tiếp LLM.
- Phân tích ưu/nhược điểm từng nhóm.
- Kết luận: MAD là hướng kết hợp LLM + truy xuất bằng chứng + phản biện đa tác tử.

### 1.3. Bài toán đặt ra

Trình bày rõ:
- Đầu vào: bản tin, tiêu đề, claim, nhận định; có thể kèm context trong non-search mode.
- Đầu ra: truth_score, giải thích, decisive points, lịch sử tranh luận, nguồn bằng chứng.
- Ba bài toán con: tổ chức bằng chứng, lập luận đối kháng, tổng hợp phán quyết.

### 1.4. Mục tiêu đồ án

Chia thành:
- Mục tiêu tổng quát.
- Mục tiêu thiết kế hệ thống.
- Mục tiêu điều phối workflow.
- Mục tiêu quản lý bằng chứng.
- Mục tiêu quản lý lập luận.
- Mục tiêu đánh giá thực nghiệm.

### 1.5. Phạm vi thực hiện

Cần nói rõ:
- Chỉ xử lý văn bản.
- Chưa xử lý ảnh/video/audio.
- Không fine-tune model.
- Dùng LLM qua API OpenAI-compatible/NineRouter.
- Search mode dùng Tavily/Wikipedia.
- Non-search mode dùng context đầu vào.
- Benchmark chính: FEVER binary SUPPORTS/REFUTES.
- GossipCop/TruthfulQA là hướng mở rộng ở mức script thử nghiệm.

### 1.6. Đóng góp chính của đồ án

Nên có mục riêng:
- Kiến trúc MAD cho fake news detection.
- Kết hợp search, source scoring, claims registry, judge.
- Dual-mode search/non-search.
- Benchmark Base LLM vs MAD.
- Khả năng giải thích và truy vết.

### 1.7. Cấu trúc báo cáo

Tóm tắt 7 chương.

---

## Chương 2. Cơ sở lý thuyết và công nghệ sử dụng

### 2.1. Bài toán phát hiện tin giả và fact-checking

Nên viết rõ:
- Fake news detection là gì.
- Fact-checking khác classification thông thường thế nào.
- Vì sao cần evidence, provenance, explanation.
- Claim-level verification và document-level fake news detection.
- Các nhãn thường gặp: supports/refutes/not enough info; trong đồ án dùng binary.

### 2.2. Hạn chế của mô hình LLM đơn lẻ

Tập trung vào:
- Hallucination.
- Static knowledge.
- Thiếu phản biện/đối soát.
- Sensitivity to prompt.
- Không có audit trail nếu chỉ hỏi trực tiếp.

### 2.3. Retrieval-Augmented Generation trong kiểm chứng thông tin

Nên có trước hoặc sau MAD:
- Vì sao LLM cần bằng chứng ngoài.
- Retrieval, Knowledge Base, source citation.
- RAG giúp giảm hallucination nhưng chưa đủ nếu chỉ có một bước suy luận.
- Hệ thống dùng Knowledge Base chung cho các agent.

### 2.4. Multi-Agent Debate

Mô tả:
- Nhiều agent đảm nhận vai trò khác nhau.
- Cơ chế đối kháng giống phiên tòa số.
- Defender bảo vệ bản tin.
- Challenger phản bác.
- Source Scorer đánh giá nguồn.
- Judge tổng hợp.
- Lợi ích: tăng kiểm tra chéo, phát hiện lỗ hổng, tạo lịch sử suy luận.
- Hạn chế: tốn token, phụ thuộc LLM, cần điều phối tốt.

### 2.5. LangGraph và mô hình workflow dạng trạng thái

Nên thêm để nối sang Chương 3:
- LangGraph phù hợp vì debate là quy trình lặp.
- StateGraph giúp lưu trạng thái qua nhiều node.
- Các node xử lý: prepare, search, score, debate, save, judge.
- Reducer/state giúp cập nhật knowledge_base, debate_history, verdict.

### 2.6. Công nghệ sử dụng

Bảng công nghệ:
- Python.
- LangGraph.
- LangChain ChatOpenAI.
- NineRouter/OpenAI-compatible API.
- Tavily.
- Wikipedia.
- Gradio.
- FEVER.

Sau bảng cần viết phân tích vì sao chọn từng công nghệ, không chỉ liệt kê.

---

## Chương 3. Phân tích và thiết kế hệ thống

Đây là chương trọng tâm. Cần viết rất kỹ, chia thành nhiều lượt nhỏ.

### 3.1. Tổng quan kiến trúc hệ thống

Nội dung:
- Mô tả hệ thống như một pipeline kiểm chứng nhiều vòng.
- Flow tổng quát:
  User Input -> Query Planning -> Evidence Search -> Source Scoring -> Defender/Challenger Debate -> Judge -> Verdict.
- Nhấn mạnh dữ liệu không đi một chiều đơn giản mà được lưu trong state và tái sử dụng qua các vòng.
- Có 2 chế độ: Search Mode và Non-Search Mode.

Ghi chú hình:
- `% GHI CHÚ HÌNH ẢNH: Sơ đồ tổng quan kiến trúc MAD System từ input đến verdict.`

### 3.2. Các thành phần chính

Viết lần lượt từng mục, không viết hết một lượt nếu quá dài.

#### 3.2.1. Defender Agent
- Vai trò.
- Input.
- Output.
- Cách dùng evidence.
- Claim ID D1/D2.
- Vai trò trong adversarial reasoning.

#### 3.2.2. Challenger Agent
- Vai trò.
- Input/output.
- Claim ID C1/C2.
- Tập trung vào lỗi thực thể, thời gian, logic, ngữ nghĩa, thiếu bằng chứng.

#### 3.2.3. Search/Query Planning Module
- Không gọi là agent độc lập nếu code coi là module.
- Mỗi vòng tạo query riêng cho mỗi phía.
- Không lặp executed_queries.
- Tavily trước, Wikipedia fallback.
- relevance_score > 0.8.
- Source ID [S1], [S2].

#### 3.2.4. Source Scorer
- Chấm trust_score.
- Input/output.
- Trust giúp Judge cân nhắc lập luận.

#### 3.2.5. Claims Registry
- Mục rất quan trọng.
- Lưu toàn bộ claim D*/C*.
- Mỗi claim có lịch sử nhiều vòng.
- Vòng 1 ASSERT.
- Vòng 2+ REBUT/DEFEND nhắm claim cụ thể.
- Tránh tranh luận lan man.

#### 3.2.6. Judge Agent
- Nhận knowledge_base, source_scores, debate_history.
- Có logic penalty mức thiết kế: hallucination/parroting/không có evidence.
- Output JSON: truth_score, top_3_decisive_points, final_reasoning.

### 3.3. Thiết kế trạng thái MADState

Cần có bảng:
- Input: original_news, initial_context.
- Knowledge: knowledge_base, source_scores.
- Search: pending_search_requests, executed_queries.
- Debate: current_round, debate_history, claims_registry.
- Output: verdict.

Sau bảng cần giải thích vì sao state quan trọng trong multi-round debate.

### 3.4. Luồng xử lý Search Mode

Cần viết thật cụ thể từng node:
- prepare_round.
- search_defender.
- search_round.
- score_sources.
- defender.
- challenger.
- save_round.
- judge.

Ghi chú hình:
- `% GHI CHÚ HÌNH ẢNH: Sơ đồ LangGraph Search Mode với vòng lặp qua max_rounds.`

### 3.5. Luồng xử lý Non-Search Mode

Dùng cho FEVER:
- prepare.
- load initial_context as [S1].
- defender/challenger/save_round/judge.
- Không search web.
- Trust [S1] = 1.0.
- Phù hợp benchmark.

### 3.6. Cơ chế kiểm soát lỗi và độ bền hệ thống

Gồm:
- Rate limiter.
- Retry 429/quota.
- Judge parser nhiều tầng.
- GC để giảm token.
- Fallback Wikipedia.
- Structured output ở mức thiết kế.

---

## Chương 4. Cài đặt và triển khai

### 4.1. Cấu trúc thư mục dự án

Cần map code với thiết kế:
- agents/.
- graph/.
- prompts/.
- scripts/.
- data/.
- main.py.
- app.py.

### 4.2. Cấu hình môi trường

- Python.
- requirements.
- .env.
- NINEROUTER_API_KEY.
- NINEROUTER_BASE_URL.
- NINEROUTER_MODEL.
- TAVILY_API_KEY.

### 4.3. Triển khai workflow LangGraph

- build_workflow.
- build_non_search_workflow.
- Điều kiện dừng max_rounds.
- State reducers.

### 4.4. Triển khai các tác tử

- defender.py.
- challenger.py.
- search_agent.py.
- evaluator/source scorer.
- judge.py.

### 4.5. Structured output và prompt ở mức thiết kế

Không đi vào prompt chi tiết.
Nói về:
- Phase query planning.
- Phase speaking.
- JSON contracts.
- Judge output instructions.
- Robust parsing.

### 4.6. Giao diện demo và entry point

- main.py cho CLI/script.
- app.py cho Gradio demo.
- Nếu UI chưa đồng bộ code, trình bày ở mức giao diện demo/định hướng, không khẳng định quá mức.

---

## Chương 5. Thực nghiệm và phương pháp đánh giá

### 5.1. Mục tiêu thực nghiệm

- MAD có cải thiện so với Base LLM không?
- MAD có giải thích được quyết định không?
- MAD có giảm xu hướng đoán thiếu căn cứ không?

### 5.2. Tập dữ liệu FEVER

- Claim + evidence Wikipedia.
- SUPPORTS/REFUTES.
- Quy đổi 1.0/0.0.
- Sampling cân bằng.

### 5.3. Chuẩn bị dữ liệu

- prepare_fever.py.
- Đọc FEVER.jsonl.
- Lọc verifiable.
- Lấy Wikipedia evidence.
- Xuất fever_claims_binary.json.

### 5.4. Quy trình đánh giá Base LLM vs MAD

- Base LLM direct prompt.
- MAD non_search.
- truth_score > 0.5 -> 1.0.
- Lưu log.

### 5.5. Chỉ số đánh giá

- Accuracy.
- Precision.
- Recall.
- F1-score.
- Avg duration.
- Parsing/system errors.

---

## Chương 6. Kết quả và phân tích

### 6.1. Kết quả tổng hợp

Bảng:
- Llama 3.3 70B: 92.5 -> 97.5.
- Gemma 4-31B: 82.5 -> 90.0.
- GPT-OSS 120B: 85.0 -> 92.5.
- Gemini 3.1 Flash Lite: 80.0 -> 85.0.

### 6.2. So sánh hiệu năng giữa các mô hình

- MAD cải thiện ổn định.
- Precision cao.
- Model lớn chính xác hơn nhưng chậm hơn.
- Model nhỏ nhanh hơn nhưng dễ lỗi format.

### 6.3. Phân tích các ca thất bại

Chọn 2-3 case:
- Frank Ocean was in a poll.
- Hotel Transylvania 2.
- Parsing error với model nhỏ.

### 6.4. Nhận xét chung

- MAD thận trọng hơn.
- Có khả năng giải thích tốt hơn classification.
- Đổi lại chi phí thời gian/token cao.
- Dataset label có thể mơ hồ.

---

## Chương 7. Kết luận và hướng phát triển

### 7.1. Kết luận

- Đã xây dựng hệ thống MAD cho fake news detection.
- Có debate nhiều vòng, evidence, claims registry, judge.
- Thực nghiệm cho thấy cải thiện so với Base LLM.
- Có khả năng giải thích và truy vết tốt hơn.

### 7.2. Hạn chế

- Chưa tối ưu tốc độ.
- Phụ thuộc LLM và chất lượng search/context.
- Structured output vẫn có thể lỗi với model nhỏ.
- UI/demo cần đồng bộ thêm nếu code chưa khớp.
- Chưa xử lý multimodal.

### 7.3. Hướng phát triển

- Đồng bộ UI và workflow.
- Bổ sung/gắn chặt Evaluator nếu muốn gatekeeper đầy đủ.
- Dùng schema/tool calling để ổn định JSON.
- Mở rộng benchmark TruthfulQA/GossipCop.
- Model routing để tối ưu chi phí.
- Multilingual và multimodal verification.

## Thứ tự thực hiện tiếp theo

1. Kiểm tra lại phần hiện có trong `main.tex` và điều chỉnh Chương 1 nếu còn quá ngắn.
2. Mở rộng Chương 2 theo từng cụm: 2.1-2.2, rồi 2.3-2.4, rồi 2.5-2.6.
3. Viết Chương 3 theo từng cụm nhỏ: 3.1, rồi 3.2.1-3.2.2, rồi 3.2.3-3.2.6, rồi 3.3, rồi 3.4-3.6.
4. Sau mỗi cụm, kiểm tra heading và LaTeX cơ bản.
5. Không dừng cho tới khi hoàn thành toàn bộ báo cáo, trừ khi cần người dùng quyết định nội dung chưa rõ.
