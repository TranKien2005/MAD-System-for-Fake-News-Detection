"""
Defender Agent — Argues that the news is REAL.
Phase 1 (Ask): Decides what info to search for.
Phase 2 (Speak): Builds arguments using all available evidence.
"""

from langchain_core.messages import HumanMessage

from prompts.templates import (
    DEFENDER_ROUND1_PROMPT,
    DEFENDER_REBUTTAL_PROMPT,
    DEFENDER_ASK_PROMPT,
)
from agents.evaluator import parse_json_robust, format_evaluator_summary, _format_knowledge_base


def defend_ask(state: dict, llm) -> dict:
    """Phase 1: Defender analyzes the situation and requests search queries."""
    news_text = state["original_news"]
    history_text = _format_debate_history(state.get("debate_history", []))
    executed = str(state.get("executed_queries", []))
    
    prompt = DEFENDER_ASK_PROMPT.format(
        original_news=news_text,
        debate_history=history_text,
        executed_queries=executed
    )
    
    response = llm.invoke([HumanMessage(content=prompt)])
    data = parse_json_robust(response.content)
    
    return {"pending_search_queries": data.get("pending_search_queries", [])}


def defend(state: dict, llm) -> dict:
    """Phase 2: Defender speaks using all available info from KB."""
    news_text = state["original_news"]
    current_round = state.get("current_round", 1)
    kb_text = _format_knowledge_base(state.get("knowledge_base", []), state.get("source_scores", {}))
    debate_history = state.get("debate_history", [])

    if current_round == 1:
        # Round 1: Initial statements — independent, no rebuttal
        prompt = DEFENDER_ROUND1_PROMPT.format(
            original_news=news_text,
            knowledge_base_with_scores=kb_text,
        )
    else:
        # Round 2+: Rebuttals — respond to Challenger's PREVIOUS round
        eval_summary = format_evaluator_summary(state.get("evaluator_rulings", []))
        opponent_last = _get_opponent_last_argument(debate_history, "challenger")
        history_text = _format_debate_history(debate_history)

        prompt = DEFENDER_REBUTTAL_PROMPT.format(
            original_news=news_text,
            knowledge_base_with_scores=kb_text,
            round_number=current_round,
            opponent_last_argument=opponent_last,
            debate_history=history_text,
            evaluator_summary=eval_summary,
        )

    response = llm.invoke([HumanMessage(content=prompt)])
    argument = response.content.strip()

    return {
        "current_defender_argument": argument,
    }


def _get_opponent_last_argument(debate_history: list, opponent: str) -> str:
    """Get the opponent's argument from the last completed round."""
    if not debate_history:
        return "(Chưa có lập luận từ đối phương)"
    last_round = debate_history[-1]
    key = "challenger_argument" if opponent == "challenger" else "defender_argument"
    return last_round.get(key, "(Chưa có)")


def _format_debate_history(debate_history: list) -> str:
    """Format previous debate rounds — full text, no truncation."""
    if not debate_history:
        return "(Chưa có lịch sử tranh luận)"

    lines = ["\n#### Lịch sử tranh luận:"]
    for r in debate_history:
        lines.append(f"\n{'='*40}")
        lines.append(f"Vòng {r['round_number']}:")
        lines.append(f"{'='*40}")
        lines.append(f"📗 DEFENDER:\n{r['defender_argument']}")
        lines.append(f"\n📕 CHALLENGER:\n{r['challenger_argument']}")
    return "\n".join(lines)
