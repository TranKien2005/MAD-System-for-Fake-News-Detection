# Chương trình AI Thực chiến – Báo cáo sản phẩm sau 6 tuần

> Bản nháp định hướng sản phẩm dựa trên dự án Multi-Agent Debate cho kiểm chứng tin giả hiện tại. Các thông tin nhóm, link demo và chỉ số thực nghiệm cần được cập nhật sau khi nhóm có dữ liệu thật.

## 1. Thông tin nhóm

- **Tên nhóm:** [Cập nhật]
- **Tên sản phẩm:** VeriAI – AI Output Auditor
- **Lĩnh vực ứng dụng:** AI Governance, AI Quality Assurance, Fact-checking, EdTech, Productivity
- **Đại diện nhóm:** [Cập nhật]
- **Email/SĐT liên hệ:** [Cập nhật]

## 2. One-liner sản phẩm

**VeriAI giúp người dùng kiểm tra độ tin cậy của câu trả lời do AI tạo ra bằng cách sử dụng cơ chế phản biện đa tác tử, đối chiếu bằng chứng và chấm điểm rủi ro trước khi kết quả được sử dụng.**

## 3. Bài toán đang giải quyết

### Người dùng mục tiêu là ai?

Người dùng mục tiêu ban đầu của VeriAI gồm:

- Sinh viên, học viên, người tự học đang dùng ChatGPT, Gemini, Claude hoặc các chatbot khác để hỗ trợ học tập, làm báo cáo, nghiên cứu.
- Người viết nội dung, content creator, nhân sự marketing cần dùng AI để tạo bài viết, tóm tắt thông tin hoặc chuẩn bị nội dung xuất bản.
- Nhân viên văn phòng hoặc nhóm doanh nghiệp nhỏ sử dụng AI để soạn email, báo cáo, phân tích thông tin hoặc trả lời khách hàng.

### Họ đang gặp vấn đề gì?

Người dùng ngày càng phụ thuộc vào AI để tạo câu trả lời nhanh, nhưng họ thường không biết câu trả lời đó có thực sự đáng tin hay không. Các mô hình AI có thể trả lời rất tự tin, mạch lạc và thuyết phục, nhưng vẫn có thể:

- Sai dữ kiện, ngày tháng, tên người, tên tổ chức hoặc số liệu.
- Bịa nguồn hoặc diễn giải sai nguồn.
- Bỏ sót điều kiện quan trọng trong câu hỏi.
- Suy luận thiếu logic nhưng trình bày như một kết luận chắc chắn.
- Trả lời đúng một phần nhưng thiếu bằng chứng để sử dụng trong bối cảnh học tập, báo cáo hoặc xuất bản.

### Vấn đề này gây mất thời gian, chi phí, rủi ro hoặc cơ hội như thế nào?

Nếu người dùng tin trực tiếp vào kết quả AI mà không kiểm tra lại, họ có thể gặp các rủi ro sau:

- **Mất thời gian:** phải tự kiểm tra thủ công từng thông tin bằng Google, tài liệu, Wikipedia hoặc nguồn tham khảo khác.
- **Rủi ro chất lượng:** bài báo cáo, bài viết hoặc nội dung học tập có thể chứa lỗi factual/hallucination.
- **Rủi ro uy tín:** nội dung sai nếu được gửi cho khách hàng, giảng viên, đồng nghiệp hoặc đăng công khai có thể làm giảm độ tin cậy của người dùng/tổ chức.
- **Rủi ro quyết định:** nếu dùng câu trả lời AI để hỗ trợ quyết định nghiệp vụ, lỗi thông tin có thể dẫn đến nhận định sai.

### Vì sao đây là bài toán đáng giải quyết?

Hiện nay, người dùng không còn thiếu công cụ tạo nội dung bằng AI. Vấn đề lớn hơn là **làm sao biết nội dung do AI tạo ra có đáng tin để sử dụng hay không**. Vì vậy, một lớp kiểm định độc lập cho đầu ra AI là cần thiết, đặc biệt trong các bối cảnh có yêu cầu về độ chính xác, bằng chứng và trách nhiệm sử dụng thông tin.

## 4. Insight quan trọng

Sau quá trình nghiên cứu và phát triển từ bài toán kiểm chứng tin giả, nhóm nhận thấy một insight quan trọng:

> Người dùng không chỉ cần một AI tạo câu trả lời, họ cần một AI có khả năng phản biện câu trả lời đó trước khi họ tin và sử dụng nó.

Các quan sát chính:

- Người dùng đang kiểm tra thủ công kết quả AI bằng cách tự tìm nguồn, đọc lại tài liệu hoặc hỏi thêm nhiều lần để xác nhận.
- Quy trình kiểm tra hiện tại tốn thời gian ở bước đối chiếu dữ kiện, phát hiện lỗi suy luận và đánh giá độ đáng tin của nguồn.
- Các chatbot hiện tại thường tập trung vào việc tạo câu trả lời nhanh, nhưng chưa cung cấp một cơ chế phản biện độc lập, có cấu trúc và có thể truy vết.
- AI có thể tạo thay đổi rõ rệt nếu được dùng như một **reviewer/auditor**, tức là không chỉ sinh nội dung mà còn kiểm tra, phản biện và đánh giá nội dung do AI khác tạo ra.

Insight cốt lõi của sản phẩm:

> Trong kỷ nguyên AI tạo sinh, niềm tin vào đầu ra AI cần được xây dựng bằng cơ chế kiểm định, không chỉ bằng sự trôi chảy của câu trả lời.

## 5. Giải pháp của nhóm

### Sản phẩm hoạt động như thế nào?

VeriAI nhận đầu vào gồm:

1. Câu hỏi hoặc nhiệm vụ ban đầu của người dùng.
2. Câu trả lời do một mô hình AI khác tạo ra.
3. Tùy chọn: ngữ cảnh, tài liệu tham chiếu, evidence hoặc link nguồn.

Sau đó hệ thống thực hiện quy trình kiểm định:

```text
User Input
  -> Tách các claim chính trong câu trả lời AI
  -> Tìm hoặc nạp bằng chứng liên quan
  -> Agent ủng hộ phân tích điểm hợp lý của câu trả lời
  -> Agent phản biện tìm lỗi, thiếu sót, hallucination và mâu thuẫn
  -> Agent đánh giá độ tin cậy của nguồn/bằng chứng
  -> Judge tổng hợp kết quả
  -> Trả về điểm tin cậy, lỗi quan trọng và gợi ý sửa
```

### AI được dùng ở bước nào?

AI được sử dụng ở các bước chính:

- Phân tích câu trả lời AI thành các nhận định có thể kiểm chứng.
- Lập kế hoạch tìm kiếm bằng chứng hoặc sử dụng context người dùng cung cấp.
- Tạo lập luận ủng hộ câu trả lời để tránh đánh giá một chiều.
- Tạo lập luận phản biện để phát hiện lỗi, điểm thiếu bằng chứng hoặc mâu thuẫn.
- Đánh giá chất lượng nguồn thông tin.
- Tổng hợp verdict cuối cùng và đề xuất bản trả lời cải thiện.

### Output cuối cùng người dùng nhận được là gì?

Người dùng nhận được:

- Điểm tin cậy tổng thể của câu trả lời AI.
- Mức cảnh báo: đáng tin / cần kiểm tra thêm / rủi ro cao.
- Các điểm đúng hoặc có cơ sở trong câu trả lời.
- Các điểm sai, thiếu bằng chứng hoặc đáng nghi.
- Bằng chứng hoặc nguồn liên quan nếu có.
- Giải thích ngắn gọn vì sao hệ thống đưa ra đánh giá đó.
- Gợi ý chỉnh sửa hoặc bản trả lời an toàn hơn.

### Điểm khác biệt chính của sản phẩm là gì?

VeriAI không phải là một chatbot trả lời câu hỏi thông thường. Sản phẩm đóng vai trò là **lớp kiểm định độc lập cho đầu ra của các chatbot khác**.

Điểm khác biệt chính:

- Sử dụng cơ chế **Multi-Agent Debate** thay vì để một model tự chấm câu trả lời của chính nó.
- Có cả agent ủng hộ và agent phản biện để đánh giá cân bằng hơn.
- Tập trung vào độ tin cậy, bằng chứng, lỗi suy luận và rủi ro sử dụng thực tế.
- Có thể dùng với đầu ra của nhiều mô hình AI khác nhau như ChatGPT, Gemini, Claude, Copilot hoặc chatbot nội bộ.

## 6. Tính năng nổi bật nhất

### 1. AI Output Audit Score

**Tính năng làm gì?**

Hệ thống chấm điểm độ tin cậy của câu trả lời AI dựa trên các tiêu chí như:

- Độ đúng factual.
- Độ đầy đủ so với câu hỏi gốc.
- Độ nhất quán logic.
- Mức độ có bằng chứng.
- Rủi ro hallucination.

**Mang lại giá trị gì cho người dùng?**

Người dùng có thể nhanh chóng biết câu trả lời AI có đủ tin cậy để sử dụng ngay hay cần kiểm tra lại. Điều này giúp giảm thời gian review thủ công và giảm rủi ro dùng sai thông tin.

### 2. Multi-Agent Debate Review

**Tính năng làm gì?**

Hệ thống sử dụng nhiều agent với vai trò khác nhau:

- Agent ủng hộ: tìm các điểm hợp lý và bằng chứng có thể bảo vệ câu trả lời.
- Agent phản biện: tìm lỗi factual, lỗi logic, điểm thiếu bằng chứng hoặc diễn giải sai.
- Judge: tổng hợp tranh luận và đưa ra đánh giá cuối cùng.

**Mang lại giá trị gì cho người dùng?**

Cơ chế phản biện chéo giúp giảm thiên kiến so với việc chỉ dùng một AI tự đánh giá một lần. Người dùng nhận được lý do rõ ràng hơn về việc câu trả lời đáng tin hoặc không đáng tin ở điểm nào.

### 3. Evidence-backed Fix Suggestions

**Tính năng làm gì?**

Hệ thống chỉ ra các phần cần sửa trong câu trả lời AI, gắn với lý do và bằng chứng liên quan. Sau đó hệ thống có thể đề xuất phiên bản trả lời đã được chỉnh sửa để an toàn và chính xác hơn.

**Mang lại giá trị gì cho người dùng?**

Người dùng không chỉ nhận một cảnh báo chung chung, mà có thể biết cần sửa gì, vì sao cần sửa và sửa theo hướng nào. Điều này biến hệ thống từ công cụ chấm điểm thành công cụ hỗ trợ cải thiện chất lượng đầu ra AI.

## 7. Demo & mức độ hoàn thiện

- **Link demo:** [Cập nhật]
- **Link video demo:** [Cập nhật]
- **Link slide pitching:** [Cập nhật]
- **Link GitHub/source code nếu có:** [Cập nhật]
- **Tài khoản test nếu có:** [Cập nhật]

### Mức độ hoàn thiện hiện tại

**Prototype / MVP sớm**

Giải thích ngắn gọn:

Dự án hiện đã có nền tảng kỹ thuật cho cơ chế Multi-Agent Debate, gồm workflow tìm bằng chứng, agent bảo vệ, agent phản biện, source scoring và Judge tổng hợp verdict. Phiên bản hiện tại ban đầu được xây dựng cho bài toán kiểm chứng tin giả. Để trở thành sản phẩm VeriAI, hệ thống cần được điều chỉnh giao diện và input/output theo hướng kiểm định câu trả lời do AI khác tạo ra, nhưng phần lõi phản biện đa tác tử đã có prototype hoạt động.

## 8. Kết quả sau 6 tuần

> Ghi chú: Các chỉ số dưới đây cần cập nhật bằng dữ liệu thật sau khi nhóm test sản phẩm. Không nên bịa số liệu nếu chưa đo được.

- **Số người đã test:** [Chưa đo / Cập nhật]
- **Số lượt sử dụng thử:** [Chưa đo / Cập nhật]
- **Độ chính xác/kết quả đầu ra:** Ở phiên bản kiểm chứng tin giả ban đầu, hệ thống đã được thử nghiệm trên bài toán FEVER binary SUPPORTS/REFUTES. Cần cập nhật lại chỉ số chính thức sau khi chạy test trên use case kiểm định đầu ra AI.
- **Thời gian xử lý:** [Cập nhật theo demo thực tế]
- **Chi phí vận hành ước tính:** Phụ thuộc vào model sử dụng, số vòng tranh luận, số lượt tìm kiếm và số lần gọi LLM. Cần đo trên từng cấu hình cụ thể.
- **Mức tiết kiệm thời gian/chi phí:** [Chưa đo / Cập nhật sau user test]
- **Phản hồi nổi bật từ người dùng:** [Cập nhật sau user test]
- **Kết quả đáng tự hào nhất:** Nhóm đã xây dựng được prototype có khả năng tổ chức phản biện đa tác tử, lưu lịch sử tranh luận, đối chiếu bằng chứng và đưa ra verdict có khả năng truy vết thay vì chỉ trả lời trực tiếp như một chatbot thông thường.

## 9. Công nghệ & kiến trúc

### AI model sử dụng

- Mô hình LLM thông qua API tương thích OpenAI/NineRouter.
- Model cụ thể có thể cấu hình bằng biến môi trường `NINEROUTER_MODEL`.

### Công cụ/framework

- Python
- LangGraph
- LangChain / LangChain OpenAI
- Gradio cho giao diện demo
- Tavily Search API nếu có khóa API
- Wikipedia fallback khi không có Tavily

### Database

- Phiên bản hiện tại chưa sử dụng database cố định.
- Trạng thái xử lý được quản lý trong LangGraph state.
- Kết quả benchmark/log có thể lưu dưới dạng file JSON trong thư mục kết quả.

### API tích hợp

- OpenAI-compatible/NineRouter API cho LLM.
- Tavily API cho tìm kiếm bằng chứng nếu được cấu hình.
- Wikipedia library làm nguồn fallback.

### Hạ tầng triển khai

- Prototype hiện có thể chạy local bằng Python và Gradio.
- Nếu triển khai thực tế, có thể đưa lên cloud/server với giao diện web, lưu lịch sử kiểm định và quản lý người dùng.

### Kiến trúc tổng quan

```text
Người dùng
  -> Giao diện Web/Gradio
  -> Input: câu hỏi gốc + câu trả lời AI cần kiểm định + context tùy chọn
  -> MAD Workflow
      -> Claim/Context Preparation
      -> Evidence Search hoặc Context Loading
      -> Source Scoring
      -> Supporter/Defender Agent
      -> Critic/Challenger Agent
      -> Judge Agent
  -> Output: Audit Score + Risk Findings + Evidence + Suggested Fix
```

Trong phiên bản hiện tại của codebase, kiến trúc được tổ chức quanh các module chính:

- `main.py`: entry point CLI và hàm chạy hệ thống.
- `app.py`: giao diện demo Gradio.
- `graph/state.py`: định nghĩa trạng thái chung của hệ thống.
- `graph/workflow.py`: workflow LangGraph cho search mode và non-search mode.
- `agents/`: các agent tìm kiếm, bảo vệ, phản biện, đánh giá nguồn và Judge.
- `prompts/templates.py`: prompt template và JSON contract cho từng agent.
- `config/settings.py`: cấu hình model, số vòng tranh luận và thông số tìm kiếm.

## 10. Tiềm năng ứng dụng thực tế

### Sản phẩm có thể ứng dụng trong bối cảnh nào?

VeriAI có thể ứng dụng trong các bối cảnh:

- Kiểm tra câu trả lời AI trong học tập, nghiên cứu và làm báo cáo.
- Kiểm định bài viết, nội dung marketing, nội dung truyền thông trước khi đăng.
- Kiểm tra câu trả lời AI trước khi gửi cho khách hàng trong doanh nghiệp.
- Hỗ trợ giảng viên/người hướng dẫn đánh giá nội dung do sinh viên tạo với sự hỗ trợ của AI.
- Là lớp kiểm định đầu ra cho chatbot nội bộ trong doanh nghiệp.

### Ai có thể là khách hàng/người dùng đầu tiên?

Nhóm người dùng đầu tiên phù hợp:

- Sinh viên, học viên, người tự học thường xuyên dùng AI.
- Content creator và nhóm marketing nhỏ.
- Giảng viên hoặc nhóm đào tạo muốn hướng dẫn người học dùng AI có trách nhiệm.
- Doanh nghiệp nhỏ đang dùng AI để hỗ trợ soạn thảo và trả lời thông tin nhưng chưa có quy trình kiểm định.

### Có thể triển khai trong doanh nghiệp, trường học, cộng đồng hay thị trường nào?

Sản phẩm có thể triển khai trong:

- Trường đại học, trung tâm đào tạo, lớp học AI literacy.
- Nhóm content/marketing trong doanh nghiệp nhỏ và vừa.
- Bộ phận chăm sóc khách hàng sử dụng chatbot hỗ trợ.
- Cộng đồng người dùng AI cần công cụ kiểm tra nhanh độ tin cậy của nội dung.

### Điều kiện cần để sản phẩm được triển khai thật là gì?

Để triển khai thật, sản phẩm cần:

- Giao diện nhập liệu và đọc kết quả rõ ràng hơn cho người dùng không kỹ thuật.
- Bộ tiêu chí đánh giá ổn định cho từng use case: học tập, content, doanh nghiệp, factual checking.
- Đo lường thực nghiệm trên tập test cụ thể để biết hệ thống phát hiện lỗi tốt đến đâu.
- Cơ chế giới hạn chi phí API và thời gian xử lý.
- Tùy chọn lưu lịch sử audit, nguồn tham khảo và phiên bản câu trả lời đã sửa.
- Chính sách bảo mật dữ liệu nếu xử lý nội dung doanh nghiệp hoặc tài liệu nhạy cảm.

## 11. Tiềm năng mở rộng / thương mại hóa

### Sản phẩm có thể mở rộng cho nhóm người dùng nào?

Sau MVP, VeriAI có thể mở rộng cho:

- Cá nhân dùng AI hằng ngày.
- Sinh viên và giảng viên.
- Nhóm truyền thông/content.
- Doanh nghiệp triển khai chatbot nội bộ.
- Nền tảng học tập hoặc công cụ productivity muốn tích hợp lớp kiểm định AI.
- Các đội AI governance/compliance cần giám sát chất lượng đầu ra AI.

### Có thể thu phí theo mô hình nào?

Các mô hình thương mại hóa tiềm năng:

- **SaaS:** nền tảng web cho người dùng kiểm tra đầu ra AI.
- **Subscription:** gói cá nhân/tháng với số lượt audit nhất định.
- **Pay-per-use:** tính phí theo số lượt kiểm định hoặc số token xử lý.
- **B2B license:** cấp phép cho doanh nghiệp/trường học dùng nội bộ.
- **Internal tool:** triển khai riêng trong tổ chức để kiểm định chatbot hoặc tài liệu nội bộ.
- **API integration:** cung cấp API để các chatbot khác gọi VeriAI như một lớp review trước khi trả kết quả cho người dùng cuối.

### Lợi thế cạnh tranh nếu tiếp tục phát triển là gì?

Lợi thế cạnh tranh của VeriAI nằm ở:

- Cơ chế phản biện đa tác tử có khả năng truy vết, không chỉ đưa ra một điểm số đơn giản.
- Có thể tận dụng cả bằng chứng bên ngoài và context do người dùng cung cấp.
- Có khả năng mở rộng sang nhiều bối cảnh: học tập, nội dung, doanh nghiệp, fact-checking.
- Có nền tảng kỹ thuật sẵn từ hệ thống Multi-Agent Debate cho kiểm chứng tin giả.
- Tập trung vào vai trò “AI kiểm định AI”, một nhu cầu ngày càng quan trọng khi AI tạo sinh được sử dụng rộng rãi.

## 12. Rủi ro & điểm cần cải thiện

### 1. Rủi ro kỹ thuật

- Hệ thống vẫn phụ thuộc vào chất lượng của LLM nền. Nếu LLM đánh giá sai, hallucinate hoặc không tuân thủ JSON format, kết quả audit có thể bị ảnh hưởng.
- Tìm kiếm bằng chứng bên ngoài có thể thiếu nguồn, nguồn không đủ tin cậy hoặc không phù hợp với ngữ cảnh.
- Multi-agent workflow tốn nhiều lượt gọi API hơn chatbot thông thường, dẫn đến chi phí và thời gian xử lý cao hơn.
- Việc đánh giá factual correctness, logic và completeness là bài toán khó, cần benchmark rõ ràng để đo hiệu quả.

### 2. Rủi ro sản phẩm/người dùng

- Người dùng có thể hiểu nhầm điểm tin cậy là kết luận tuyệt đối, trong khi sản phẩm chỉ nên đóng vai trò hỗ trợ kiểm định.
- Nếu giao diện trả về quá nhiều thông tin, người dùng phổ thông có thể khó hiểu hoặc không biết cần hành động gì tiếp theo.
- Một số nhóm người dùng có thể chưa sẵn sàng trả phí cho việc kiểm tra đầu ra AI nếu chưa thấy rõ rủi ro từ hallucination.
- Trong môi trường học tập, cần định vị sản phẩm là công cụ hỗ trợ dùng AI có trách nhiệm, không phải công cụ làm bài thay người học.

### 3. Điểm cần hỗ trợ thêm

- Cần user test với nhóm người dùng thật để xác định output nào hữu ích nhất: điểm số, cảnh báo lỗi, nguồn tham khảo hay bản sửa.
- Cần bộ dữ liệu test riêng cho use case “đánh giá câu trả lời AI khác”, không chỉ benchmark fake news.
- Cần cải thiện UI/UX để thể hiện rõ các phần: điểm tin cậy, lỗi nghiêm trọng, bằng chứng và gợi ý sửa.
- Cần tối ưu chi phí bằng cách giảm số vòng tranh luận, chọn model phù hợp từng vai trò hoặc cache kết quả tìm kiếm.
- Cần bổ sung cơ chế bảo mật và quyền riêng tư nếu triển khai cho doanh nghiệp hoặc tài liệu nhạy cảm.

## Gợi ý hướng phát triển MVP tiếp theo

Để chuyển từ prototype kiểm chứng tin giả sang sản phẩm VeriAI, nhóm nên ưu tiên các bước sau:

1. Đổi input chính của demo từ “news/claim” sang “câu hỏi gốc + câu trả lời AI cần kiểm định”.
2. Thêm output dạng audit report gồm: audit score, verdict, top issues, evidence, suggested revision.
3. Chuẩn bị 3–5 demo case có lỗi AI rõ ràng để trình bày.
4. Chạy user test nhỏ với sinh viên hoặc người dùng AI thường xuyên.
5. Đo các chỉ số cơ bản: thời gian xử lý, số lỗi phát hiện được, mức độ hữu ích theo phản hồi người dùng.
