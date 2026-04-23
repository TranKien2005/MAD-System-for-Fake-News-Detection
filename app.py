"""
MAD System — Information Dashboard (3-Column Layout)
Focused on data transparency and complete information visibility.

Usage:
    python app.py
"""

import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from config.settings import config
from graph.workflow import build_workflow

load_dotenv()

import gradio as gr


def create_llms():
    """Create LLM instances."""
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
    """
    Run the MAD system and yield progress updates for Gradio.
    """
    if not news_text.strip():
        yield "⚠️ Vui lòng nhập tin tức.", "", "", ""
        return

    config.debate.max_rounds = int(max_rounds)
    llm_main, llm_light = create_llms()
    app = build_workflow(llm_main, llm_light)

    initial_state = {
        "original_news": news_text,
        "knowledge_base": [],
        "pending_search_queries": [],
        "executed_queries": [],
        "active_side": "DEFENDER",
        "current_round": 1,
        "max_rounds": config.debate.max_rounds,
        "debate_history": [],
        "current_defender_argument": "",
        "current_challenger_argument": "",
        "evaluator_rulings": [],
        "verdict": None,
    }

    # State variables for display
    progress_log = "🚀 **Bắt đầu phân tích hệ thống...**\n\n"
    research_display = "### 📚 PHÒNG NGHIÊN CỨU (KNOWLEDGE BASE)\n\n*Chưa có dữ liệu tìm kiếm...*"
    debate_display = "### ⚔️ ĐẤU TRƯỜNG TRANH LUẬN\n\n*Đang khởi tạo bối cảnh...*"
    analysis_display = "### ⚖️ HÀNH LANG PHÂN TÍCH\n\n*Chờ dữ liệu từ các vòng...*"

    yield progress_log, research_display, debate_display, analysis_display

    # Internal buffers
    kb_entries = []
    executed_queries = []
    debate_history_text = ""
    eval_text = ""

    for event in app.stream(initial_state, stream_mode="updates"):
        for node_name, node_output in event.items():

            if node_name == "direct_search_news":
                new_kb = node_output.get("knowledge_base", [])
                queries = node_output.get("executed_queries", [])
                
                kb_entries.extend(new_kb)
                executed_queries.extend(queries)
                
                if not new_kb:
                    progress_log += f"⚠️ **Tim kiem ban dau**: Khong tim thay nguon tin nao.\n\n"
                else:
                    progress_log += f"🔍 **Tim kiem ban dau**: Thanh cong ({len(new_kb)} nguon).\n\n"
                
                research_display = _build_research_column(kb_entries, executed_queries)
                yield progress_log, research_display, debate_display, analysis_display

            elif node_name.startswith("ask_"):
                queries = node_output.get("pending_search_queries", [])
                side = node_output.get("active_side", "Agent")
                
                if queries:
                    q_str = ", ".join(f"`{q}`" for q in queries)
                    progress_log += f"🧠 **{side}** yeu cau tim kiem: {q_str}\n\n"
                else:
                    progress_log += f"🧠 **{side}**: Da du bang chung, khong can tim them.\n\n"
                
                yield progress_log, research_display, debate_display, analysis_display

            elif node_name.startswith("search_"):
                new_kb = node_output.get("knowledge_base", [])
                new_queries = node_output.get("executed_queries", [])
                kb_entries.extend(new_kb)
                executed_queries.extend(new_queries)
                
                if new_kb:
                    progress_log += f"🔄 **Tra cuu bo sung**: Them {len(new_kb)} nguon moi.\n\n"
                    research_display = _build_research_column(kb_entries, executed_queries)
                yield progress_log, research_display, debate_display, analysis_display

            elif node_name in ("score_initial", "score_def", "score_chal"):
                new_scores = node_output.get("source_scores", {})
                if new_scores:
                    progress_log += f"⚖️ **Source Scorer**: Da cham diem {len(new_scores)} nguon.\n\n"
                yield progress_log, research_display, debate_display, analysis_display

            elif node_name == "defender":
                arg = node_output.get("current_defender_argument", "")
                progress_log += "✅ **Defender** da gui lap luan.\n\n"
                debate_history_text += f"\n\n---\n### 🟢 DEFENDER (Bao ve tin THAT)\n\n{arg}"
                debate_display = f"### ⚔️ DAU TRUONG TRANH LUAN\n{debate_history_text}"
                yield progress_log, research_display, debate_display, analysis_display

            elif node_name == "challenger":
                arg = node_output.get("current_challenger_argument", "")
                progress_log += "❌ **Challenger** da gui phan bien.\n\n"
                debate_history_text += f"\n\n---\n### 🔴 CHALLENGER (Bao ve tin GIA)\n\n{arg}"
                debate_display = f"### ⚔️ DAU TRUONG TRANH LUAN\n{debate_history_text}"
                yield progress_log, research_display, debate_display, analysis_display

            elif node_name == "evaluator":
                rulings = node_output.get("evaluator_rulings", [])
                if rulings:
                    r = rulings[0]
                    eval_text += _format_eval_ruling_dense(r)
                    analysis_display = f"### ⚖️ HANH LANG PHAN TICH\n{eval_text}"
                    progress_log += f"⚖️ **Evaluator** da tham dinh vong {r.get('round_number')}.\n\n"
                yield progress_log, research_display, debate_display, analysis_display

            elif node_name == "judge":
                progress_log += "🏆 **PHAN QUYET CUOI CUNG DA CO.**\n\n"
                verdict = node_output.get("verdict", {})
                analysis_display += _build_final_verdict_dense(verdict)
                yield progress_log, research_display, debate_display, analysis_display


def _build_research_column(kb_entries, executed_queries):
    text = "### 📚 PHONG NGHIEN CUU (KNOWLEDGE BASE)\n\n"
    
    if executed_queries:
        text += "#### 🔎 Lich su truy van:\n"
        for q in executed_queries:
            text += f"- `{q}`\n"
        text += "\n"

    text += "#### 📖 Danh sach nguon du lieu:\n"
    for entry in kb_entries:
        eid = entry.get("id", "S?")
        title = entry.get("title", "N/A")
        rel = entry.get("relevance_score", 0.0)
        url = entry.get("source_url", "#")
        content = entry.get("content", "")[:300]
        
        text += f"---\n**{eid} - {title}**\n"
        text += f"- **Relevance**: `{rel:.2f}` | [Source]({url})\n"
        text += f"> {content}...\n\n"
    
    return text


def _format_eval_ruling_dense(ruling):
    r_num = ruling.get("round_number", "?")
    text = f"\n#### 🔔 Tham dinh Vong {r_num}\n"
    
    # Use point_verifications (new format from evaluator)
    points = ruling.get("point_verifications", [])
    for p in points:
        pid = p.get("point_id", "?")
        status = p.get("status", "UNCERTAIN")
        verdict_text = p.get("evaluator_verdict", "")
        guidance = p.get("guidance", "")
        grounded = "Grounded" if p.get("is_grounded") else "NO SOURCE"
        common = " | Common Knowledge" if p.get("is_common_knowledge") else ""
        basic_r = " | Basic Reasoning" if p.get("is_basic_reasoning") else ""
        stubborn = " | STUBBORN" if p.get("is_stubborn") else ""
        
        symbol = {"VERIFIED": "✅", "DEBUNKED": "❌", "REJECTED": "🗑️"}.get(status, "🔄")
        text += f"- {symbol} **{pid}**: {status} ({grounded}{common}{basic_r}{stubborn})\n"
        if verdict_text:
            text += f"  - Ket luan: *{verdict_text}*\n"
        if guidance:
            text += f"  - 💡 **Guidance**: *{guidance}*\n"
    
    summary = ruling.get("round_summary", "")
    if summary:
        text += f"\n📝 **Tom tat**: {summary}\n"
    
    text += "---\n"
    return text


def _build_final_verdict_dense(verdict):
    v = verdict.get("verdict", "UNCERTAIN")
    conf = verdict.get("confidence", 0)
    
    emoji = {"LIKELY_REAL": "✅", "LIKELY_FAKE": "🚫"}.get(v, "❓")
    label = {"LIKELY_REAL": "TIN THAT", "LIKELY_FAKE": "TIN GIA"}.get(v, "KHONG XAC DINH")
    
    text = f"\n\n## 🏆 PHAN QUYET: {emoji} {label}\n"
    text += f"### 📊 Confidence: {conf}%\n\n"
    
    text += "#### 📈 Diem so tung nhan dinh:\n"
    for ps in verdict.get("final_scores", []):
        pid = ps.get("id", "?")
        combined = ps.get("combined_score", 0.0)
        reason = ps.get("reason", "")
        concluded = " (Evaluator da ket luan)" if ps.get("is_concluded_by_evaluator") else ""
        text += f"- **{pid}**: `{combined:.2f}`{concluded} - *{reason}*\n"
    
    text += f"\n- **Defender Weighted Avg**: `{verdict.get('defender_weighted_avg', 0):.2f}`\n"
    text += f"- **Challenger Weighted Avg**: `{verdict.get('challenger_weighted_avg', 0):.2f}`\n\n"
    
    text += f"#### 📝 Phan tich:\n{verdict.get('analysis', '')}\n\n"
    text += f"#### 🏁 Ket luan:\n{verdict.get('final_reasoning', '')}\n"
    
    return text


# --- Gradio UI ---

with gr.Blocks(title="MAD System — Command Center", theme=gr.themes.Default()) as demo:
    gr.Markdown("# 🕹️ MAD System: News Command Center")
    gr.Markdown("Hệ thống tranh biện đa Agent - Tập trung tối đa vào dữ liệu và tính minh bạch.")

    with gr.Row():
        with gr.Column(scale=1):
            news_input = gr.Textbox(label="📰 Tin tức đầu vào", lines=5, placeholder="Dán tin tức cần kiểm tra...")
            max_rounds = gr.Slider(minimum=1, maximum=5, value=3, step=1, label="🔄 Số vòng tranh luận")
            run_btn = gr.Button("🚀 BẮT ĐẦU PHÂN TÍCH", variant="primary")
            
            progress_output = gr.Markdown(label="📡 Trạng thái hệ thống", value="*Hệ thống sẵn sàng...*")

    with gr.Row():
        # Column 1: Research
        with gr.Column(scale=1, variant="panel"):
            research_output = gr.Markdown(value="### 📚 PHÒNG NGHIÊN CỨU")
            
        # Column 2: Debate
        with gr.Column(scale=1, variant="panel"):
            debate_output = gr.Markdown(value="### ⚔️ ĐẤU TRƯỜNG TRANH LUẬN")
            
        # Column 3: Analysis
        with gr.Column(scale=1, variant="panel"):
            analysis_output = gr.Markdown(value="### ⚖️ HÀNH LANG PHÂN TÍCH")

    run_btn.click(
        fn=run_analysis,
        inputs=[news_input, max_rounds],
        outputs=[progress_output, research_output, debate_output, analysis_output]
    )

if __name__ == "__main__":
    demo.launch()
