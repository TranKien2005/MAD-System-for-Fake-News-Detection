from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
OUT = Path(__file__).resolve().parent
try:
    FONT_TITLE = ImageFont.truetype("arialbd.ttf", 30)
    FONT_BOX = ImageFont.truetype("arialbd.ttf", 20)
    FONT = ImageFont.truetype("arial.ttf", 16)
    FONT_SMALL = ImageFont.truetype("arial.ttf", 14)
except Exception:
    FONT_TITLE = FONT_BOX = FONT = FONT_SMALL = ImageFont.load_default()
BG = "#ffffff"; TEXT = "#1F1F1F"; BLUE="#DCEBFF"; BLUE_B="#2F5E9E"; GREEN="#E4F6E7"; GREEN_B="#3E8C4A"; ORANGE="#FFF1D8"; ORANGE_B="#B87516"; PURPLE="#EFE5FF"; PURPLE_B="#7150A8"; GRAY="#F2F2F2"; GRAY_B="#777777"

def wrap(draw, text, font, width):
    out=[]; cur=""
    for w in text.split():
        t=(cur+" "+w).strip()
        if draw.textbbox((0,0),t,font=font)[2] <= width: cur=t
        else:
            if cur: out.append(cur)
            cur=w
    if cur: out.append(cur)
    return out

def box(d, xy, title, body, fill, outline):
    x1,y1,x2,y2=xy
    d.rounded_rectangle(xy, radius=16, fill=fill, outline=outline, width=3)
    d.text((x1+14,y1+12), title, fill=TEXT, font=FONT_BOX)
    y=y1+42
    for line in wrap(d, body, FONT_SMALL, x2-x1-28):
        d.text((x1+14,y), line, fill=TEXT, font=FONT_SMALL); y+=18

def arrow(d, s, e, color="#333"):
    import math
    d.line([s,e], fill=color, width=3)
    x1,y1=s; x2,y2=e; ang=math.atan2(y2-y1,x2-x1); L=13; A=.45
    p1=(x2-L*math.cos(ang-A), y2-L*math.sin(ang-A)); p2=(x2-L*math.cos(ang+A), y2-L*math.sin(ang+A))
    d.polygon([e,p1,p2], fill=color)

def title(d, text, w):
    b=d.textbbox((0,0),text,font=FONT_TITLE); d.text(((w-(b[2]-b[0]))/2,20),text,fill=TEXT,font=FONT_TITLE)

w,h=1550,760
img=Image.new("RGB",(w,h),BG); d=ImageDraw.Draw(img); title(d,"Pipeline đánh giá FEVER: Base LLM và MAD non-search",w)
y=150
box(d,(60,y,270,y+115),"FEVER.jsonl","Claim, label SUPPORTS/REFUTES và evidence Wikipedia",BLUE,BLUE_B)
box(d,(340,y,560,y+115),"prepare_fever.py","Lọc nhãn nhị phân, lấy evidence, tạo initial_context",GREEN,GREEN_B)
box(d,(630,y,860,y+115),"fever_claims_binary","Dữ liệu đã xử lý: claim, label, initial_context",GREEN,GREEN_B)
box(d,(980,80,1230,210),"Base LLM","Hỏi trực tiếp mô hình nền để lấy dự đoán nhị phân",ORANGE,ORANGE_B)
box(d,(980,280,1230,430),"MAD non-search","run_mad(..., debate_mode=non_search); nạp context thành [S1]",PURPLE,PURPLE_B)
box(d,(1320,180,1500,330),"So sánh","Accuracy, Precision, Recall, F1, duration và lỗi parsing",GRAY,GRAY_B)
arrow(d,(270,y+58),(340,y+58)); arrow(d,(560,y+58),(630,y+58)); arrow(d,(860,y+40),(980,145)); arrow(d,(860,y+80),(980,355)); arrow(d,(1230,145),(1320,235)); arrow(d,(1230,355),(1320,275))
box(d,(250,560,1300,680),"Ý nghĩa thực nghiệm","Base LLM và MAD dùng cùng mô hình nền. Khác biệt kết quả chủ yếu phản ánh tác động của cơ chế điều phối, tranh luận và sử dụng evidence có cấu trúc.",BLUE,BLUE_B)
img.save(OUT/"fever_evaluation_pipeline.png","PNG")
