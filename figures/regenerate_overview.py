from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

OUT = Path(__file__).resolve().parent
try:
    FONT_TITLE = ImageFont.truetype("arialbd.ttf", 30)
    FONT_BOX = ImageFont.truetype("arialbd.ttf", 20)
    FONT = ImageFont.truetype("arial.ttf", 17)
    FONT_SMALL = ImageFont.truetype("arial.ttf", 14)
except Exception:
    FONT_TITLE = FONT_BOX = FONT = FONT_SMALL = ImageFont.load_default()

BG = "#ffffff"; TEXT = "#1F1F1F"
BLUE = "#DCEBFF"; BLUE_BORDER = "#2F5E9E"
GREEN = "#E4F6E7"; GREEN_BORDER = "#3E8C4A"
ORANGE = "#FFF1D8"; ORANGE_BORDER = "#B87516"
PURPLE = "#EFE5FF"; PURPLE_BORDER = "#7150A8"
GRAY = "#F2F2F2"; GRAY_BORDER = "#777777"


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
        y = y1 + 44
        for line in wrap_text(draw, body, FONT_SMALL, x2 - x1 - 30):
            draw.text((x1 + 16, y), line, fill=TEXT, font=FONT_SMALL)
            y += 18


def arrow_head(draw, start, end, color="#333333"):
    x1, y1 = start; x2, y2 = end
    ang = math.atan2(y2-y1, x2-x1)
    L = 13; A = 0.45
    p1 = (x2 - L*math.cos(ang-A), y2 - L*math.sin(ang-A))
    p2 = (x2 - L*math.cos(ang+A), y2 - L*math.sin(ang+A))
    draw.polygon([end, p1, p2], fill=color)


def arrow(draw, start, end, color="#333333", width=3):
    draw.line([start, end], fill=color, width=width)
    arrow_head(draw, start, end, color)


def poly_arrow(draw, points, color="#333333", width=3):
    for a, b in zip(points, points[1:]):
        draw.line([a, b], fill=color, width=width)
    arrow_head(draw, points[-2], points[-1], color)


def title(draw, text, w):
    bbox = draw.textbbox((0, 0), text, font=FONT_TITLE)
    draw.text(((w - (bbox[2]-bbox[0]))/2, 20), text, fill=TEXT, font=FONT_TITLE)

w, h = 1500, 900
img = Image.new("RGB", (w, h), BG)
d = ImageDraw.Draw(img)
title(d, "Khung tổng quan hệ thống phát hiện tin giả dựa trên MAD", w)

boxes = {
    "input": (60, 150, 280, 260),
    "state": (380, 120, 660, 300),
    "search": (780, 95, 1060, 220),
    "kb": (1150, 95, 1440, 220),
    "debate": (780, 330, 1060, 540),
    "judge": (1150, 350, 1440, 500),
    "out": (1150, 620, 1440, 760),
}
rounded_box(d, boxes["input"], "Đầu vào", "original_news; initial_context nếu có", BLUE, BLUE_BORDER)
rounded_box(d, boxes["state"], "MADState", "Bộ nhớ làm việc chung: knowledge_base, source_scores, debate_history, claims_registry, verdict", GRAY, GRAY_BORDER)
rounded_box(d, boxes["search"], "Truy xuất bằng chứng", "plan_round_queries; Tavily trước, Wikipedia fallback; lọc relevance > 0.8", GREEN, GREEN_BORDER)
rounded_box(d, boxes["kb"], "Knowledge Base", "Nguồn [S1], [S2]... kèm title, content, domain, relevance và trust score", GREEN, GREEN_BORDER)
rounded_box(d, boxes["debate"], "Multi-Agent Debate", "Defender tạo D*; Challenger tạo C*; REBUT/DEFEND theo claims_registry qua nhiều vòng", ORANGE, ORANGE_BORDER)
rounded_box(d, boxes["judge"], "Judge", "Tổng hợp evidence, source_scores và debate_history để sinh verdict", PURPLE, PURPLE_BORDER)
rounded_box(d, boxes["out"], "Đầu ra", "truth_score, reasoning, điểm quyết định, lịch sử tranh luận và nguồn bằng chứng", BLUE, BLUE_BORDER)

# Main forward flow
arrow(d, (280, 205), (380, 205))
arrow(d, (660, 175), (780, 155))
arrow(d, (1060, 155), (1150, 155))
arrow(d, (660, 255), (780, 430))
arrow(d, (1060, 435), (1150, 425))
arrow(d, (1295, 500), (1295, 620))
# KB feeds debate without crossing boxes
poly_arrow(d, [(1295, 220), (1295, 285), (930, 285), (930, 330)], GREEN_BORDER)
# Debate state update routed below all boxes; no crossing through MADState
poly_arrow(d, [(920, 540), (920, 825), (520, 825), (520, 300)], ORANGE_BORDER)
d.text((600, 790), "save_round cập nhật debate_history và current_round", fill=TEXT, font=FONT_SMALL)

img.save(OUT / "mad_system_overview.png", "PNG")
