"""
MAD System — Redesigned Interface
Focus: Unified Thread Tracking, Dynamic ID Visualization, and Enhanced UX.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import gradio as gr

from config.settings import config
from graph.workflow import build_workflow
from graph.state import build_initial_state

load_dotenv()

def create_llms():
    api_key = os.getenv("NINEROUTER_API_KEY")
    base_url = os.getenv("NINEROUTER_BASE_URL")

    llm_main = ChatOpenAI(
        model=config.model.main_model,
        temperature=config.model.debate_temperature,
        api_key=api_key,
        base_url=base_url,
        max_tokens=config.model.max_tokens,
    )
    llm_light = ChatOpenAI(
        model=config.model.light_model,
        temperature=config.model.parser_temperature,
        api_key=api_key,
        base_url=base_url,
        max_tokens=config.model.max_tokens,
    )
    return llm_main, llm_light

def run_analysis(news_text: str, max_rounds: int):
    if not news_text.strip():
        yield "⚠️ Vui lòng nhập tin tức.", "", "", ""
        return

    config.debate.max_rounds = int(max_rounds)
    llm_main, llm_light = create_llms()
    app = build_workflow(llm_main, llm_light)

    initial_state = build_initial_state(
        news_text=news_text,
        max_rounds=config.debate.max_rounds,
    )

    progress_log = "🚀 **Khởi động hệ thống MAD...**\n\n"
    research_display = "### 📚 PHÒNG NGHIÊN CỨU\n*Chưa có dữ liệu...*"
    debate_display = "### ⚔️ LUỒNG TRANH LUẬN\n*Đang chờ lượt đầu tiên...*"
    verdict_display = "### ⚖️ PHÁN QUYẾT\n*Chờ kết thúc tranh luận...*"

    yield progress_log, research_display, debate_display, verdict_display

    kb_entries = []
    executed_queries = []
    claims_registry = {}

    for event in app.stream(initial_state, stream_mode="updates"):
        for node_name, node_output in event.items():
            
            if node_name == "prepare_round":
                progress_log += f"🧭 **Vòng {node_output.get('current_round', '?')}**: Đang lập kế hoạch tìm kiếm...\n"
                yield progress_log, research_display, debate_display, verdict_display

            elif "search" in node_name:
                new_kb = node_output.get("knowledge_base", [])
                new_queries = node_output.get("executed_queries", [])
                kb_entries.extend(new_kb)
                executed_queries.extend(new_queries)
                research_display = _build_research_view(kb_entries, executed_queries)
                progress_log += f"🔍 **Tìm kiếm**: Đã tìm thấy {len(new_kb)} nguồn mới.\n"
                if new_queries:
                    progress_log += f"   *(Truy vấn: {', '.join([q for q in new_queries])})*\n"
                yield progress_log, research_display, debate_display, verdict_display

            elif node_name in ["defender", "challenger"]:
                claims_registry.update(node_output.get("claims_registry", {}))
                side = "DEFENDER" if node_name == "defender" else "CHALLENGER"
                emoji = "🟢" if side == "DEFENDER" else "🔴"
                progress_log += f"{emoji} **{side}** đã đưa ra lập luận.\n"
                debate_display = _build_debate_thread_view(claims_registry)
                yield progress_log, research_display, debate_display, verdict_display

            elif node_name == "judge":
                verdict = node_output.get("verdict", {})
                progress_log += f"\n⚖️  [Judge] Đang tổng hợp và đưa ra phán quyết...\n"
                progress_log += f"   → Truth Score: {verdict.get('truth_score', 0.5)}\n"
                verdict_display = _build_verdict_view(verdict)
                yield progress_log, research_display, debate_display, verdict_display

def _build_debate_thread_view(registry: dict):
    if not registry:
        return "Chưa có nội dung."
    
    # Collect and sort all interactions
    all_interactions = []
    for cid, history in registry.items():
        for entry in history:
            all_interactions.append({**entry, "claim_id": cid})
            
    all_interactions.sort(key=lambda x: (x['round'], 0 if x['side'] == 'D' else 1))
    
    text = "### ⚔️ LUỒNG TRANH LUẬN\n"
    current_round = 0
    
    for h in all_interactions:
        if h['round'] > current_round:
            current_round = h['round']
            text += f"\n<hr>\n<h4 style='color: #4f46e5; margin-top: 15px;'>📍 VÒNG {current_round}</h4>\n\n"
            
        side_emoji = "🛡️" if h['side'] == "D" else "🗡️"
        side_name = "DEFENDER" if h['side'] == "D" else "CHALLENGER"
        atype = h.get('action_type', 'ASSERT')
        target_ids = h.get('target_claim_ids', [])
        cid = h.get('claim_id', '?')
        
        # Labeling according to user request
        if atype == "ASSERT":
            label = f"[KHỞI TẠO NHẬN ĐỊNH {cid}]"
        elif atype == "REBUT":
            label = f"[PHẢN BIỆN {', '.join(target_ids)}]"
        elif atype == "DEFEND":
            label = f"[BẢO VỆ {cid}]"
        else:
            label = f"[{atype} {cid}]"
            
        color = "#16a34a" if h['side'] == "D" else "#dc2626"
        bg_color = "rgba(22, 163, 74, 0.05)" if h['side'] == "D" else "rgba(220, 38, 38, 0.05)"
        border_color = "#16a34a" if h['side'] == "D" else "#dc2626"
        
        text += f"<div style='background-color: {bg_color}; border-left: 4px solid {border_color}; padding: 10px 15px; margin: 10px 0; border-radius: 4px;'>\n"
        text += f"{side_emoji} <strong style='color:{color}'>{side_name}</strong> <code>{label}</code><br><br>\n"
        text += f"<div style='color: inherit; line-height: 1.5;'>{h['text']}</div>\n\n"
        
        # Sources
        source_ids = [e.get('source_id') for e in h.get('evidence', []) if e.get('evidence_type') == 'SOURCE']
        if source_ids:
            text += f"<br><em style='color: #6b7280; font-size: 0.9em;'>(Nguồn: {', '.join(source_ids)})</em>\n"
        
        text += "</div>\n"
            
    return text

def _build_research_view(kb_entries, executed_queries):
    text = "### 📚 PHÒNG NGHIÊN CỨU\n\n"
    if executed_queries:
        text += "**Lịch sử tìm kiếm:**\n" + ", ".join([f"`{q}`" for q in executed_queries[-3:]]) + "\n\n"
    
    for entry in kb_entries:
        eid = entry.get("id", "S?")
        title = entry.get("title", "N/A")
        score = entry.get("relevance_score", 0.0)
        url = entry.get("source_url", "#")
        content = entry.get("content", "Chưa có trích xuất chi tiết...")
        
        text += f"<details open style='margin-bottom: 8px; border: 1px solid var(--border-color-primary, #e2e8f0); border-radius: 4px; padding: 5px 10px; background: var(--background-fill-secondary, transparent);'>\n"
        text += f"  <summary style='cursor: pointer; font-weight: 500;'><strong>{eid}</strong>: <a href='{url}' target='_blank'>{title}</a> <em>(Score: {score:.2f})</em></summary>\n"
        text += f"  <p style='margin-top: 8px; font-size: 0.9em; opacity: 0.85; white-space: pre-wrap;'>{content}</p>\n"
        text += f"</details>\n"
    return text

def _build_verdict_view(verdict):
    score = verdict.get("truth_score", 0.5)
    if score == 1.0:
        emoji = "✅"
        label = "HOÀN TOÀN CHÍNH XÁC (True)"
    elif score >= 0.75:
        emoji = "☑️"
        label = "KHÁ CHÍNH XÁC (Mostly True)"
    elif score == 0.5:
        emoji = "❓"
        label = "KHÔNG THỂ XÁC ĐỊNH (Uncertain)"
    elif score >= 0.25:
        emoji = "⚠️"
        label = "SAI LỆCH NGHIÊM TRỌNG (Misleading/Mostly False)"
    else:
        emoji = "🚫"
        label = "HOÀN TOÀN BỊA ĐẶT (Fake News)"
        
    text = f"## {emoji} KẾT LUẬN: {label}\n"
    text += f"**Độ chân thực (Truth Score):** {score*100:.1f}%\n\n"
    text += "#### 🎯 Các điểm mấu chốt:\n"
    for p in verdict.get("top_3_decisive_points", []):
        text += f"- {p}\n"
    text += f"\n#### 📝 Phân tích chi tiết:\n{verdict.get('final_reasoning', '')}"
    return text

# --- UI Design ---
custom_theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="blue",
    neutral_hue="slate"
)

with gr.Blocks(title="MAD System", theme=custom_theme) as demo:
    gr.HTML("""
    <div style="text-align: center; max-width: 800px; margin: 0 auto; padding: 20px 0;">
        <h1 style="color: #4338ca; font-size: 2.5rem; margin-bottom: 5px;">🛡️ MAD System</h1>
        <p style="font-size: 1.1rem; color: #64748b;">Hệ thống AI Đa tác vụ tự động điều tra, tranh biện và đánh giá độ xác thực của thông tin.</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=4):
            with gr.Group():
                news_input = gr.Textbox(
                    show_label=False,
                    placeholder="📰 Dán nội dung bản tin, bài viết hoặc tin đồn bạn muốn kiểm chứng vào đây...", 
                    lines=5
                )
                with gr.Row():
                    rounds_slider = gr.Slider(1, 5, 3, step=1, label="Số vòng tranh luận", info="Nhiều vòng hơn cho kết quả sâu hơn nhưng tốn thời gian hơn.")
                    run_btn = gr.Button("🚀 Phân tích & Kiểm chứng", variant="primary", size="lg")
            
            with gr.Accordion("📡 Bảng điều khiển hệ thống", open=True):
                status_box = gr.Markdown("*Hệ thống sẵn sàng.*")
            
            with gr.Accordion("📚 Nguồn Dữ liệu & Nghiên cứu", open=False):
                research_box = gr.Markdown("*Chưa có dữ liệu.*")
            
        with gr.Column(scale=6):
            with gr.Tabs():
                with gr.TabItem("⚔️ Diễn biến Tranh luận"):
                    debate_box = gr.Markdown("### ⚔️ LUỒNG TRANH LUẬN\n*Hãy nhập tin tức và bấm Phân tích để bắt đầu...*")
                with gr.TabItem("⚖️ Kết luận Phán quyết"):
                    verdict_box = gr.Markdown("### ⚖️ PHÁN QUYẾT\n*Chờ hệ thống đưa ra phán quyết cuối cùng...*")

    run_btn.click(
        fn=run_analysis,
        inputs=[news_input, rounds_slider],
        outputs=[status_box, research_box, debate_box, verdict_box]
    )

if __name__ == "__main__":
    demo.launch()
