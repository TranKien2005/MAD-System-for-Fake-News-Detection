"""
MAD System — Gradio UI
Hiển thị đầy đủ quá trình tranh luận và kết quả phán quyết.

Usage:
    python app.py
"""

import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from config.settings import config
from graph.workflow import build_workflow

load_dotenv()

import gradio as gr


def create_llms():
    """Create LLM instances."""
    llm_main = ChatGroq(
        model=config.model.main_model,
        temperature=config.model.debate_temperature,
    )
    llm_light = ChatGroq(
        model=config.model.light_model,
        temperature=config.model.parser_temperature,
    )
    return llm_main, llm_light


def run_analysis(news_text: str, max_rounds: int):
    """
    Run the MAD system and yield progress updates for Gradio.
    """
    if not news_text.strip():
        yield "⚠️ Vui lòng nhập tin tức cần kiểm tra.", "", "", ""
        return

    # Update config
    config.debate.max_rounds = int(max_rounds)

    llm_main, llm_light = create_llms()
    app = build_workflow(llm_main, llm_light)

    initial_state = {
        "original_news": news_text,
        "claims": [],
        "search_results": [],
        "pending_search_queries": [],
        "current_round": 1,
        "max_rounds": config.debate.max_rounds,
        "debate_history": [],
        "current_defender_argument": "",
        "current_challenger_argument": "",
        "verdict": None,
    }

    # Stream progress
    progress_log = ""
    claims_display = ""
    verdict_display = ""

    # Tích lũy tất cả các vòng đã hoàn thành
    completed_rounds_display = ""
    # Preview tạm cho vòng hiện tại (chưa hoàn thành)
    current_round_preview = ""

    progress_log += "🚀 **Bắt đầu phân tích...**\n\n"
    debate_display = ""
    yield progress_log, claims_display, debate_display, verdict_display

    # Run workflow step by step using stream
    for event in app.stream(initial_state, stream_mode="updates"):
        for node_name, node_output in event.items():

            if node_name == "claim_parser":
                claims = node_output.get("claims", [])
                progress_log += f"🔍 **Claim Parser** — Trích xuất được {len(claims)} claims\n\n"
                claims_display = "### 📋 Claims Trích Xuất\n\n"
                for i, c in enumerate(claims, 1):
                    claims_display += f"{i}. {c}\n"
                yield progress_log, claims_display, debate_display, verdict_display

            elif node_name == "initial_search":
                results = node_output.get("search_results", [])
                progress_log += f"🌐 **Search Agent** — Tìm thấy {len(results)} kết quả\n\n"
                yield progress_log, claims_display, debate_display, verdict_display

            elif node_name == "defender":
                arg = node_output.get("current_defender_argument", "")
                progress_log += f"✅ **Defender** đã đưa ra lập luận\n\n"
                # Preview: show defender arg for current round
                current_round_preview = f"\n---\n### ✅ Defender đang lập luận...\n\n{arg}\n"
                debate_display = completed_rounds_display + current_round_preview
                yield progress_log, claims_display, debate_display, verdict_display

            elif node_name == "challenger":
                arg = node_output.get("current_challenger_argument", "")
                progress_log += f"❌ **Challenger** đã đưa ra lập luận\n\n"
                # Preview: add challenger arg to current round
                current_round_preview += f"\n### ❌ Challenger đang phản biện...\n\n{arg}\n"
                debate_display = completed_rounds_display + current_round_preview
                yield progress_log, claims_display, debate_display, verdict_display

            elif node_name == "save_round":
                round_data = node_output.get("debate_history", [])
                if round_data:
                    r = round_data[0]
                    progress_log += f"💾 **Lưu vòng {r['round_number']}** hoàn tất\n\n"
                    # Finalize: add completed round to accumulated display
                    completed_rounds_display += _format_completed_round(r)
                    current_round_preview = ""
                    debate_display = completed_rounds_display
                yield progress_log, claims_display, debate_display, verdict_display

            elif node_name == "adaptive_search":
                results = node_output.get("search_results", [])
                if results:
                    progress_log += f"🔄 **Adaptive Search** — Tìm thêm {len(results)} kết quả\n\n"
                else:
                    progress_log += f"🔄 **Adaptive Search** — Không có yêu cầu tìm thêm\n\n"
                yield progress_log, claims_display, debate_display, verdict_display

            elif node_name == "judge":
                progress_log += f"⚖️ **Judge** đã đưa ra phán quyết!\n\n"
                verdict = node_output.get("verdict", {})
                verdict_display = _build_verdict_display(verdict)
                yield progress_log, claims_display, debate_display, verdict_display


def _format_completed_round(round_data):
    """Format a completed debate round for permanent display."""
    r_num = round_data["round_number"]
    defender_arg = round_data["defender_argument"]
    challenger_arg = round_data["challenger_argument"]

    section = f"\n## 🔔 Vòng {r_num}\n\n"
    section += f"### ✅ Defender (Bảo vệ tin thật)\n\n{defender_arg}\n\n"
    section += f"---\n\n"
    section += f"### ❌ Challenger (Bảo vệ tin giả)\n\n{challenger_arg}\n\n"
    return section


def _build_verdict_display(verdict):
    """Build the verdict display."""
    if not verdict:
        return "❓ Không có kết quả"

    v = verdict.get("verdict", "UNCERTAIN")
    confidence = verdict.get("confidence", 50)

    if v == "LIKELY_REAL":
        emoji = "✅"
        label = "CÓ VẺ LÀ TIN THẬT"
        color = "green"
    elif v == "LIKELY_FAKE":
        emoji = "🚫"
        label = "CÓ VẺ LÀ TIN GIẢ"
        color = "red"
    else:
        emoji = "❓"
        label = "KHÔNG CHẮC CHẮN"
        color = "orange"

    display = f"# {emoji} {label}\n\n"
    display += f"## 📊 Độ tin cậy: {confidence}%\n\n"
    display += f"### 📝 Giải thích\n\n{verdict.get('reasoning', 'N/A')}\n\n"

    # Key evidence
    key_evidence = verdict.get("key_evidence", [])
    if key_evidence:
        display += "### 🔑 Bằng chứng chính\n\n"
        for i, e in enumerate(key_evidence, 1):
            display += f"{i}. {e}\n"
        display += "\n"

    # Score table
    def_score = verdict.get("defender_score", {})
    chal_score = verdict.get("challenger_score", {})
    if def_score and chal_score:
        display += "### 📊 Bảng điểm\n\n"
        display += "| Tiêu chí | Defender | Challenger |\n"
        display += "|----------|---------|------------|\n"

        labels = {
            "evidence_quality": "Chất lượng bằng chứng",
            "rebuttal_effectiveness": "Hiệu quả phản bác",
            "unrefuted_points": "Điểm chưa bác bỏ",
            "consistency": "Tính nhất quán",
            "faithfulness": "Faithfulness",
        }
        for key, label in labels.items():
            d = def_score.get(key, "N/A")
            c = chal_score.get(key, "N/A")
            display += f"| {label} | {d} | {c} |\n"

    return display


# --- Build Gradio UI ---

with gr.Blocks(
    title="MAD System — Fake News Detection",
    theme=gr.themes.Soft(),
) as demo:
    gr.Markdown(
        """
        # 🔎 MAD System — Fake News Detection
        ### Multi-Agent Debate System for Detecting Fake News
        
        Nhập tin tức cần kiểm tra → Hệ thống sẽ tranh luận nhiều vòng → Đưa ra phán quyết
        """
    )

    with gr.Row():
        with gr.Column(scale=2):
            news_input = gr.Textbox(
                label="📰 Nhập tin tức cần kiểm tra",
                placeholder="Dán đoạn tin tức vào đây...",
                lines=5,
            )
        with gr.Column(scale=1):
            max_rounds = gr.Slider(
                minimum=1, maximum=5, value=3, step=1,
                label="🔄 Số vòng tranh luận",
            )
            run_btn = gr.Button("🚀 Bắt Đầu Phân Tích", variant="primary", size="lg")

    with gr.Row():
        with gr.Column(scale=1):
            progress_output = gr.Markdown(
                label="📋 Tiến trình",
                value="*Chờ nhập tin tức...*",
            )
            claims_output = gr.Markdown(
                label="📋 Claims",
                value="",
            )

        with gr.Column(scale=2):
            debate_output = gr.Markdown(
                label="💬 Quá trình tranh luận",
                value="*Chưa có dữ liệu tranh luận*",
            )

    verdict_output = gr.Markdown(
        label="⚖️ Kết quả phán quyết",
        value="*Chưa có phán quyết*",
    )

    # Wire up
    run_btn.click(
        fn=run_analysis,
        inputs=[news_input, max_rounds],
        outputs=[progress_output, claims_output, debate_output, verdict_output],
    )

    # Example inputs
    gr.Examples(
        examples=[
            ["Theo nghiên cứu mới nhất của Đại học Harvard năm 2024, uống 3 ly cà phê mỗi ngày giúp giảm 50% nguy cơ ung thư gan. Nghiên cứu được thực hiện trên 10,000 người trong 5 năm và đã được WHO công nhận."],
            ["NASA vừa xác nhận phát hiện sự sống ngoài Trái Đất trên sao Hỏa. Theo thông báo chính thức, các nhà khoa học đã tìm thấy vi khuẩn sống trong mẫu đất do rover Perseverance thu thập."],
            ["Bộ Y tế Việt Nam khuyến cáo người dân nên tiêm vaccine COVID-19 mũi nhắc lại để tăng cường miễn dịch trước mùa đông."],
        ],
        inputs=news_input,
        label="📝 Ví dụ tin tức",
    )


if __name__ == "__main__":
    demo.launch()
