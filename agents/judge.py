"""
Judge Agent — Evaluates the entire debate and delivers a final verdict.
Uses "Weight of Evidence" and prose analysis.
"""

import json

from langchain_core.messages import HumanMessage

from prompts.templates import JUDGE_PROMPT
from agents.evaluator import _format_knowledge_base


def judge(state: dict, llm) -> dict:
    """
    Evaluate the full debate history and produce a final verdict
    using the new integrated weighted scoring logic.
    """
    kb_text = _format_knowledge_base(state.get("knowledge_base", []), state.get("source_scores", {}))

    # Build full debate + evaluator history
    full_history = _format_full_debate_with_evaluator(
        state.get("debate_history", []),
        state.get("evaluator_rulings", []),
    )

    prompt = JUDGE_PROMPT.format(
        original_news=state["original_news"],
        knowledge_base=kb_text,
        full_debate_with_evaluator=full_history,
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    verdict = _parse_verdict(response.content)

    return {"verdict": verdict}


def _format_full_debate_with_evaluator(
    debate_history: list,
    evaluator_rulings: list,
) -> str:
    """Format the complete debate history interleaved with evaluator rulings."""
    if not debate_history:
        return "(Không có lịch sử tranh luận)"

    # Index evaluator rulings by round number
    rulings_by_round = {}
    for ruling in evaluator_rulings:
        r_num = ruling.get("round_number", 0)
        rulings_by_round[r_num] = ruling

    lines = []
    for r in debate_history:
        r_num = r["round_number"]
        lines.append(f"\n{'='*60}")
        lines.append(f"VÒNG {r_num}")
        lines.append(f"{'='*60}")
        lines.append(f"\n📗 DEFENDER:")
        lines.append(r["defender_argument"])
        lines.append(f"\n📕 CHALLENGER:")
        lines.append(r["challenger_argument"])

        # Add evaluator ruling for this round if exists
        if r_num in rulings_by_round:
            ruling = rulings_by_round[r_num]
            lines.append(f"\n⚖️ THẨM ĐỊNH SAU VÒNG {r_num}:")
            
            # Point Verifications
            verifications = ruling.get("point_verifications", [])
            for v in verifications:
                pid = v.get("point_id", "?")
                status = v.get("status", "UNCERTAIN")
                grounded = "Grounded" if v.get("is_grounded") else "✖️ KHÔNG NGUỒN"
                common = " | Common" if v.get("is_common_knowledge") else ""
                verdict = v.get("evaluator_verdict", "")
                
                symbol = {"VERIFIED": "✅", "DEBUNKED": "❌", "REJECTED": "🗑️"}.get(status, "🔄")
                lines.append(f"  {symbol} {pid}: {status} ({grounded}{common})")
                if verdict:
                    lines.append(f"     -> Phán quyết Evaluator: {verdict}")
            
            summary = ruling.get("round_summary", "")
            if summary:
                lines.append(f"  📝 Tóm tắt: {summary}")

    return "\n".join(lines)


def _parse_verdict(raw_text: str) -> dict:
    """Parse JSON verdict from Judge's response."""
    text = raw_text.strip()

    # Remove markdown code block if present
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

    return {
        "verdict": "UNCERTAIN",
        "confidence": 50,
        "final_reasoning": f"Không thể parse kết quả Judge. Raw: {raw_text[:500]}",
        "defender_weighted_avg": 0,
        "challenger_weighted_avg": 0,
        "final_scores": [],
        "analysis": "Lỗi dữ liệu JSON"
    }
