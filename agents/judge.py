"""Judge agent (qualitative-first final verdict)."""

import json

from langchain_core.messages import HumanMessage

from prompts.templates import JUDGE_PROMPT
from agents.evaluator import format_knowledge_base


def judge(state: dict, llm) -> dict:
    kb_text = format_knowledge_base(state.get("knowledge_base", []), state.get("source_scores", {}))

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


def _format_full_debate_with_evaluator(debate_history: list, evaluator_rulings: list) -> str:
    if not debate_history:
        return "(Không có lịch sử tranh luận)"

    rulings_by_round = {}
    for ruling in evaluator_rulings:
        r_num = ruling.get("round_number", 0)
        rulings_by_round[r_num] = ruling

    lines = []
    for r in debate_history:
        r_num = r["round_number"]
        lines.append(f"\n{'=' * 60}")
        lines.append(f"VÒNG {r_num}")
        lines.append(f"{'=' * 60}")
        lines.append("\n📗 DEFENDER:")
        lines.append(r["defender_argument"])
        lines.append("\n📕 CHALLENGER:")
        lines.append(r["challenger_argument"])

        if r_num in rulings_by_round:
            ruling = rulings_by_round[r_num]
            lines.append(f"\n⚖️ THẨM ĐỊNH SAU VÒNG {r_num}:")
            for d in ruling.get("claim_decisions", []):
                lines.append(
                    f"- {d.get('claim_id', '?')}: {d.get('status', 'ACTIVE')} | "
                    f"{d.get('closure_reason', '')}"
                )

            summary = ruling.get("round_summary", "")
            if summary:
                lines.append(f"  📝 Tóm tắt: {summary}")

    return "\n".join(lines)


def _parse_verdict(raw_text: str) -> dict:
    text = raw_text.strip()

    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                data = json.loads(text[start:end])
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}

    truth_score = data.get("truth_score", 0.5)
    try:
        truth_score = float(truth_score)
    except (ValueError, TypeError):
        truth_score = 0.5
        
    points = data.get("top_3_decisive_points", [])
    reasoning = data.get("final_reasoning", "Không thể parse đầy đủ kết quả Judge.")

    if not isinstance(points, list):
        points = []

    return {
        "truth_score": truth_score,
        "top_3_decisive_points": points[:3],
        "final_reasoning": reasoning,
    }
