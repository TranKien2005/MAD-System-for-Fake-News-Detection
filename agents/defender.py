"""
Defender Agent — Argues that the news is REAL.
Adapts behavior based on search mode (with/without search).
"""

from langchain_core.messages import HumanMessage

from prompts.templates import (
    DEFENDER_PROMPT_WITH_SEARCH,
    DEFENDER_PROMPT_NO_SEARCH,
    DEBATER_REBUTTAL_CONTEXT_WITH_SEARCH,
    DEBATER_REBUTTAL_CONTEXT_NO_SEARCH,
)
from config.settings import config


def defend(state: dict, llm) -> dict:
    """
    Generate Defender's argument for the current round.
    
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
        opponent_arg = state.get("current_challenger_argument", "")
        history = format_debate_history(state.get("debate_history", []))
        moderator = state.get("moderator_ruling", "")
        debate_context = rebuttal_template.format(
            round_number=current_round,
            opponent_argument=opponent_arg,
            debate_history=history,
            moderator_ruling=moderator if moderator else "(Chưa có phán quyết Moderator)",
        )
    else:
        debate_context = "(Đây là vòng đầu tiên — hãy đưa ra lập luận mở đầu)"

    # Build prompt
    if enable_search:
        prompt = DEFENDER_PROMPT_WITH_SEARCH.format(
            original_news=state["original_news"],
            claims=claims_text,
            evidence=evidence_text,
            debate_context=debate_context,
        )
    else:
        prompt = DEFENDER_PROMPT_NO_SEARCH.format(
            original_news=state["original_news"],
            claims=claims_text,
            debate_context=debate_context,
        )

    response = llm.invoke([HumanMessage(content=prompt)])
    argument = response.content.strip()

    # Extract search queries only if search is enabled
    search_queries = extract_search_queries(argument) if enable_search else []

    return {
        "current_defender_argument": argument,
        "pending_search_queries": search_queries,
    }


def format_evidence(search_results: list) -> str:
    """Format search results as readable evidence."""
    if not search_results:
        return "(Chưa có evidence)"

    lines = []
    for r in search_results:
        lines.append(
            f"- [{r.get('title', 'N/A')}] ({r.get('domain', 'N/A')}, "
            f"credibility: {r.get('credibility_score', 0):.1f} — "
            f"{r.get('credibility_label', 'N/A')}): {r.get('content', '')}"
        )
    return "\n".join(lines)


def format_debate_history(debate_history: list) -> str:
    """Format previous debate rounds."""
    if not debate_history:
        return "(Chưa có lịch sử tranh luận)"

    lines = []
    for r in debate_history:
        lines.append(f"\n=== VÒNG {r['round_number']} ===")
        lines.append(f"DEFENDER: {r['defender_argument'][:500]}...")
        lines.append(f"CHALLENGER: {r['challenger_argument'][:500]}...")
    return "\n".join(lines)


def extract_search_queries(argument: str) -> list[str]:
    """Extract search queries from the agent's response."""
    queries = []
    in_search_section = False

    for line in argument.split("\n"):
        line = line.strip()
        if "YÊU CẦU TÌM THÊM" in line:
            in_search_section = True
            continue
        if in_search_section and line and "không cần" not in line.lower():
            query = line.lstrip("- ").strip()
            if query and not query.startswith("#"):
                queries.append(query)

    return queries
