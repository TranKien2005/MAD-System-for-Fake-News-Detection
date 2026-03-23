"""
LangGraph Workflow — Connects all agents into a debate flow.

Flow (no search):
  START → claim_parser → defender → challenger → save_round → moderator
  → [loop: defender → challenger → save_round → moderator] → judge → END

Flow (with search):
  START → claim_parser → initial_search → defender → challenger → save_round → moderator
  → [loop: adaptive_search → defender → challenger → save_round → moderator] → judge → END
"""

from langgraph.graph import StateGraph, END

from graph.state import MADState
from agents.claim_parser import parse_claims
from agents.search_agent import search_evidence
from agents.defender import defend
from agents.challenger import challenge
from agents.judge import judge
from agents.moderator import moderate
from config.settings import config


def build_workflow(llm_main, llm_light):
    """
    Build and compile the LangGraph workflow.
    
    Args:
        llm_main: LLM for complex agents (Defender, Challenger, Judge, Moderator)
        llm_light: LLM for simple agents (Claim Parser, Search)
    
    Returns:
        Compiled LangGraph app
    """

    # --- Node functions (wrap agents with LLM) ---

    def node_claim_parser(state: MADState) -> dict:
        print("\n🔍 [Claim Parser] Đang trích xuất claims...")
        result = parse_claims(state, llm_light)
        print(f"   → Tìm thấy {len(result['claims'])} claims")
        for i, c in enumerate(result["claims"], 1):
            print(f"   {i}. {c}")
        return result

    def node_initial_search(state: MADState) -> dict:
        print("\n🌐 [Search Agent] Đang tìm kiếm thông tin ban đầu...")
        result = search_evidence(
            state, llm_light,
            enable_search=config.debate.enable_search
        )
        print(f"   → Tìm thấy {len(result['search_results'])} kết quả")
        return result

    def node_defender(state: MADState) -> dict:
        round_num = state.get("current_round", 1)
        print(f"\n✅ [Defender - Vòng {round_num}] Đang lập luận...")
        result = defend(state, llm_main)
        print(f"   → Đã đưa ra lập luận ({len(result['current_defender_argument'])} chars)")
        return result

    def node_challenger(state: MADState) -> dict:
        round_num = state.get("current_round", 1)
        print(f"\n❌ [Challenger - Vòng {round_num}] Đang phản biện...")
        result = challenge(state, llm_main)
        print(f"   → Đã đưa ra lập luận ({len(result['current_challenger_argument'])} chars)")
        return result

    def node_save_round(state: MADState) -> dict:
        """Save current round to debate history and increment round counter."""
        current_round = state.get("current_round", 1)
        round_data = {
            "round_number": current_round,
            "defender_argument": state.get("current_defender_argument", ""),
            "challenger_argument": state.get("current_challenger_argument", ""),
            "search_queries_used": state.get("pending_search_queries", []),
        }
        print(f"\n💾 [Save] Lưu kết quả vòng {current_round}")
        return {
            "debate_history": [round_data],
            "current_round": current_round + 1,
        }

    def node_moderator(state: MADState) -> dict:
        """Moderator evaluates the round and makes rulings."""
        round_num = state.get("current_round", 1) - 1
        print(f"\n⚖️ [Moderator - Vòng {round_num}] Đang đánh giá vòng tranh luận...")
        result = moderate(state, llm_main)
        print(f"   → Đã đưa ra phán quyết vòng {round_num}")
        return result

    def node_adaptive_search(state: MADState) -> dict:
        """Search based on debater requests between rounds."""
        pending = state.get("pending_search_queries", [])
        if pending:
            print(f"\n🔄 [Adaptive Search] Tìm thêm {len(pending)} query...")
            result = search_evidence(
                state, llm_light,
                enable_search=config.debate.enable_search
            )
            return result
        return {"search_results": [], "pending_search_queries": []}

    def node_judge(state: MADState) -> dict:
        print("\n⚖️  [Judge] Đang đánh giá toàn bộ cuộc tranh luận...")
        result = judge(state, llm_main)
        verdict = result.get("verdict", {})
        print(f"   → Verdict: {verdict.get('verdict', 'N/A')}")
        print(f"   → Confidence: {verdict.get('confidence', 'N/A')}%")
        return result

    # --- Conditional edges ---

    def should_continue_debate(state: MADState) -> str:
        """Check if debate should continue or go to judge."""
        current_round = state.get("current_round", 1)
        max_rounds = state.get("max_rounds", config.debate.max_rounds)

        if current_round > max_rounds:
            print(f"\n🏁 Đã đạt {max_rounds} vòng — chuyển sang Judge")
            return "judge"
        else:
            print(f"\n🔄 Tiếp tục vòng {current_round}/{max_rounds}")
            return "continue"

    # --- Build Graph ---

    workflow = StateGraph(MADState)

    # Add nodes (always present)
    workflow.add_node("claim_parser", node_claim_parser)
    workflow.add_node("defender", node_defender)
    workflow.add_node("challenger", node_challenger)
    workflow.add_node("save_round", node_save_round)
    workflow.add_node("moderator", node_moderator)
    workflow.add_node("judge", node_judge)

    # Set entry point
    workflow.set_entry_point("claim_parser")

    # Common edges for both modes
    workflow.add_edge("defender", "challenger")
    workflow.add_edge("challenger", "save_round")
    workflow.add_edge("save_round", "moderator")

    # Moderator decides: continue debate or go to judge
    workflow.add_conditional_edges(
        "moderator",
        should_continue_debate,
        {
            "continue": "adaptive_search" if config.debate.enable_search else "defender",
            "judge": "judge",
        }
    )

    if config.debate.enable_search:
        # WITH SEARCH
        workflow.add_node("initial_search", node_initial_search)
        workflow.add_node("adaptive_search", node_adaptive_search)

        workflow.add_edge("claim_parser", "initial_search")
        workflow.add_edge("initial_search", "defender")
        workflow.add_edge("adaptive_search", "defender")
    else:
        # NO SEARCH
        workflow.add_edge("claim_parser", "defender")

    workflow.add_edge("judge", END)

    # Compile
    app = workflow.compile()

    return app
