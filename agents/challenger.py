"""
Challenger Agent — Argues that the news is FAKE.
Phase 1 (Ask): Decides what info to search for.
Phase 2 (Speak): Builds arguments using all available evidence.
"""

from langchain_core.messages import HumanMessage

from prompts.templates import (
    CHALLENGER_ROUND1_PROMPT,
    CHALLENGER_REBUTTAL_PROMPT,
    CHALLENGER_ASK_PROMPT,
)
from agents.evaluator import format_evaluator_summary, _format_knowledge_base, parse_json_robust
from agents.defender import _format_debate_history, _get_opponent_last_argument


def challenge_ask(state: dict, llm) -> dict:
    """Phase 1: Challenger analyzes the situation and requests search queries."""
    news_text = state["original_news"]
    history_text = _format_debate_history(state.get("debate_history", []))
    executed = str(state.get("executed_queries", []))
    
    prompt = CHALLENGER_ASK_PROMPT.format(
        original_news=news_text,
        debate_history=history_text,
        executed_queries=executed
    )
    
    response = llm.invoke([HumanMessage(content=prompt)])
    data = parse_json_robust(response.content)
    
    return {"pending_search_queries": data.get("pending_search_queries", [])}


def challenge(state: dict, llm) -> dict:
    """Phase 2: Challenger speaks using all available info from KB.
    
    Key change: Challenger now responds to Defender's PREVIOUS round
    (from debate_history), NOT the current round's defender argument.
    This ensures both agents respond to the same previous round.
    """
    news_text = state["original_news"]
    current_round = state.get("current_round", 1)
    kb_text = _format_knowledge_base(state.get("knowledge_base", []), state.get("source_scores", {}))
    debate_history = state.get("debate_history", [])

    if current_round == 1:
        # Round 1: Initial statements — independent, no rebuttal
        prompt = CHALLENGER_ROUND1_PROMPT.format(
            original_news=news_text,
            knowledge_base_with_scores=kb_text,
        )
    else:
        # Round 2+: Rebuttals — respond to Defender's PREVIOUS round
        # Uses debate_history (not current_defender_argument) so both
        # agents respond to the same previous round's arguments.
        eval_summary = format_evaluator_summary(state.get("evaluator_rulings", []))
        opponent_last = _get_opponent_last_argument(debate_history, "defender")
        history_text = _format_debate_history(debate_history)

        prompt = CHALLENGER_REBUTTAL_PROMPT.format(
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
        "current_challenger_argument": argument,
    }
