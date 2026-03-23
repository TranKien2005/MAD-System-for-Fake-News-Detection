"""
LangGraph State definition for the MAD System.
This state is shared across all nodes in the graph.
"""

from typing import Annotated
from typing_extensions import TypedDict


def add_to_list(current: list, new: list) -> list:
    """Reducer: append new items to existing list."""
    return current + new


class SearchResult(TypedDict):
    """A single search result with credibility info."""
    url: str
    title: str
    content: str
    domain: str
    credibility_score: float
    credibility_label: str


class DebateRound(TypedDict):
    """A single round of debate."""
    round_number: int
    defender_argument: str
    challenger_argument: str
    search_queries_used: list[str]


class JudgeVerdict(TypedDict):
    """Final verdict from the Judge agent."""
    verdict: str              # LIKELY_REAL / LIKELY_FAKE / UNCERTAIN
    confidence: float         # 0-100
    reasoning: str
    key_evidence: list[str]
    defender_score: dict
    challenger_score: dict


class MADState(TypedDict):
    """Main state for the Multi-Agent Debate workflow."""

    # --- Input ---
    original_news: str                                    # Tin tức gốc
    claims: list[str]                                     # Claims đã trích xuất

    # --- Search ---
    search_results: Annotated[list[SearchResult], add_to_list]  # Tất cả kết quả search
    pending_search_queries: list[str]                     # Query cần search tiếp

    # --- Debate ---
    current_round: int                                    # Vòng hiện tại
    max_rounds: int                                       # Số vòng tối đa
    debate_history: Annotated[list[DebateRound], add_to_list]   # Lịch sử tranh luận

    # --- Current round arguments ---
    current_defender_argument: str                        # Lập luận Defender vòng hiện tại
    current_challenger_argument: str                      # Lập luận Challenger vòng hiện tại
    moderator_ruling: str                                 # Phán quyết Moderator vòng trước

    # --- Judge ---
    verdict: JudgeVerdict | None                          # Phán quyết cuối cùng
