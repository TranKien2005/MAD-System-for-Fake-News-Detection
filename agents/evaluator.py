"""
Evaluator Agent — Evaluates each debate round and makes rulings on claims.
Replaces the old Moderator with authority to CONFIRM, REJECT, or KEEP claims.
"""

import json

from langchain_core.messages import HumanMessage

from prompts.templates import EVALUATOR_PROMPT, SOURCE_SCORER_PROMPT


def score_sources(state: dict, llm) -> dict:
    """
    Evaluates the trust score of new sources in the knowledge base.
    """
    kb = state.get("knowledge_base", [])
    scores = state.get("source_scores", {})
    
    # Identify new sources that haven't been scored yet
    new_sources_list = [entry for entry in kb if entry["id"] not in scores]
    
    if not new_sources_list:
        return {"source_scores": {}}

    # Format new sources for the prompt
    new_sources_text = "\n".join([
        f"📖 {s['id']} {s['title']} (Domain: {s['domain']})\n   {s['content'][:300]}..."
        for s in new_sources_list
    ])

    prompt = SOURCE_SCORER_PROMPT.format(
        original_news=state["original_news"],
        new_sources=new_sources_text
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    data = _parse_json_robust(response.content)
    
    new_scores = {}
    for item in data.get("assessments", []):
        sid = item.get("source_id")
        score = float(item.get("trust_score", 0.0))
        if sid:
            new_scores[sid] = score
            
    # Default 0.0 for any missed sources
    for s in new_sources_list:
        if s["id"] not in new_scores:
            new_scores[s["id"]] = 0.0

    print(f"\n⚖️ [Source Scorer] Đã giám định {len(new_scores)} nguồn mới.")
    return {"source_scores": new_scores}


def evaluate_round(state: dict, llm) -> dict:
    """
    Evaluate the current round's arguments based on evidence.
    Phases: Round 1 (Eligibility) | Round 2+ (Resolution/Steerance)
    """
    current_round = state.get("current_round", 1) - 1

    # Format knowledge base with scores
    kb_text = _format_knowledge_base(state.get("knowledge_base", []), state.get("source_scores", {}))

    # Format previous evaluator rulings
    prev_rulings = state.get("evaluator_rulings", [])
    prev_text = _format_previous_rulings(prev_rulings)

    prompt = EVALUATOR_PROMPT.format(
        original_news=state["original_news"],
        knowledge_base_with_scores=kb_text,
        previous_evaluator_rulings=prev_text,
        round_number=current_round,
        defender_argument=state.get("current_defender_argument", ""),
        challenger_argument=state.get("current_challenger_argument", ""),
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    ruling = _parse_json_robust(response.content)
    ruling["round_number"] = current_round

    return {
        "evaluator_rulings": [ruling],
    }


def format_evaluator_summary(evaluator_rulings: list[dict]) -> str:
    """Format all evaluator rulings as readable text for debater prompts."""
    if not evaluator_rulings:
        return "(Chưa có đánh giá từ Evaluator)"

    lines = []
    for ruling in evaluator_rulings:
        r_num = ruling.get("round_number", "?")
        lines.append(f"\n⚖️ THẨM ĐỊNH SAU VÒNG {r_num}:")

        # Point Verifications
        verifications = ruling.get("point_verifications", [])
        for v in verifications:
            pid = v.get("point_id", "?")
            status = v.get("status", "UNCERTAIN")
            grounded = "Grounded" if v.get("is_grounded") else "✖️ KHÔNG NGUỒN"
            common = " | Common Knowledge" if v.get("is_common_knowledge") else ""
            basic_r = " | Basic Reasoning" if v.get("is_basic_reasoning") else ""
            stubborn = " | ⚠️ CÃI CÙN" if v.get("is_stubborn") else ""
            verdict = v.get("evaluator_verdict", "")
            guidance = v.get("guidance", "")
            
            symbol = {"VERIFIED": "✅", "DEBUNKED": "❌", "REJECTED": "🗑️"}.get(status, "🔄")
            lines.append(f"  {symbol} {pid}: {status} ({grounded}{common}{basic_r}{stubborn})")
            if verdict:
                lines.append(f"     -> Kết luận: {verdict}")
            if guidance:
                lines.append(f"     -> 💡 CHỈ DẪN: {guidance}")

        summary = ruling.get("round_summary", "")
        if summary:
            lines.append(f"  📝 Tóm tắt: {summary}")

    return "\n".join(lines)


def _format_knowledge_base(knowledge_base: list, source_scores: dict = None) -> str:
    """Format knowledge base as readable text, including trust scores."""
    if not knowledge_base:
        return "(Không có dữ liệu từ Knowledge Base)"

    if source_scores is None:
        source_scores = {}

    lines = []
    for entry in knowledge_base:
        tid = entry.get("id", "[S?]")
        title = entry.get("title", "N/A")
        content = entry.get("content", "")
        domain = entry.get("domain", "")
        relevance = entry.get("relevance_score", 0.5)
        trust = source_scores.get(tid, "Chưa giám định")
        
        lines.append(f"📖 {tid} {title} (Trust: {trust} | Domain: {domain} | Relevance: {relevance:.2f})")
        lines.append(f"   {content[:400]}")
        lines.append("")
    return "\n".join(lines)


def _format_previous_rulings(rulings: list) -> str:
    """Format previous evaluator rulings."""
    if not rulings:
        return "(Chưa có đánh giá trước đó)"
    return format_evaluator_summary(rulings)


def _format_debate_history(debate_history: list) -> str:
    """Format debate history."""
    if not debate_history:
        return "(Chưa có lịch sử tranh luận)"

    lines = []
    for r in debate_history:
        lines.append(f"\n{'='*50}")
        lines.append(f"VÒNG {r['round_number']}")
        lines.append(f"{'='*50}")
        lines.append(f"📗 DEFENDER:\n{r['defender_argument']}")
        lines.append(f"\n📕 CHALLENGER:\n{r['challenger_argument']}")
    return "\n".join(lines)


def _parse_json_robust(text: str) -> dict:
    """Robustly parse JSON from LLM response."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return {}


# Public alias used by defender.py and challenger.py
parse_json_robust = _parse_json_robust
