"""
Moderator Agent — Evaluates each debate round and makes rulings on specific points.
Runs after each round to guide the next round of debate.
"""

import json

from langchain_core.messages import HumanMessage

from prompts.templates import MODERATOR_PROMPT


def moderate(state: dict, llm) -> dict:
    """
    Evaluate the current round and produce rulings on contested points.
    
    Returns moderator ruling to be passed to debaters in the next round.
    """
    claims_text = "\n".join(f"- {c}" for c in state.get("claims", []))
    current_round = state.get("current_round", 1) - 1  # save_round already incremented

    prompt = MODERATOR_PROMPT.format(
        original_news=state["original_news"],
        claims=claims_text,
        round_number=current_round,
        defender_argument=state.get("current_defender_argument", ""),
        challenger_argument=state.get("current_challenger_argument", ""),
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    ruling = _parse_moderator_ruling(response.content)

    # Format ruling as readable text for debaters
    ruling_text = _format_ruling_for_debaters(ruling, current_round)

    return {
        "moderator_ruling": ruling_text,
    }


def _parse_moderator_ruling(raw_text: str) -> dict:
    """Parse JSON ruling from Moderator's response."""
    text = raw_text.strip()

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
        "round_summary": "Moderator không thể phân tích vòng này.",
        "points_resolved": [],
        "points_still_contested": [],
        "guidance": raw_text[:300],
    }


def _format_ruling_for_debaters(ruling: dict, round_number: int) -> str:
    """Format moderator ruling as readable text for debaters."""
    lines = [f"⚖️ PHÁN QUYẾT CỦA MODERATOR SAU VÒNG {round_number}:"]
    lines.append(f"Tóm tắt: {ruling.get('round_summary', 'N/A')}")

    # Resolved points
    resolved = ruling.get("points_resolved", [])
    if resolved:
        lines.append("\n📌 Các điểm đã được phán quyết:")
        for p in resolved:
            winner = p.get("winner", "DRAW")
            point = p.get("point", "N/A")
            reason = p.get("reasoning", "")
            lines.append(f"  - {point} → Thắng: {winner}. {reason}")
            lines.append(f"    ⚠️ KHÔNG CẦN tranh luận lại điểm này.")

    # Still contested
    contested = ruling.get("points_still_contested", [])
    if contested:
        lines.append("\n🔄 Các điểm chưa giải quyết (cần tranh luận tiếp):")
        for p in contested:
            lines.append(f"  - {p}")

    guidance = ruling.get("guidance", "")
    if guidance:
        lines.append(f"\n💡 Hướng dẫn: {guidance}")

    return "\n".join(lines)
