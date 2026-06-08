"""Gradio demo for MAD System for Fake News Detection."""

from __future__ import annotations

import html
import json
import os
from typing import Any

import gradio as gr
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from config.settings import config
from graph.state import build_initial_state
from graph.workflow import build_non_search_workflow, build_workflow

load_dotenv()


def create_llm() -> ChatOpenAI:
    api_key = os.getenv("NINEROUTER_API_KEY")
    base_url = os.getenv("NINEROUTER_BASE_URL")
    if not api_key or not base_url:
        raise RuntimeError("Thiếu NINEROUTER_API_KEY hoặc NINEROUTER_BASE_URL trong file .env.")

    return ChatOpenAI(
        model=config.model.model_name,
        temperature=config.model.debate_temperature,
        api_key=api_key,
        base_url=base_url,
    )


def _escape(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _empty_outputs(message: str):
    return (
        _status_view([message]),
        _build_verdict_view({}),
        _build_debate_thread_view({}),
        _build_research_view([], [], {}),
    )


def run_analysis(news_text: str, initial_context: str, debate_mode: str, max_rounds: int):
    news_text = (news_text or "").strip()
    initial_context = (initial_context or "").strip()
    mode = "non_search" if debate_mode == "Non-search" else "search"

    if not news_text:
        yield _empty_outputs("Vui lòng nhập bản tin hoặc claim cần kiểm chứng.")
        return

    if mode == "non_search" and not initial_context:
        yield _empty_outputs("Chế độ Non-search cần ngữ cảnh hoặc bằng chứng ban đầu.")
        return

    progress = [f"Khởi động MAD System ở chế độ {debate_mode} với {int(max_rounds)} vòng tranh luận."]
    research_display = _build_research_view([], [], {})
    debate_display = _build_debate_thread_view({})
    verdict_display = _build_verdict_view({})
    yield _status_view(progress), verdict_display, debate_display, research_display

    kb_entries: list[dict] = []
    executed_queries: list[str] = []
    source_scores: dict[str, float] = {}
    claims_registry: dict[str, list[dict]] = {}

    try:
        llm = create_llm()
        workflow = build_non_search_workflow(llm) if mode == "non_search" else build_workflow(llm)
        initial_state = build_initial_state(
            news_text=news_text,
            initial_context=initial_context if mode == "non_search" else None,
            debate_mode=mode,
            max_rounds=int(max_rounds),
        )

        for event in workflow.stream(initial_state, stream_mode="updates"):
            for node_name, node_output in event.items():
                node_output = node_output or {}

                if node_name in {"prepare_round", "prepare"}:
                    if node_name == "prepare" and node_output.get("knowledge_base"):
                        kb_entries.extend(node_output.get("knowledge_base", []))
                        source_scores.update(node_output.get("source_scores", {}))
                        research_display = _build_research_view(kb_entries, executed_queries, source_scores)
                        progress.append("Đã nạp ngữ cảnh ban đầu thành nguồn [S1].")
                    else:
                        progress.append("Chuẩn bị vòng tranh luận và lập kế hoạch truy vấn.")

                elif "search" in node_name:
                    new_kb = node_output.get("knowledge_base", []) or []
                    new_queries = node_output.get("executed_queries", []) or []
                    kb_entries.extend(new_kb)
                    executed_queries.extend(new_queries)
                    research_display = _build_research_view(kb_entries, executed_queries, source_scores)
                    progress.append(f"Tìm kiếm bằng chứng: thu thập thêm {len(new_kb)} nguồn.")

                elif node_name == "score_sources":
                    source_scores.update(node_output.get("source_scores", {}) or {})
                    research_display = _build_research_view(kb_entries, executed_queries, source_scores)
                    progress.append("Đã chấm điểm độ tin cậy của các nguồn bằng chứng.")

                elif node_name in {"defender", "challenger"}:
                    claims_registry.update(node_output.get("claims_registry", {}) or {})
                    debate_display = _build_debate_thread_view(claims_registry)
                    side = "Defender" if node_name == "defender" else "Challenger"
                    progress.append(f"{side} đã cập nhật lập luận và claims registry.")

                elif node_name == "save_round":
                    current_round = node_output.get("current_round")
                    progress.append(f"Đã lưu vòng tranh luận. Vòng tiếp theo: {current_round}.")

                elif node_name == "judge":
                    verdict = node_output.get("verdict", {}) or {}
                    verdict_display = _build_verdict_view(verdict)
                    progress.append(f"Judge đã đưa ra phán quyết với truth_score = {verdict.get('truth_score', 'N/A')}.")

                yield _status_view(progress), verdict_display, debate_display, research_display

    except Exception as exc:
        progress.append(f"Lỗi khi chạy hệ thống: {_escape(exc)}")
        yield _status_view(progress), verdict_display, debate_display, research_display


def _status_view(messages: list[str]) -> str:
    items = "".join(f"<li>{_escape(msg)}</li>" for msg in messages[-12:])
    return f"""
<div class='mad-card'>
  <h3>Tiến trình xử lý</h3>
  <ol class='mad-progress'>{items}</ol>
</div>
"""


def _build_research_view(kb_entries: list[dict], executed_queries: list[str], source_scores: dict[str, float] | None = None) -> str:
    source_scores = source_scores or {}
    if not kb_entries and not executed_queries:
        return """
<div class='mad-card muted-card'>
  <h3>Nguồn bằng chứng</h3>
  <p>Chưa có nguồn bằng chứng. Với Search Mode, nguồn sẽ xuất hiện sau bước tìm kiếm. Với Non-search Mode, context đầu vào sẽ được nạp thành [S1].</p>
</div>
"""

    query_html = ""
    if executed_queries:
        query_items = "".join(f"<span class='query-chip'>{_escape(q)}</span>" for q in executed_queries[-8:])
        query_html = f"<div class='query-list'><strong>Truy vấn gần nhất:</strong><br>{query_items}</div>"

    source_blocks = []
    for entry in kb_entries:
        sid = _escape(entry.get("id", "S?"))
        title = _escape(entry.get("title", "Không có tiêu đề"))
        url = _escape(entry.get("source_url", "#"))
        domain = _escape(entry.get("domain", "unknown"))
        content = _escape(entry.get("content", "Chưa có trích xuất chi tiết."))
        relevance = _safe_float(entry.get("relevance_score"), 0.0)
        trust = source_scores.get(str(entry.get("id", "")))
        trust_text = f"Trust {trust:.2f}" if isinstance(trust, (int, float)) else "Trust N/A"
        source_blocks.append(f"""
<details class='source-card' open>
  <summary><strong>{sid}</strong> {title}</summary>
  <div class='source-meta'>Domain: {domain} · Relevance {relevance:.2f} · {trust_text}</div>
  <a href='{url}' target='_blank' rel='noopener noreferrer'>{url}</a>
  <p>{content}</p>
</details>
""")

    return f"""
<div class='mad-card'>
  <h3>Nguồn bằng chứng</h3>
  {query_html}
  {''.join(source_blocks)}
</div>
"""


def _build_debate_thread_view(registry: dict) -> str:
    if not registry:
        return """
<div class='mad-card muted-card'>
  <h3>Luồng tranh luận</h3>
  <p>Chưa có lập luận. Khi hệ thống chạy, các nhận định D*/C* sẽ được hiển thị theo từng vòng.</p>
</div>
"""

    interactions = []
    for claim_id, history in registry.items():
        for entry in history or []:
            interactions.append({**entry, "claim_id": claim_id})

    interactions.sort(key=lambda x: (_safe_float(x.get("round"), 0), 0 if x.get("side") == "D" else 1))
    html_parts = ["<div class='mad-card'><h3>Luồng tranh luận theo claims registry</h3>"]
    current_round = None

    for item in interactions:
        round_no = item.get("round", "?")
        if round_no != current_round:
            current_round = round_no
            html_parts.append(f"<h4 class='round-title'>Vòng {round_no}</h4>")

        side = item.get("side", "?")
        side_name = "Defender" if side == "D" else "Challenger" if side == "C" else "Agent"
        side_class = "defender" if side == "D" else "challenger"
        claim_id = _escape(item.get("claim_id", "?"))
        action = _escape(item.get("action_type", "ASSERT"))
        targets = item.get("target_claim_ids", []) or []
        target_text = ", ".join(_escape(t) for t in targets) if targets else "-"
        text = _escape(item.get("text", "Không có nội dung."))

        evidence_html = ""
        source_evidence = [e for e in item.get("evidence", []) or [] if e.get("evidence_type") == "SOURCE"]
        if source_evidence:
            snippets = []
            for ev in source_evidence:
                sid = _escape(ev.get("source_id", "?"))
                snippet = _escape(ev.get("snippet", ""))
                snippets.append(f"<blockquote><strong>{sid}</strong>: {snippet}</blockquote>")
            evidence_html = "<div class='evidence-list'>" + "".join(snippets) + "</div>"

        html_parts.append(f"""
<div class='claim-card {side_class}'>
  <div class='claim-head'>
    <span class='side-label'>{side_name}</span>
    <span class='claim-id'>{claim_id}</span>
    <span class='action-label'>{action}</span>
  </div>
  <div class='target-line'>Target: {target_text}</div>
  <p>{text}</p>
  {evidence_html}
</div>
""")

    html_parts.append("</div>")
    return "".join(html_parts)


def _build_verdict_view(verdict: dict) -> str:
    if not verdict:
        return """
<div class='mad-card verdict-card pending'>
  <h3>Phán quyết</h3>
  <p>Hệ thống chưa có phán quyết. Kết quả sẽ xuất hiện sau khi Judge tổng hợp tranh luận.</p>
</div>
"""

    score = max(0.0, min(1.0, _safe_float(verdict.get("truth_score"), 0.5)))
    percent = score * 100
    if score >= 0.85:
        label = "Đáng tin cậy"
        badge = "true"
    elif score >= 0.65:
        label = "Khá đáng tin"
        badge = "mostly-true"
    elif score > 0.35:
        label = "Chưa đủ chắc chắn"
        badge = "uncertain"
    elif score > 0.15:
        label = "Có dấu hiệu sai lệch"
        badge = "misleading"
    else:
        label = "Không đáng tin"
        badge = "false"

    points = verdict.get("top_3_decisive_points", []) or []
    points_html = "".join(f"<li>{_escape(point)}</li>" for point in points) or "<li>Judge không trả về điểm quyết định cụ thể.</li>"
    reasoning = _escape(verdict.get("final_reasoning") or verdict.get("reasoning") or "Không có phân tích chi tiết.")
    raw_json = _escape(json.dumps(verdict, ensure_ascii=False, indent=2))

    return f"""
<div class='mad-card verdict-card'>
  <div class='verdict-top'>
    <div>
      <h3>Phán quyết cuối cùng</h3>
      <span class='verdict-badge {badge}'>{label}</span>
    </div>
    <div class='score-circle'>{percent:.1f}%</div>
  </div>
  <h4>Các điểm quyết định</h4>
  <ul>{points_html}</ul>
  <h4>Phân tích</h4>
  <p>{reasoning}</p>
  <details>
    <summary>Raw verdict JSON</summary>
    <pre>{raw_json}</pre>
  </details>
</div>
"""


def update_context_hint(mode: str):
    if mode == "Non-search":
        return gr.update(
            label="Ngữ cảnh / bằng chứng ban đầu (bắt buộc với Non-search)",
            placeholder="Dán evidence hoặc context để hệ thống kiểm chứng claim trong phạm vi này...",
        )
    return gr.update(
        label="Ngữ cảnh bổ sung (tùy chọn với Search)",
        placeholder="Có thể để trống. Nếu nhập, nội dung này chỉ đóng vai trò tham khảo cho bạn khi chạy demo.",
    )


CUSTOM_CSS = """
* { color: #000000; }
.mad-card, .mad-card *, .input-panel, .input-panel *, .claim-card, .claim-card *, .source-card, .source-card * {
  color: #000000 !important;
  opacity: 1 !important;
  text-shadow: none !important;
}

.gradio-container { max-width: 1380px !important; margin: auto; }
.hero {
  padding: 28px 32px;
  border-radius: 24px;
  background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 55%, #0f766e 100%);
  color: white;
  margin-bottom: 18px;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.18);
}
.hero h1 { font-size: 2.45rem; margin: 0 0 8px 0; }
.hero p { font-size: 1.05rem; opacity: .92; max-width: 850px; }
.badge-row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 16px; }
.badge { background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.28); border-radius: 999px; padding: 7px 12px; font-size: .88rem; }
.input-panel, .mad-card {
  border: 1px solid #000000;
  border-radius: 12px;
  padding: 18px;
  background: #ffffff !important;
  color: #000000 !important;
  box-shadow: none;
}
.mad-card h3 { margin-top: 0; color: #0f172a; }
.muted-card { color: #000000 !important; background: #ffffff !important; }
.mad-progress { padding-left: 22px; line-height: 1.65; }
.query-chip { display: inline-block; margin: 6px 6px 0 0; padding: 5px 9px; border-radius: 999px; background: #ffffff !important; color: #000000 !important; border: 1px solid #000000; font-size: .86rem; }
.source-card { border: 1px solid #000000; border-radius: 8px; padding: 10px 12px; margin-top: 12px; background: #ffffff !important; color: #000000 !important; }
.source-card summary { cursor: pointer; color: #0f172a; }
.source-meta { color: #000000 !important; font-size: .88rem; margin: 7px 0; }
.round-title { color: #000000 !important; border-bottom: 1px solid #000000; padding-bottom: 6px; margin-top: 18px; }
.claim-card { border-radius: 8px; padding: 14px 16px; margin: 12px 0; border: 1px solid #000000; border-left: 5px solid #000000; background: #ffffff !important; color: #000000 !important; box-shadow: none; }
.claim-card.defender { border-color: #000000; border-left-color: #000000; background: #ffffff !important; color: #000000 !important; }
.claim-card.challenger { border-color: #000000; border-left-color: #000000; background: #ffffff !important; color: #000000 !important; }
.claim-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.side-label { font-weight: 700; color: #000000 !important; }
.claim-id, .action-label { font-size: .82rem; padding: 3px 8px; border-radius: 999px; background: #ffffff !important; color: #000000 !important; border: 1px solid #000000; }
.target-line { color: #000000 !important; font-size: .88rem; margin-bottom: 8px; }
.evidence-list blockquote { margin: 8px 0 0 0; padding: 10px 12px; border: 1px solid #000000; border-left: 4px solid #000000; background: #ffffff !important; color: #000000 !important; border-radius: 0; }
.verdict-top { display: flex; align-items: center; justify-content: space-between; gap: 18px; }
.score-circle { min-width: 112px; height: 112px; border-radius: 999px; display: flex; align-items: center; justify-content: center; background: #dbeafe; color: #1d4ed8; font-size: 1.55rem; font-weight: 800; }
.verdict-badge { display: inline-block; border-radius: 999px; padding: 7px 12px; color: #000000 !important; background: #ffffff !important; border: 1px solid #000000; font-weight: 700; }
.verdict-badge { display: inline-block; border-radius: 999px; padding: 7px 12px; color: #000000 !important; background: #ffffff !important; border: 1px solid #000000; font-weight: 700; }
.verdict-badge { display: inline-block; border-radius: 999px; padding: 7px 12px; color: #000000 !important; background: #ffffff !important; border: 1px solid #000000; font-weight: 700; }
.verdict-badge { display: inline-block; border-radius: 999px; padding: 7px 12px; color: #000000 !important; background: #ffffff !important; border: 1px solid #000000; font-weight: 700; }
.verdict-badge { display: inline-block; border-radius: 999px; padding: 7px 12px; color: #000000 !important; background: #ffffff !important; border: 1px solid #000000; font-weight: 700; }
.verdict-badge { display: inline-block; border-radius: 999px; padding: 7px 12px; color: #000000 !important; background: #ffffff !important; border: 1px solid #000000; font-weight: 700; }
pre { white-space: pre-wrap; background: #ffffff !important; color: #000000 !important; border: 1px solid #000000; border-radius: 0; padding: 12px; }
"""


APP_THEME = gr.themes.Soft(primary_hue="blue", secondary_hue="teal", neutral_hue="slate")


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="MAD System") as demo:
        gr.HTML(
            """
<div class='hero'>
  <h1>MAD System for Fake News Detection</h1>
  <p>Giao diện kiểm chứng tin giả dựa trên truy xuất bằng chứng, tranh biện đa tác tử và phán quyết có khả năng truy vết.</p>
  <div class='badge-row'>
    <span class='badge'>Multi-Agent Debate</span>
    <span class='badge'>LangGraph Workflow</span>
    <span class='badge'>Search / Non-search</span>
    <span class='badge'>FEVER-ready</span>
  </div>
</div>
"""
        )

        with gr.Row(equal_height=False):
            with gr.Column(scale=4, min_width=360):
                with gr.Group(elem_classes="input-panel"):
                    gr.Markdown("### Thông tin đầu vào")
                    news_input = gr.Textbox(
                        label="Bản tin hoặc claim cần kiểm chứng",
                        placeholder="Ví dụ: A public figure claimed that ...",
                        lines=7,
                    )
                    mode_radio = gr.Radio(
                        ["Search", "Non-search"],
                        value="Search",
                        label="Chế độ vận hành",
                        info="Search tự truy xuất bằng chứng. Non-search chỉ dùng context bạn cung cấp.",
                    )
                    context_input = gr.Textbox(
                        label="Ngữ cảnh bổ sung (tùy chọn với Search)",
                        placeholder="Có thể để trống khi dùng Search Mode.",
                        lines=8,
                    )
                    rounds_slider = gr.Slider(1, 5, value=3, step=1, label="Số vòng tranh luận")
                    run_btn = gr.Button("Phân tích và kiểm chứng", variant="primary", size="lg")

                gr.Examples(
                    examples=[
                        ["Frank Ocean was in a poll.", "Frank Ocean is an American singer and songwriter. Evidence may mention lists, rankings, or polls.", "Non-search", 1],
                        ["A study claims drinking three cups of coffee a day reduces liver cancer risk by 50%.", "", "Search", 2],
                    ],
                    inputs=[news_input, context_input, mode_radio, rounds_slider],
                )

            with gr.Column(scale=8):
                with gr.Tabs():
                    with gr.Tab("Phán quyết"):
                        verdict_box = gr.HTML(_build_verdict_view({}))
                    with gr.Tab("Tranh luận"):
                        debate_box = gr.HTML(_build_debate_thread_view({}))
                    with gr.Tab("Nguồn bằng chứng"):
                        research_box = gr.HTML(_build_research_view([], [], {}))
                    with gr.Tab("Tiến trình"):
                        status_box = gr.HTML(_status_view(["Hệ thống sẵn sàng."]))

        mode_radio.change(fn=update_context_hint, inputs=[mode_radio], outputs=[context_input])
        run_btn.click(
            fn=run_analysis,
            inputs=[news_input, context_input, mode_radio, rounds_slider],
            outputs=[status_box, verdict_box, debate_box, research_box],
        )

    return demo


demo = build_demo()

if __name__ == "__main__":
    demo.launch(theme=APP_THEME, css=CUSTOM_CSS)




