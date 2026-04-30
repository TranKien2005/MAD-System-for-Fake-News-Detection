"""Judge agent (qualitative-first final verdict)."""

import json
from typing import Any

from langchain_core.messages import HumanMessage

from prompts.templates import JUDGE_PROMPT_BASE, DEFAULT_JUDGE_OUTPUT_INSTRUCTIONS
from agents.evaluator import format_knowledge_base


def judge(state: dict, llm) -> dict:
    kb_text = format_knowledge_base(state.get("knowledge_base", []), state.get("source_scores", {}))

    full_history = _format_full_debate_with_evaluator(
        state.get("debate_history", []),
        state.get("evaluator_rulings", []),
    )

    output_instructions = state.get("custom_output_instructions") or DEFAULT_JUDGE_OUTPUT_INSTRUCTIONS

    prompt = JUDGE_PROMPT_BASE.format(
        original_news=state["original_news"],
        knowledge_base=kb_text,
        full_debate_with_evaluator=full_history,
        output_format_instructions=output_instructions
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


def _parse_verdict(raw_text: Any) -> dict:
    if isinstance(raw_text, list):
        text = "".join([c.get("text", "") for c in raw_text if isinstance(c, dict)])
    else:
        text = str(raw_text)
        
    text = text.strip()

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
                raise ValueError(f"Không thể parse JSON từ kết quả của Judge: {text}")
        else:
            raise ValueError(f"Không tìm thấy JSON trong kết quả của Judge: {text}")

    # Trích xuất truth_score (BẮT BUỘC)
    if "truth_score" not in data:
        raise ValueError(f"Kết quả của Judge thiếu trường 'truth_score': {data}")
        
    try:
        data["truth_score"] = float(data["truth_score"])
    except (ValueError, TypeError):
        raise ValueError(f"Giá trị 'truth_score' của Judge không hợp lệ: {data.get('truth_score')}")
        
    return data
