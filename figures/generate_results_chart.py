from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
OUT = Path(__file__).resolve().parent
try:
    FT=ImageFont.truetype("arialbd.ttf",30); FB=ImageFont.truetype("arialbd.ttf",18); F=ImageFont.truetype("arial.ttf",15); FS=ImageFont.truetype("arial.ttf",13)
except Exception:
    FT=FB=F=FS=ImageFont.load_default()
models=["Llama 3.3\n70B","Gemma\n4-31B","GPT-OSS\n120B","Gemini 3.1\nFlash Lite"]
base_scores=[92.5,82.5,85.0,80.0]; mad_scores=[97.5,90.0,92.5,85.0]
w,h=1400,820; img=Image.new("RGB",(w,h),"white"); d=ImageDraw.Draw(img)
title="So sánh Accuracy giữa Base LLM và hệ thống MAD trên FEVER"; bb=d.textbbox((0,0),title,font=FT); d.text(((w-(bb[2]-bb[0]))/2,20),title,font=FT,fill="#1F1F1F")
left,top,right,bottom=130,120,1280,650
d.line([(left,top),(left,bottom),(right,bottom)],fill="#333",width=3)
for yv in range(0,101,10):
    y=bottom-(yv/100)*(bottom-top)
    d.line([(left-5,y),(right,y)],fill="#E5E5E5",width=1)
    d.text((70,y-8),f"{yv}%",font=FS,fill="#333")
bar_group=(right-left)/len(models); bw=70
for i,model_name in enumerate(models):
    cx=left+bar_group*i+bar_group/2
    for val,off,col in [(base_scores[i],-45,"#8DB7E8"),(mad_scores[i],45,"#F2B56B")]:
        x1=cx+off-bw/2; x2=cx+off+bw/2; y=bottom-(val/100)*(bottom-top)
        d.rectangle((x1,y,x2,bottom),fill=col,outline="#333")
        d.text((x1+4,y-22),f"{val:.1f}%",font=FS,fill="#111")
    yy=bottom+20
    for line in model_name.split("\n"):
        b=d.textbbox((0,0),line,font=F); d.text((cx-(b[2]-b[0])/2,yy),line,font=F,fill="#111"); yy+=18
d.rectangle((1030,80,1060,105),fill="#8DB7E8",outline="#333"); d.text((1070,82),"Base LLM",font=F,fill="#111")
d.rectangle((1160,80,1190,105),fill="#F2B56B",outline="#333"); d.text((1200,82),"MAD",font=F,fill="#111")
d.text((left,720),"Nguồn số liệu: kết quả thực nghiệm FEVER nhị phân trong báo cáo.",font=F,fill="#333")
img.save(OUT/"fever_accuracy_comparison.png","PNG")
