from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT = Path(__file__).resolve().parent

try:
    FONT_TITLE = ImageFont.truetype("arialbd.ttf", 30)
    FONT_BOX = ImageFont.truetype("arialbd.ttf", 20)
    FONT = ImageFont.truetype("arial.ttf", 17)
    FONT_SMALL = ImageFont.truetype("arial.ttf", 14)
except Exception:
    FONT_TITLE = FONT_BOX = FONT = FONT_SMALL = ImageFont.load_default()

BG = "#ffffff"
BLUE = "#DCEBFF"
BLUE_BORDER = "#2F5E9E"
GREEN = "#E4F6E7"
GREEN_BORDER = "#3E8C4A"
ORANGE = "#FFF1D8"
ORANGE_BORDER = "#B87516"
PURPLE = "#EFE5FF"
PURPLE_BORDER = "#7150A8"
RED = "#FFE0E0"
RED_BORDER = "#B24848"
GRAY = "#F2F2F2"
GRAY_BORDER = "#777777"
TEXT = "#1F1F1F"


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def rounded_box(draw, xy, title, body="", fill=BLUE, outline=BLUE_BORDER, width=3):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=18, fill=fill, outline=outline, width=width)
    if title:
        draw.text((x1 + 16, y1 + 12), title, fill=TEXT, font=FONT_BOX)
    if body:
        y = y1 + 42
        for line in wrap_text(draw, body, FONT_SMALL, x2 - x1 - 28):
            draw.text((x1 + 16, y), line, fill=TEXT, font=FONT_SMALL)
            y += 18


def arrow(draw, start, end, color="#333333", width=3):
    draw.line([start, end], fill=color, width=width)
    x1, y1 = start
    x2, y2 = end
    import math
    ang = math.atan2(y2-y1, x2-x1)
    L = 13
    A = 0.45
    p1 = (x2 - L*math.cos(ang-A), y2 - L*math.sin(ang-A))
    p2 = (x2 - L*math.cos(ang+A), y2 - L*math.sin(ang+A))
    draw.polygon([end, p1, p2], fill=color)


def title(draw, text, w):
    bbox = draw.textbbox((0, 0), text, font=FONT_TITLE)
    draw.text(((w - (bbox[2]-bbox[0]))/2, 20), text, fill=TEXT, font=FONT_TITLE)


def save(img, name):
    img.save(OUT / name, "PNG")


def overview():
    w, h = 1500, 820
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    title(d, "Khung tổng quan hệ thống phát hiện tin giả dựa trên MAD", w)
    boxes = {
        "input": (60, 140, 280, 250),
        "state": (370, 110, 650, 280),
        "search": (760, 90, 1050, 210),
        "kb": (1130, 90, 1430, 210),
        "debate": (760, 300, 1050, 500),
        "judge": (1130, 330, 1430, 470),
        "out": (1130, 570, 1430, 720),
    }
    rounded_box(d, boxes["input"], "Đầu vào", "original_news; initial_context nếu có", BLUE, BLUE_BORDER)
    rounded_box(d, boxes["state"], "MADState", "Bộ nhớ làm việc chung: knowledge_base, source_scores, debate_history, claims_registry, verdict", GRAY, GRAY_BORDER)
    rounded_box(d, boxes["search"], "Truy xuất bằng chứng", "plan_round_queries; Tavily trước, Wikipedia fallback; lọc relevance > 0.8", GREEN, GREEN_BORDER)
    rounded_box(d, boxes["kb"], "Knowledge Base", "Nguồn [S1], [S2]... kèm title, content, domain, relevance và trust score", GREEN, GREEN_BORDER)
    rounded_box(d, boxes["debate"], "Multi-Agent Debate", "Defender tạo D*; Challenger tạo C*; REBUT/DEFEND theo claims_registry qua nhiều vòng", ORANGE, ORANGE_BORDER)
    rounded_box(d, boxes["judge"], "Judge", "Tổng hợp evidence, source_scores và debate_history để sinh verdict", PURPLE, PURPLE_BORDER)
    rounded_box(d, boxes["out"], "Đầu ra", "truth_score, reasoning, điểm quyết định, lịch sử tranh luận và nguồn bằng chứng", BLUE, BLUE_BORDER)
    arrow(d, (280,195), (370,195))
    arrow(d, (650,170), (760,150))
    arrow(d, (1050,150), (1130,150))
    arrow(d, (650,235), (760,385))
    arrow(d, (1050,395), (1130,395))
    arrow(d, (1280,470), (1280,570))
    arrow(d, (1280,210), (910,300), GREEN_BORDER)
    arrow(d, (910,500), (510,280), ORANGE_BORDER)
    d.text((790, 520), "save_round cập nhật debate_history và current_round", fill=TEXT, font=FONT_SMALL)
    save(img, "mad_system_overview.png")


def search_workflow():
    w, h = 1600, 900
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    title(d, "Workflow chế độ tìm kiếm trong graph/workflow.py", w)
    y = 140
    xs = [70, 300, 560, 820, 1080, 1330]
    rounded_box(d, (xs[0], y, xs[0]+180, y+100), "prepare_round", "Lập query cho Defender và Challenger", BLUE, BLUE_BORDER)
    rounded_box(d, (xs[1], y-75, xs[1]+190, y+25), "search_defender", "Tìm evidence cho DEFENDER", GREEN, GREEN_BORDER)
    rounded_box(d, (xs[1], y+75, xs[1]+190, y+175), "search_round", "Tìm evidence cho CHALLENGER", GREEN, GREEN_BORDER)
    rounded_box(d, (xs[2], y, xs[2]+190, y+100), "score_sources", "Chấm trust_score cho nguồn mới", GREEN, GREEN_BORDER)
    rounded_box(d, (xs[3], y, xs[3]+170, y+100), "defender", "Sinh lập luận bảo vệ; tạo/cập nhật D*", ORANGE, ORANGE_BORDER)
    rounded_box(d, (xs[4], y, xs[4]+190, y+100), "challenger", "Phản biện; tạo/cập nhật C*", RED, RED_BORDER)
    rounded_box(d, (xs[5], y, xs[5]+170, y+100), "save_round", "Lưu debate_history; tăng current_round; GC nguồn", GRAY, GRAY_BORDER)
    rounded_box(d, (650, 520, 900, 640), "should_continue_debate", "Nếu current_round <= max_rounds thì tiếp tục; ngược lại chuyển Judge", PURPLE, PURPLE_BORDER)
    rounded_box(d, (1020, 520, 1190, 640), "judge", "Sinh verdict cuối", PURPLE, PURPLE_BORDER)
    rounded_box(d, (1300, 520, 1480, 640), "END", "Kết thúc workflow", BLUE, BLUE_BORDER)
    arrow(d, (250, y+50), (300, y-25))
    arrow(d, (250, y+50), (300, y+125))
    arrow(d, (490, y-25), (560, y+45))
    arrow(d, (490, y+125), (560, y+55))
    arrow(d, (750, y+50), (820, y+50))
    arrow(d, (990, y+50), (1080, y+50))
    arrow(d, (1270, y+50), (1330, y+50))
    arrow(d, (1415, y+100), (780, 520))
    arrow(d, (650, 580), (160, y+100), PURPLE_BORDER)
    d.text((265, 455), "continue", fill=PURPLE_BORDER, font=FONT)
    arrow(d, (900, 580), (1020, 580), PURPLE_BORDER)
    d.text((925, 550), "judge", fill=PURPLE_BORDER, font=FONT)
    arrow(d, (1190, 580), (1300, 580))
    rounded_box(d, (120, 720, 1480, 820), "Dữ liệu trạng thái xuyên suốt", "knowledge_base, source_scores, pending_search_requests, executed_queries, current_round, debate_history, claims_registry, verdict", GRAY, GRAY_BORDER)
    save(img, "search_workflow.png")


def non_search_workflow():
    w, h = 1400, 760
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    title(d, "Workflow chế độ không tìm kiếm cho FEVER/non_search", w)
    y = 170
    boxes = [
        ((70, y, 260, y+110), "prepare", "Vòng 1 nạp initial_context thành [S1]; trust=1.0", BLUE, BLUE_BORDER),
        ((340, y, 530, y+110), "defender", "Lập luận từ [S1] và history; tạo/cập nhật D*", ORANGE, ORANGE_BORDER),
        ((610, y, 800, y+110), "challenger", "Phản biện từ [S1] và history; tạo/cập nhật C*", RED, RED_BORDER),
        ((880, y, 1070, y+110), "save_round", "Lưu round; tăng current_round", GRAY, GRAY_BORDER),
        ((500, 460, 760, 590), "should_continue_debate", "continue quay lại defender; judge khi hết max_rounds", PURPLE, PURPLE_BORDER),
        ((860, 460, 1030, 590), "judge", "Tổng hợp verdict", PURPLE, PURPLE_BORDER),
        ((1130, 460, 1290, 590), "END", "Kết thúc", BLUE, BLUE_BORDER),
    ]
    for b in boxes:
        rounded_box(d, *b)
    arrow(d, (260, y+55), (340, y+55))
    arrow(d, (530, y+55), (610, y+55))
    arrow(d, (800, y+55), (880, y+55))
    arrow(d, (975, y+110), (630, 460))
    arrow(d, (500, 525), (430, y+110), PURPLE_BORDER)
    d.text((345, 420), "continue", fill=PURPLE_BORDER, font=FONT)
    arrow(d, (760, 525), (860, 525), PURPLE_BORDER)
    d.text((785, 495), "judge", fill=PURPLE_BORDER, font=FONT)
    arrow(d, (1030, 525), (1130, 525))
    rounded_box(d, (100, 650, 1300, 720), "Điểm khác biệt", "Không gọi Tavily/Wikipedia trong lúc đánh giá; toàn bộ lập luận bị giới hạn trong evidence/context đã cung cấp.", GREEN, GREEN_BORDER)
    save(img, "non_search_workflow.png")


def state_claims():
    w, h = 1500, 860
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    title(d, "MADState và Claims Registry trong tranh luận nhiều vòng", w)
    rounded_box(d, (80, 120, 420, 250), "Input", "original_news; initial_context; debate_mode; max_rounds", BLUE, BLUE_BORDER)
    rounded_box(d, (80, 310, 420, 460), "Knowledge", "knowledge_base [S*]; source_scores; executed_queries; round_search_results", GREEN, GREEN_BORDER)
    rounded_box(d, (80, 520, 420, 700), "Output", "verdict gồm truth_score và reasoning; debate_history phục vụ giải thích", PURPLE, PURPLE_BORDER)
    rounded_box(d, (560, 110, 940, 250), "Defender claims", "ASSERT tạo D1, D2...; DEFEND/REBUT cập nhật thread theo target_id", ORANGE, ORANGE_BORDER)
    rounded_box(d, (560, 320, 940, 460), "Challenger claims", "ASSERT tạo C1, C2...; REBUT/DEFEND nhắm vào D* hoặc C*", RED, RED_BORDER)
    rounded_box(d, (1080, 190, 1410, 390), "claims_registry", "Dict lưu lịch sử từng claim. Mỗi entry có round, side, action_type, text, evidence, target_claim_ids", GRAY, GRAY_BORDER)
    rounded_box(d, (1080, 520, 1410, 700), "debate_history", "Mỗi vòng lưu defender_argument, challenger_argument, defender_claims, challenger_claims", GRAY, GRAY_BORDER)
    arrow(d, (420, 185), (560, 180))
    arrow(d, (420, 385), (560, 390))
    arrow(d, (940, 180), (1080, 250), ORANGE_BORDER)
    arrow(d, (940, 390), (1080, 320), RED_BORDER)
    arrow(d, (1245, 390), (1245, 520), GRAY_BORDER)
    arrow(d, (1080, 610), (420, 610), GRAY_BORDER)
    d.text((565, 610), "save_round", fill=TEXT, font=FONT)
    save(img, "mad_state_claims_registry.png")


overview()
search_workflow()
non_search_workflow()
state_claims()
