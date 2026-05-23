from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
OUT = Path(__file__).resolve().parent
try:
    FT = ImageFont.truetype("arialbd.ttf", 30); FB=ImageFont.truetype("arialbd.ttf",20); F=ImageFont.truetype("arial.ttf",15)
except Exception:
    FT=FB=F=ImageFont.load_default()
BG="#fff"; TEXT="#1F1F1F"; BLUE="#DCEBFF"; GREEN="#E4F6E7"; RED="#FFE0E0"; PURPLE="#EFE5FF"; GRAY="#F2F2F2"; ORANGE="#FFF1D8"
B="#2F5E9E"; G="#3E8C4A"; R="#B24848"; P="#7150A8"; O="#B87516"; GR="#777"
def wrap(d,t,font,w):
    res=[]; cur=""
    for x in t.split():
        s=(cur+" "+x).strip()
        if d.textbbox((0,0),s,font=font)[2]<=w: cur=s
        else:
            if cur: res.append(cur)
            cur=x
    if cur: res.append(cur)
    return res
def box(d,xy,head,body,fill,out):
    x1,y1,x2,y2=xy; d.rounded_rectangle(xy, radius=18, fill=fill, outline=out, width=3); d.text((x1+14,y1+12),head,font=FB,fill=TEXT); y=y1+42
    for line in wrap(d,body,F,x2-x1-28): d.text((x1+14,y),line,font=F,fill=TEXT); y+=18
def arrow(d,s,e,c="#333"):
    import math
    d.line([s,e], fill=c, width=3); x1,y1=s; x2,y2=e; a=math.atan2(y2-y1,x2-x1); L=13; A=.45
    d.polygon([e,(x2-L*math.cos(a-A),y2-L*math.sin(a-A)),(x2-L*math.cos(a+A),y2-L*math.sin(a+A))], fill=c)
w,h=1400,760; img=Image.new("RGB",(w,h),BG); d=ImageDraw.Draw(img); title="Mô hình phiên tòa số trong Multi-Agent Debate"; bb=d.textbbox((0,0),title,font=FT); d.text(((w-bb[2])/2,20),title,font=FT,fill=TEXT)
box(d,(80,130,360,280),"Defender","Bảo vệ nhận định; tạo D1, D2; dùng evidence [S*] để củng cố lập luận",GREEN,G)
box(d,(80,420,360,570),"Challenger","Phản biện nhận định; tạo C1, C2; tìm lỗi thực thể, logic, phạm vi và thiếu bằng chứng",RED,R)
box(d,(540,120,860,290),"Claims Registry","Lưu thread D*/C*: ASSERT, REBUT, DEFEND, evidence và target_claim_ids",GRAY,GR)
box(d,(540,420,860,570),"Knowledge Base","Lưu nguồn [S1], [S2]... và source_scores do Source Scorer đánh giá",BLUE,B)
box(d,(1040,250,1320,430),"Judge","Đọc knowledge_base, source_scores, debate_history và claims_registry để sinh truth_score",PURPLE,P)
box(d,(540,610,860,720),"Source Scorer","Chấm trust_score cho nguồn mới trước khi tranh luận",ORANGE,O)
arrow(d,(360,205),(540,205),G); arrow(d,(360,495),(540,495),R); arrow(d,(700,290),(700,420),GR); arrow(d,(860,205),(1040,310),P); arrow(d,(860,495),(1040,370),P); arrow(d,(700,610),(700,570),O); arrow(d,(220,280),(220,420),"#999"); arrow(d,(220,420),(220,280),"#999")
d.text((112,340),"đối kháng qua nhiều vòng",font=F,fill=TEXT)
img.save(OUT/"mad_debate_court.png","PNG")
