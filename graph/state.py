"""
LangGraph State definition for the MAD System.
This state is shared across all nodes in the graph.
"""

from typing import Annotated
from typing_extensions import TypedDict
from config.settings import config


def add_to_list(current: list, new: list) -> list:
    """Reducer: append new items to existing list."""
    return current + new


def update_dict(current: dict, new: dict) -> dict:
    """Reducer: merge new dictionary into existing one."""
    if current is None: current = {}
    if new is None: return current
    return {**current, **new}


def last_value_reducer(current: any, new: any) -> any:
    """Reducer: keep only the latest value."""
    return new


class KnowledgeEntry(TypedDict):
    """A search result stored in the shared knowledge base."""
    id: str
    query: str
    query_language: str
    title: str
    content: str
    source_url: str
    domain: str
    relevance_score: float
    retrieval_provider: str
    retrieval_language: str
    rank_within_query_language: int


class DebateRound(TypedDict):
    """A single round of debate."""
    round_number: int
    defender_argument: str
    challenger_argument: str
    defender_claims: list[dict]
    challenger_claims: list[dict]


class MADState(TypedDict):
    """Main state for the Multi-Agent Debate workflow."""

    # --- Input ---
    original_news: str
    initial_context: str | None

    # --- Version ---
    state_version: int

    # --- Knowledge Base ---
    knowledge_base: Annotated[list[KnowledgeEntry], add_to_list]
    source_scores: Annotated[dict[str, float], update_dict]

    # --- Search ---
    pending_search_queries: Annotated[list[dict], last_value_reducer]
    pending_search_requests: Annotated[list[dict], last_value_reducer]
    executed_queries: Annotated[list[str], add_to_list]
    round_retrieval_plan: Annotated[list[dict], last_value_reducer]
    round_search_results: Annotated[list[dict], last_value_reducer]

    # --- Claim Context ---
    claim_contexts: Annotated[dict[str, list[str]], update_dict]
    focused_targets: Annotated[dict[str, dict], update_dict]

    # --- Debate ---
    debate_mode: str # "search" or "non_search"
    current_round: int
    max_rounds: int
    debate_history: Annotated[list[DebateRound], add_to_list]
    claims_registry: Annotated[dict[str, list[dict]], update_dict]
    current_defender_argument: Annotated[str, last_value_reducer]
    current_challenger_argument: Annotated[str, last_value_reducer]
    current_defender_claims: Annotated[list[dict], last_value_reducer]
    current_challenger_claims: Annotated[list[dict], last_value_reducer]
 
    # --- Evaluator ---
    evaluator_rulings: Annotated[list[dict], add_to_list]
 
    # --- Status ---
    active_side: Annotated[str, last_value_reducer]
    verdict: Annotated[dict | None, last_value_reducer]

    # Các thuộc tính phụ trợ phục vụ benchmarking/test
    custom_output_instructions: str | None


def build_initial_state(
    news_text: str, 
    initial_context: str | None = None,
    debate_mode: str = "search",
    max_rounds: int | None = None, 
    custom_output_instructions: str | None = None
) -> MADState:
    """Build a consistent initial state used by both CLI and UI entry points."""
    resolved_rounds = max_rounds if max_rounds is not None else config.debate.max_rounds
    return {
        "original_news": news_text,
        "initial_context": initial_context,
        "state_version": 2,
        "knowledge_base": [],
        "source_scores": {},
        "pending_search_queries": [],
        "pending_search_requests": [],
        "executed_queries": [],
        "round_retrieval_plan": [],
        "round_search_results": [],
        "claim_contexts": {},
        "focused_targets": {},
        "active_side": "DEFENDER",
        "debate_mode": debate_mode,
        "current_round": 1,
        "max_rounds": resolved_rounds,
        "debate_history": [],
        "claims_registry": {},
        "current_defender_argument": "",
        "current_challenger_argument": "",
        "current_defender_claims": [],
        "current_challenger_claims": [],
        "evaluator_rulings": [],
        "verdict": None,
        "custom_output_instructions": custom_output_instructions,
    }


def ensure_state_defaults(state: dict) -> MADState:
    """Backfill missing keys so legacy callers can still run under the new schema."""
    merged = build_initial_state(
        news_text=state.get("original_news", ""),
        initial_context=state.get("initial_context"),
        debate_mode=state.get("debate_mode", "search"),
        max_rounds=state.get("max_rounds", config.debate.max_rounds),
    )
    merged.update(state)

    pending = merged.get("pending_search_queries", [])
    if pending and isinstance(pending[0], str):
        merged["pending_search_queries"] = [
            {
                "query": q,
                "language": "auto",
                "intent": "verify",
                "target_claim_ids": [],
            }
            for q in pending
        ]

    if "pending_search_requests" not in merged:
        merged["pending_search_requests"] = []
    if "focused_targets" not in merged:
        merged["focused_targets"] = {}

    return merged  # type: ignore[return-value]
