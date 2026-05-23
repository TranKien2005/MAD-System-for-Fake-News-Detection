> **Lưu ý trạng thái tài liệu:** Tài liệu này là bản thiết kế/ghi chú kỹ thuật cũ và có một số phần không còn khớp hoàn toàn với workflow hiện tại trong code. Để xem hướng dẫn chạy, biến môi trường, cấu trúc hệ thống đang dùng và các lưu ý mới nhất, ưu tiên đọc `README.md`. Một số khái niệm như Claim Parser Agent, Evaluator chạy sau mỗi vòng hoặc cấu hình nhiều model có thể là định hướng thiết kế thay vì thành phần đang được nối trực tiếp trong workflow hiện tại.
# MAD System for Fake News Detection

## Multi-Agent Debate System â€” Thiáº¿t Káº¿ Chi Tiáº¿t (v2)

> Há»‡ thá»‘ng sá»­ dá»¥ng nhiá»u agent LLM tranh luáº­n vá»›i nhau Ä‘á»ƒ Ä‘Ã¡nh giÃ¡ Ä‘á»™ tin cáº­y cá»§a má»™t tin tá»©c,
> láº¥y cáº£m há»©ng tá»« bÃ i bÃ¡o **Tool-MAD** (2026).

---

## 1. Tá»•ng Quan Há»‡ Thá»‘ng

### Má»¥c tiÃªu
XÃ¢y dá»±ng há»‡ thá»‘ng multi-agent debate sá»­ dá»¥ng LangGraph, trong Ä‘Ã³ cÃ¡c agent LLM Ä‘Ã³ng vai trÃ² khÃ¡c nhau Ä‘á»ƒ **tranh luáº­n cÃ³ cáº¥u trÃºc** (theo tá»«ng nháº­n Ä‘á»‹nh) vÃ  **Ä‘Ã¡nh giÃ¡** xem má»™t tin tá»©c cÃ³ pháº£i tin giáº£ hay khÃ´ng, Ä‘Æ°a ra **pháº§n trÄƒm tin cáº­y** kÃ¨m giáº£i thÃ­ch dá»±a trÃªn **cÃ´ng thá»©c tÃ­nh Ä‘iá»ƒm cho tá»«ng nháº­n Ä‘á»‹nh**.

### Kiáº¿n TrÃºc Tá»•ng Quan

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                        USER INPUT                                â”‚
â”‚                   (Äoáº¡n tin tá»©c cáº§n kiá»ƒm tra)                    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                       â”‚
                       â–¼
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â”‚  Claim Parser   â”‚  TrÃ­ch xuáº¥t cÃ¡c claim chÃ­nh
              â”‚     Agent       â”‚  tá»« Ä‘oáº¡n tin tá»©c
              â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                       â”‚
                       â–¼
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â”‚  Knowledge      â”‚  TÃ¬m kiáº¿m trÃªn Wikipedia
              â”‚  Researcher     â”‚  â†’ XÃ¢y dá»±ng Knowledge Base chung
              â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                       â”‚
           â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
           â”‚                       â”‚
           â–¼                       â–¼
   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”      â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
   â”‚   Defender     â”‚      â”‚  Challenger    â”‚    Tranh luáº­n
   â”‚   Agent        â”‚      â”‚  Agent         â”‚    cÃ³ cáº¥u trÃºc
   â”‚ (Tin tháº­t)     â”‚      â”‚ (Tin giáº£)      â”‚    theo nháº­n Ä‘á»‹nh
   â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜      â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚                       â”‚
           â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                       â”‚
                       â–¼
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â”‚   Evaluator     â”‚  ÄÃ¡nh giÃ¡ má»—i vÃ²ng
              â”‚   Agent         â”‚  CONFIRM / REJECT / KEEP claims
              â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                       â”‚
                  (Láº·p láº¡i náº¿u chÆ°a Ä‘á»§ vÃ²ng)
                       â”‚
                       â–¼
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â”‚   Judge Agent   â”‚  TÃ­nh Ä‘iá»ƒm tá»«ng nháº­n Ä‘á»‹nh
              â”‚                 â”‚  credibility Ã— reliability Ã— relevance
              â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                       â”‚
                       â–¼
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â”‚    Káº¾T QUáº¢      â”‚  % tin cáº­y + báº£ng Ä‘iá»ƒm
              â”‚                 â”‚  tá»«ng nháº­n Ä‘á»‹nh
              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## 2. CÃ¡c Agent Chi Tiáº¿t

### 2.1. Claim Parser Agent

| Thuá»™c tÃ­nh | Chi tiáº¿t |
|------------|----------|
| **Vai trÃ²** | TrÃ­ch xuáº¥t cÃ¡c claim (tuyÃªn bá»‘) chÃ­nh tá»« Ä‘oáº¡n tin tá»©c |
| **Input** | Äoáº¡n tin tá»©c gá»‘c tá»« user |
| **Output** | Danh sÃ¡ch claims cáº§n xÃ¡c minh |
| **Tool** | KhÃ´ng |

---

### 2.2. Knowledge Researcher Agent (Má»šI)

| Thuá»™c tÃ­nh | Chi tiáº¿t |
|------------|----------|
| **Vai trÃ²** | TÃ¬m kiáº¿m kiáº¿n thá»©c ná»n táº£ng tá»« Wikipedia trÆ°á»›c khi tranh luáº­n |
| **Input** | Claims Ä‘Ã£ trÃ­ch xuáº¥t |
| **Output** | Knowledge Base chung (danh sÃ¡ch káº¿t quáº£ Wikipedia) |
| **Tool** | Wikipedia API (thÆ° viá»‡n `wikipedia`) |

**Quy trÃ¬nh:**
1. DÃ¹ng LLM Ä‘á»ƒ táº¡o 3-6 search queries tá»« claims
2. TÃ¬m kiáº¿m trÃªn Wikipedia (tiáº¿ng Viá»‡t + tiáº¿ng Anh)
3. LÆ°u káº¿t quáº£ vÃ o `knowledge_base` â€” nguá»“n kiáº¿n thá»©c chung cho Cáº¢ HAI bÃªn

**Táº¡i sao cáº§n?**
- Cung cáº¥p kiáº¿n thá»©c thá»±c táº¿ cho agents thay vÃ¬ dá»±a vÃ o hallucination cá»§a LLM
- Äáº£m báº£o cáº£ hai bÃªn cÃ³ cÃ¹ng má»™t nguá»“n thÃ´ng tin khÃ¡ch quan
- Giá»›i háº¡n agents chá»‰ dÃ¹ng thÃ´ng tin Ä‘Ã£ xÃ¡c minh hoáº·c kiáº¿n thá»©c Cá»°C Ká»² phá»• thÃ´ng

---

### 2.3. Defender Agent (Báº£o Vá»‡ Tin Tháº­t)

| Thuá»™c tÃ­nh | Chi tiáº¿t |
|------------|----------|
| **Vai trÃ²** | Láº­p luáº­n ráº±ng tin tá»©c lÃ  **THáº¬T** |
| **Input** | Claims + Knowledge Base + Lá»‹ch sá»­ tranh luáº­n |
| **Output** | Nháº­n Ä‘á»‹nh cÃ³ cáº¥u trÃºc [D1], [D2]... |
| **Tool** | KhÃ´ng |

### 2.4. Challenger Agent (Báº£o Vá»‡ Tin Giáº£)

| Thuá»™c tÃ­nh | Chi tiáº¿t |
|------------|----------|
| **Vai trÃ²** | Láº­p luáº­n ráº±ng tin tá»©c lÃ  **GIáº¢** |
| **Input** | Claims + Knowledge Base + Lá»‹ch sá»­ tranh luáº­n |
| **Output** | Nháº­n Ä‘á»‹nh cÃ³ cáº¥u trÃºc [C1], [C2]... |
| **Tool** | KhÃ´ng |

#### Cáº¥u trÃºc tranh luáº­n theo vÃ²ng

**VÃ²ng 1 â€” NÃªu nháº­n Ä‘á»‹nh ban Ä‘áº§u:**
- Má»—i agent Äá»˜C Láº¬P Ä‘Æ°a ra 3-5 nháº­n Ä‘á»‹nh
- Format: `[D1] (Nguá»“n: Wikipedia | Credibility: 0.65) Ná»™i dung...`
- Chá»‰ Ä‘Æ°á»£c dÃ¹ng: Knowledge Base + kiáº¿n thá»©c Cá»°C Ká»² phá»• thÃ´ng + logic
- Hai bÃªn KHÃ”NG tháº¥y nháº­n Ä‘á»‹nh cá»§a nhau

**VÃ²ng 2 â€” Pháº£n biá»‡n:**
- Má»—i agent pháº£n biá»‡n nháº­n Ä‘á»‹nh Cá»¤ THá»‚ cá»§a Ä‘á»‘i phÆ°Æ¡ng
- Pháº£i chá»‰ rÃµ: `### Pháº£n biá»‡n [C1]: "ná»™i dung nháº­n Ä‘á»‹nh"`
- Má»—i nháº­n Ä‘á»‹nh tranh luáº­n trong má»™t BLOCK riÃªng

**VÃ²ng 3+ â€” Báº£o vá»‡ + Pháº£n biá»‡n tiáº¿p:**
- Agent Báº¢O Vá»† nháº­n Ä‘á»‹nh bá»‹ pháº£n biá»‡n á»Ÿ vÃ²ng trÆ°á»›c
- Agent cÃ³ thá»ƒ TIáº¾P Tá»¤C pháº£n biá»‡n nháº­n Ä‘á»‹nh Ä‘á»‘i phÆ°Æ¡ng
- Chá»‰ pháº£n há»“i ná»™i dung VÃ’NG TRÆ¯á»šC (khÃ´ng pháº£n há»“i trong cÃ¹ng vÃ²ng)
- Chá»‰ tranh luáº­n nháº­n Ä‘á»‹nh cÃ²n ACTIVE (chÆ°a bá»‹ Evaluator káº¿t luáº­n)
- Táº¥t cáº£ tá»• chá»©c theo BLOCK tá»«ng nháº­n Ä‘á»‹nh

---

### 2.5. Evaluator Agent (thay tháº¿ Moderator cÅ©)

| Thuá»™c tÃ­nh | Chi tiáº¿t |
|------------|----------|
| **Vai trÃ²** | ÄÃ¡nh giÃ¡ vÃ  phÃ¡n quyáº¿t tá»«ng nháº­n Ä‘á»‹nh sau má»—i vÃ²ng |
| **Input** | Lá»‹ch sá»­ tranh luáº­n + Knowledge Base + Evaluator rulings trÆ°á»›c |
| **Output** | Danh sÃ¡ch quyáº¿t Ä‘á»‹nh: CONFIRM / REJECT / KEEP cho má»—i nháº­n Ä‘á»‹nh |
| **Tool** | KhÃ´ng |

**Quyá»n háº¡n:**
1. **CONFIRM** â€” XÃ¡c nháº­n nháº­n Ä‘á»‹nh Ä‘Ãºng â†’ Cháº¥m dá»©t tranh luáº­n vá» nháº­n Ä‘á»‹nh Ä‘Ã³
2. **REJECT** â€” BÃ¡c bá» nháº­n Ä‘á»‹nh náº¿u:
   - KhÃ´ng cÃ³ báº±ng chá»©ng (khÃ´ng trong Knowledge Base)
   - KhÃ´ng pháº£i kiáº¿n thá»©c cá»±c ká»³ phá»• thÃ´ng mÃ  tá»± xÆ°ng lÃ  phá»• thÃ´ng
   - KhÃ´ng liÃªn quan Ä‘áº¿n váº¥n Ä‘á» Ä‘ang tranh luáº­n
   - Agent khÃ´ng báº£o vá»‡ Ä‘Æ°á»£c trÆ°á»›c pháº£n biá»‡n há»£p lÃ½
3. **KEEP** â€” Giá»¯ nguyÃªn Ä‘á»ƒ tiáº¿p tá»¥c tranh luáº­n

---

### 2.6. Judge Agent (PhÃ¡n Quyáº¿t Cuá»‘i CÃ¹ng)

| Thuá»™c tÃ­nh | Chi tiáº¿t |
|------------|----------|
| **Vai trÃ²** | TÃ­nh Ä‘iá»ƒm tá»«ng nháº­n Ä‘á»‹nh vÃ  Ä‘Æ°a ra phÃ¡n quyáº¿t tá»•ng thá»ƒ |
| **Input** | ToÃ n bá»™ lá»‹ch sá»­ + Evaluator rulings + Knowledge Base |
| **Output** | Báº£ng Ä‘iá»ƒm tá»«ng nháº­n Ä‘á»‹nh + Verdict + Confidence |
| **Tool** | KhÃ´ng |

#### CÃ´ng thá»©c tÃ­nh Ä‘iá»ƒm

Má»—i nháº­n Ä‘á»‹nh Ä‘Æ°á»£c tÃ­nh:
```
score(claim) = source_credibility Ã— reliability Ã— relevance
```

| Yáº¿u tá»‘ | GiÃ¡ trá»‹ | MÃ´ táº£ |
|---------|---------|-------|
| **source_credibility** | 1.0 | Kiáº¿n thá»©c phá»• thÃ´ng |
| | 0.65 | Wikipedia |
| | 0.5 | Logic thuáº§n |
| | 0.2 | KhÃ´ng xÃ¡c minh |
| **reliability** | 1.0 | ÄÃ£ CONFIRM hoáº·c kiáº¿n thá»©c phá»• thÃ´ng |
| | 0.6-0.8 | Äang tranh luáº­n, cÃ³ há»— trá»£ tá»‘t |
| | 0.1-0.3 | Bá»‹ pháº£n bÃ¡c máº¡nh |
| | 0.0 | Bá»‹ REJECT |
| **relevance** | 0.0-1.0 | Má»©c Ä‘á»™ liÃªn quan vÃ  giÃ¡ trá»‹ Ä‘á»‘i vá»›i váº¥n Ä‘á» |

**Tá»•ng Ä‘iá»ƒm má»—i bÃªn:**
```
total_score(side) = Î£ score(claim_i)  for all claims of that side
```

So sÃ¡nh `total_score(DEFENDER)` vs `total_score(CHALLENGER)` Ä‘á»ƒ Ä‘Æ°a ra verdict.

---

## 3. Flow Chi Tiáº¿t

### VÃ²ng 0: Khá»Ÿi Táº¡o

```
User nháº­p tin tá»©c
    â”‚
    â–¼
Claim Parser trÃ­ch xuáº¥t claims
    â”‚
    â–¼
Knowledge Researcher tÃ¬m kiáº¿m Wikipedia
    â”‚ (táº¡o queries â†’ search vi + en â†’ lÆ°u knowledge_base)
    â”‚
    â–¼
Knowledge Base sáºµn sÃ ng cho tranh luáº­n
```

### VÃ²ng 1: Nháº­n Äá»‹nh Ban Äáº§u

```
Defender nháº­n claims + knowledge_base
    â†’ ÄÆ°a ra nháº­n Ä‘á»‹nh [D1], [D2], [D3]... (Äá»˜C Láº¬P)
    â†’ Má»—i nháº­n Ä‘á»‹nh ghi rÃµ nguá»“n + credibility

Challenger nháº­n claims + knowledge_base (KHÃ”NG tháº¥y Defender)
    â†’ ÄÆ°a ra nháº­n Ä‘á»‹nh [C1], [C2], [C3]...
    â†’ Má»—i nháº­n Ä‘á»‹nh ghi rÃµ nguá»“n + credibility

Evaluator Ä‘Ã¡nh giÃ¡:
    â†’ BÃ¡c bá» nháº­n Ä‘á»‹nh khÃ´ng cÃ³ cÆ¡ sá»Ÿ
    â†’ XÃ¡c nháº­n nháº­n Ä‘á»‹nh hiá»ƒn nhiÃªn
    â†’ Giá»¯ nháº­n Ä‘á»‹nh cáº§n tranh luáº­n thÃªm
```

### VÃ²ng 2: Pháº£n Biá»‡n

```
Defender Äá»ŒC láº­p luáº­n Challenger VÃ²ng 1 (tá»« debate_history)
    â†’ Pháº£n biá»‡n tá»«ng nháº­n Ä‘á»‹nh [C?] trong block riÃªng
    â†’ Báº£o vá»‡ [D?] náº¿u cáº§n

Challenger Äá»ŒC láº­p luáº­n Defender VÃ²ng 1 (tá»« debate_history)
    â†’ Pháº£n biá»‡n tá»«ng nháº­n Ä‘á»‹nh [D?] trong block riÃªng
    â†’ Báº£o vá»‡ [C?] náº¿u cáº§n

(Cáº£ hai chá»‰ Ä‘á»c VÃ’NG TRÆ¯á»šC, khÃ´ng Ä‘á»c láº«n nhau trong vÃ²ng hiá»‡n táº¡i)

Evaluator Ä‘Ã¡nh giÃ¡:
    â†’ CONFIRM/REJECT/KEEP cÃ¡c nháº­n Ä‘á»‹nh dá»±a trÃªn pháº£n biá»‡n
```

### VÃ²ng 3+: Báº£o Vá»‡ + Pháº£n Biá»‡n Tiáº¿p

```
TÆ°Æ¡ng tá»± VÃ²ng 2 nhÆ°ng:
- CHá»ˆ tranh luáº­n nháº­n Ä‘á»‹nh ACTIVE
- CÃ³ thá»ƒ báº£o vá»‡ nháº­n Ä‘á»‹nh bá»‹ pháº£n biá»‡n
- CÃ“ THá»‚ tiáº¿p tá»¥c pháº£n biá»‡n nháº­n Ä‘á»‹nh Ä‘á»‘i phÆ°Æ¡ng
- Má»—i nháº­n Ä‘á»‹nh má»™t block riÃªng
```

### VÃ²ng Cuá»‘i: Judge PhÃ¡n Quyáº¿t

```
Judge nháº­n TOÃ€N Bá»˜:
    â”œâ”€â”€ Claims gá»‘c
    â”œâ”€â”€ Knowledge Base
    â”œâ”€â”€ Táº¥t cáº£ debate history
    â””â”€â”€ Táº¥t cáº£ evaluator rulings
    â”‚
    â–¼
TÃ­nh Ä‘iá»ƒm: score = credibility Ã— reliability Ã— relevance
    â”‚
    â–¼
Total Defender vs Total Challenger â†’ Verdict
```

---

## 4. Stack CÃ´ng Nghá»‡

| Component | CÃ´ng nghá»‡ | Ghi chÃº |
|-----------|-----------|---------|
| **Orchestration** | LangGraph | State machine quáº£n lÃ½ debate flow |
| **LLM API** | Groq (Llama 3.3 70B) | Model chÃ­nh cho agents |
| **Web Search** | Wikipedia API | ThÆ° viá»‡n `wikipedia` Python, há»— trá»£ Ä‘a ngÃ´n ngá»¯ |
| **Source Whitelist** | Config file (Python) | Danh sÃ¡ch nguá»“n + credibility tier |
| **Frontend** | Gradio | Demo UI vá»›i streaming |
| **Language** | Python | â€” |

---

## 5. LangGraph State & Graph

### State Definition

```python
class MADState(TypedDict):
    original_news: str
    claims: list[str]
    knowledge_base: Annotated[list[KnowledgeEntry], add_to_list]
    search_results: Annotated[list[dict], add_to_list]
    pending_search_queries: list[str]
    current_round: int
    max_rounds: int
    debate_history: Annotated[list[DebateRound], add_to_list]
    current_defender_argument: str
    current_challenger_argument: str
    evaluator_rulings: Annotated[list[dict], add_to_list]
    verdict: dict | None
```

### Graph Flow

```mermaid
graph TD
    START([Start]) --> PARSE[Claim Parser]
    PARSE --> RESEARCH[Knowledge Researcher<br/>Wikipedia Search]
    RESEARCH --> DEF[Defender<br/>NÃªu nháº­n Ä‘á»‹nh / Pháº£n biá»‡n / Báº£o vá»‡]
    DEF --> CHAL[Challenger<br/>NÃªu nháº­n Ä‘á»‹nh / Pháº£n biá»‡n / Báº£o vá»‡]
    CHAL --> SAVE[Save Round]
    SAVE --> EVAL[Evaluator<br/>CONFIRM / REJECT / KEEP]
    EVAL --> CHECK{Äáº¡t max<br/>rounds?}
    CHECK -->|ChÆ°a| DEF
    CHECK -->|Rá»“i| JUDGE[Judge<br/>TÃ­nh Ä‘iá»ƒm & PhÃ¡n quyáº¿t]
    JUDGE --> END([Káº¿t quáº£])
```

---

## 6. VÃ­ Dá»¥ Minh Há»a

### Input
> "Theo nghiÃªn cá»©u cá»§a Äáº¡i há»c Harvard nÄƒm 2024, uá»‘ng 3 ly cÃ  phÃª má»—i ngÃ y
> giÃºp giáº£m 50% nguy cÆ¡ ung thÆ° gan."

### Knowledge Researcher
Wikipedia search: "Harvard University", "CÃ  phÃª", "Ung thÆ° gan", "Caffeine health effects"

### VÃ²ng 1

**Defender:**
```
[D1] (Nguá»“n: Wikipedia | Credibility: 0.65) Harvard thá»±c sá»± lÃ  trÆ°á»ng Ä‘áº¡i há»c nghiÃªn cá»©u hÃ ng Ä‘áº§u...
[D2] (Nguá»“n: Wikipedia | Credibility: 0.65) CÃ  phÃª cÃ³ chá»©a cÃ¡c cháº¥t chá»‘ng oxy hÃ³a...
[D3] (Nguá»“n: Kiáº¿n thá»©c phá»• thÃ´ng | Credibility: 1.0) WHO lÃ  tá»• chá»©c y táº¿ quá»‘c táº¿ uy tÃ­n...
```

**Challenger:**
```
[C1] (Nguá»“n: Logic | Credibility: 0.5) Con sá»‘ "giáº£m 50%" ráº¥t cao, cÃ¡c nghiÃªn cá»©u y khoa thÆ°á»ng cho káº¿t quáº£ khiÃªm tá»‘n hÆ¡n
[C2] (Nguá»“n: Wikipedia | Credibility: 0.65) KhÃ´ng tÃ¬m tháº¥y nghiÃªn cá»©u Harvard 2024 cá»¥ thá»ƒ vá» cÃ  phÃª vÃ  ung thÆ° gan
[C3] (Nguá»“n: Logic | Credibility: 0.5) Tin tá»©c khÃ´ng dáº«n nguá»“n cá»¥ thá»ƒ, khÃ´ng cÃ³ DOI hoáº·c link
```

**Evaluator:**
```
âœ… CONFIRM [D3]: WHO lÃ  tá»• chá»©c y táº¿ quá»‘c táº¿ â€” Kiáº¿n thá»©c phá»• thÃ´ng
ðŸ”„ KEEP [D1], [D2], [C1], [C2], [C3] â€” Cáº§n tranh luáº­n thÃªm
```

### VÃ²ng 2

**Defender:**
```
### Pháº£n biá»‡n [C1]: "Con sá»‘ 50% ráº¥t cao..."
CÃ  phÃª Ä‘Ã£ Ä‘Æ°á»£c nhiá»u nghiÃªn cá»©u chá»©ng minh... (theo Wikipedia)

### Pháº£n biá»‡n [C2]: "KhÃ´ng tÃ¬m tháº¥y nghiÃªn cá»©u Harvard..."
Thá»«a nháº­n chÆ°a tÃ¬m Ä‘Æ°á»£c nghiÃªn cá»©u cá»¥ thá»ƒ nhÆ°ng Harvard cÃ³ nhiá»u nghiÃªn cá»©u...
```

**Challenger:**
```
### Pháº£n biá»‡n [D1]: "Harvard lÃ  trÆ°á»ng nghiÃªn cá»©u hÃ ng Ä‘áº§u"
KhÃ´ng ai phá»§ nháº­n Harvard uy tÃ­n, nhÆ°ng Ä‘iá»u Ä‘Ã³ khÃ´ng chá»©ng minh tin tá»©c Ä‘Ãºng

### Pháº£n biá»‡n [D2]: "CÃ  phÃª cÃ³ cháº¥t chá»‘ng oxy hÃ³a"
ÄÃºng nhÆ°ng "cÃ³ cháº¥t chá»‘ng oxy hÃ³a" â‰  "giáº£m 50% ung thÆ° gan"
```

**Evaluator:**
```
âœ… CONFIRM [D1]: Harvard lÃ  trÆ°á»ng uy tÃ­n â€” nhÆ°ng khÃ´ng chá»©ng minh tin Ä‘Ãºng
âŒ REJECT [D2]: KhÃ´ng liÃªn quan trá»±c tiáº¿p â€” "cÃ³ cháº¥t chá»‘ng oxy hÃ³a" â‰  giáº£m 50% ung thÆ°
ðŸ”„ KEEP [C1], [C2], [C3]
```

### Judge Verdict

```json
{
  "claim_scores": [
    {"claim_id": "[C1]", "side": "CHALLENGER", "source_credibility": 0.5,
     "reliability": 0.7, "relevance": 0.9, "score": 0.315},
    {"claim_id": "[C2]", "side": "CHALLENGER", "source_credibility": 0.65,
     "reliability": 0.8, "relevance": 0.95, "score": 0.494},
    {"claim_id": "[C3]", "side": "CHALLENGER", "source_credibility": 0.5,
     "reliability": 0.8, "relevance": 0.8, "score": 0.320}
  ],
  "defender_total": 0.0,
  "challenger_total": 1.129,
  "verdict": "LIKELY_FAKE",
  "confidence": 82
}
```

