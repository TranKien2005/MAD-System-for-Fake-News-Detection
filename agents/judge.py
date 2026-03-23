"""
Judge Agent — Evaluates the entire debate and delivers a final verdict.
Adapts evaluation based on search mode.
"""

import json

from langchain_core.messages import HumanMessage

from prompts.templates import JUDGE_PROMPT, JUDGE_SEARCH_NOTE, JUDGE_NO_SEARCH_NOTE
from config.settings import config


def judge(state: dict, llm) -> dict:
    """
    Evaluate the full debate history and produce a final verdict.
    """
    claims_text = "\n".join(f"- {c}" for c in state.get("claims", []))
    debate_history = _format_full_debate(state.get("debate_history", []))

    # Choose search mode note
    search_note = JUDGE_SEARCH_NOTE if config.debate.enable_search else JUDGE_NO_SEARCH_NOTE

    prompt = JUDGE_PROMPT.format(
        original_news=state["original_news"],
        claims=claims_text,
        full_debate_history=debate_history,
        search_mode_note=search_note,
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    verdict = _parse_verdict(response.content)

    return {"verdict": verdict}


def _format_full_debate(debate_history: list) -> str:
    """Format the complete debate history for Judge review."""
    if not debate_history:
        return "(Không có lịch sử tranh luận)"

    lines = []
    for r in debate_history:
        lines.append(f"\n{'='*60}")
        lines.append(f"VÒNG {r['round_number']}")
        lines.append(f"{'='*60}")
        lines.append(f"\n📗 DEFENDER:")
        lines.append(r["defender_argument"])
        lines.append(f"\n📕 CHALLENGER:")
        lines.append(r["challenger_argument"])

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
        "reasoning": f"Không thể parse kết quả Judge. Raw output: {raw_text[:500]}",
        "key_evidence": [],
        "defender_score": {},
        "challenger_score": {},
    }
