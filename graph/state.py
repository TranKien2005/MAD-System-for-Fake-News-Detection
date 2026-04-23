"""
LangGraph State definition for the MAD System.
This state is shared across all nodes in the graph.
"""

from typing import Annotated
from typing_extensions import TypedDict


def add_to_list(current: list, new: list) -> list:
    """Reducer: append new items to existing list."""
    return current + new


def update_dict(current: dict, new: dict) -> dict:
    """Reducer: merge new dictionary into existing one."""
    return {**current, **new}


class KnowledgeEntry(TypedDict):
    """A search result stored in the shared knowledge base."""
    id: str
    query: str
    title: str
    content: str
    source_url: str
    domain: str
    relevance_score: float


class DebateRound(TypedDict):
    """A single round of debate."""
    round_number: int
    defender_argument: str
    challenger_argument: str


class MADState(TypedDict):
    """Main state for the Multi-Agent Debate workflow."""

    # --- Input ---
    original_news: str                                    # Tin tức gốc

    # --- Knowledge Base ---
    knowledge_base: Annotated[list[KnowledgeEntry], add_to_list]
    source_scores: Annotated[dict[str, float], update_dict] # { "[S1]": 1.0, ... }

    # --- Search ---
    pending_search_queries: list[str]
    executed_queries: Annotated[list[str], add_to_list]   # Các query đã thực hiện

    # --- Debate ---
    current_round: int                                    # Vòng hiện tại
    max_rounds: int                                       # Số vòng tối đa
    debate_history: Annotated[list[DebateRound], add_to_list]

    # --- Current round arguments ---
    current_defender_argument: str
    current_challenger_argument: str

    # --- Evaluator ---
    evaluator_rulings: Annotated[list[dict], add_to_list]  # One ruling per round

    # --- Status ---
    active_side: str                                      # Bên đang thực hiện (DEFENDER/CHALLENGER)
    verdict: dict | None                                  # Phán quyết cuối cùng
