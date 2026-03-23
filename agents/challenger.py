"""
Challenger Agent — Argues that the news is FAKE.
Adapts behavior based on search mode (with/without search).
"""

from langchain_core.messages import HumanMessage

from prompts.templates import (
    CHALLENGER_PROMPT_WITH_SEARCH,
    CHALLENGER_PROMPT_NO_SEARCH,
    DEBATER_REBUTTAL_CONTEXT_WITH_SEARCH,
    DEBATER_REBUTTAL_CONTEXT_NO_SEARCH,
)
from agents.defender import format_evidence, format_debate_history, extract_search_queries
from config.settings import config


def challenge(state: dict, llm) -> dict:
    """
    Generate Challenger's argument for the current round.
    
    Round 1: Initial argument based on evidence (or logic only).
    Round 2+: Rebuttal + defense based on opponent's previous argument.
    """
    current_round = state.get("current_round", 1)
    claims_text = "\n".join(f"- {c}" for c in state.get("claims", []))
    enable_search = config.debate.enable_search

    # Choose prompt based on search mode
    if enable_search:
        evidence_text = format_evidence(state.get("search_results", []))
        rebuttal_template = DEBATER_REBUTTAL_CONTEXT_WITH_SEARCH
    else:
        evidence_text = None
        rebuttal_template = DEBATER_REBUTTAL_CONTEXT_NO_SEARCH

    # Build debate context
    if current_round > 1:
        opponent_arg = state.get("current_defender_argument", "")
        history = format_debate_history(state.get("debate_history", []))
        moderator = state.get("moderator_ruling", "")
        debate_context = rebuttal_template.format(
            round_number=current_round,
            opponent_argument=opponent_arg,
            debate_history=history,
            moderator_ruling=moderator if moderator else "(Chưa có phán quyết Moderator)",
        )
    else:
        # Vòng 1: Challenger đọc lập luận Defender vừa đưa
        defender_arg = state.get("current_defender_argument", "")
        debate_context = (
            f"(Đây là vòng đầu tiên)\n"
            f"Lập luận của Defender:\n{defender_arg}"
        )

    # Build prompt
    if enable_search:
        prompt = CHALLENGER_PROMPT_WITH_SEARCH.format(
            original_news=state["original_news"],
            claims=claims_text,
            evidence=evidence_text,
            debate_context=debate_context,
        )
    else:
        prompt = CHALLENGER_PROMPT_NO_SEARCH.format(
            original_news=state["original_news"],
            claims=claims_text,
            debate_context=debate_context,
        )

    response = llm.invoke([HumanMessage(content=prompt)])
    argument = response.content.strip()

    # Extract search queries only if search is enabled
    search_queries = extract_search_queries(argument) if enable_search else []

    return {
        "current_challenger_argument": argument,
        "pending_search_queries": search_queries,
    }
