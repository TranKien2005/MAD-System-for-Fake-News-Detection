"""
LangGraph Workflow — Connects all agents into the structured debate flow.

Flow:
  START → direct_search_news → score_sources →
  [loop: ask_defender → search → score → defender(speak) →
         ask_challenger → search → score → challenger(speak) →
         save_round → evaluator] →
  judge → END
"""

from langgraph.graph import StateGraph, END

from graph.state import MADState
from agents.search_agent import (
    extract_queries_and_search_initial,
    search_adaptive_evidence
)
from agents.defender import defend, defend_ask
from agents.challenger import challenge, challenge_ask
from agents.evaluator import evaluate_round, score_sources
from agents.judge import judge
from config.settings import config


def build_workflow(llm_main, llm_light):
    """
    Build and compile the LangGraph workflow.

    Args:
        llm_main: LLM for complex agents (Defender, Challenger, Judge, Evaluator)
        llm_light: LLM for simple agents (Search Agent, Investigator)

    Returns:
        Compiled LangGraph app
    """

    # --- Node functions ---

    def node_direct_search_news(state: MADState) -> dict:
        print("\n🔍 [Round 0] Đang tìm kiếm bằng chứng trực tiếp từ tin tức...")
        result = extract_queries_and_search_initial(state, llm_light)
        return result

    def node_ask_defender(state: MADState) -> dict:
        print(f"\n🧠 [Defender] Đang phân tích nhu cầu bằng chứng...")
        result = defend_ask(state, llm_light)
        queries = result.get("pending_search_queries", [])
        if queries:
            print(f"   → Defender yêu cầu {len(queries)} tìm kiếm mới: {', '.join(queries)}")
        return {**result, "active_side": "DEFENDER"}

    def node_ask_challenger(state: MADState) -> dict:
        print(f"\n🧠 [Challenger] Đang phân tích nhu cầu bằng chứng...")
        result = challenge_ask(state, llm_light)
        queries = result.get("pending_search_queries", [])
        if queries:
            print(f"   → Challenger yêu cầu {len(queries)} tìm kiếm mới: {', '.join(queries)}")
        return {**result, "active_side": "CHALLENGER"}

    def node_adaptive_search(state: MADState) -> dict:
        return search_adaptive_evidence(state)

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
        }
        print(f"\n💾 [Save] Lưu kết quả vòng {current_round}")
        return {
            "debate_history": [round_data],
            "current_round": current_round + 1,
        }

    def node_evaluator(state: MADState) -> dict:
        """Evaluator evaluates the round and rules on claims."""
        round_num = state.get("current_round", 1) - 1
        print(f"\n⚖️ [Evaluator - Vòng {round_num}] Đang đánh giá nhận định...")
        result = evaluate_round(state, llm_main)
        rulings = result.get("evaluator_rulings", [{}])
        if rulings:
            verifications = rulings[0].get("point_verifications", [])
            for v in verifications:
                status = v.get("status", "UNCERTAIN")
                symbol = {"VERIFIED": "✅", "DEBUNKED": "❌"}.get(status, "🔄")
                print(f"   {symbol} {v.get('point_id', '?')}: {status}")
        return result

    def node_score_sources(state: MADState) -> dict:
        """Evaluates trust scores of newly discovered sources."""
        return score_sources(state, llm_main)

    def node_judge(state: MADState) -> dict:
        print("\n⚖️  [Judge] Đang tính điểm và đưa ra phán quyết...")
        result = judge(state, llm_main)
        verdict = result.get("verdict", {})
        print(f"   → Verdict: {verdict.get('verdict', 'N/A')}")
        print(f"   → Confidence: {verdict.get('confidence', 'N/A')}%")
        print(f"   → Defender weighted score: {verdict.get('defender_weighted_avg', 'N/A')}")
        print(f"   → Challenger weighted score: {verdict.get('challenger_weighted_avg', 'N/A')}")
        return result

    # --- Conditional edges ---

    def has_search_queries(state: MADState) -> str:
        """Check if there are pending queries to execute search."""
        if state.get("pending_search_queries"):
            return "search"
        return "skip"

    def should_continue_debate(state: MADState) -> str:
        """Check if debate should continue or go to judge."""
        current_round = state.get("current_round", 1)
        max_rounds = state.get("max_rounds", config.debate.max_rounds)

        if current_round > max_rounds:
            print(f"\n🏁 Đã kết thúc {max_rounds} vòng — chuyển sang Judge")
            return "judge"
        else:
            print(f"\n🔄 Bắt đầu vòng tiếp theo ({current_round}/{max_rounds})")
            return "continue"

    # --- Build Graph ---

    workflow = StateGraph(MADState)

    # Add nodes — score_sources is split into 3 to avoid ambiguous routing
    workflow.add_node("direct_search_news", node_direct_search_news)
    workflow.add_node("score_initial", node_score_sources)
    workflow.add_node("ask_defender", node_ask_defender)
    workflow.add_node("search_defender", node_adaptive_search)
    workflow.add_node("score_def", node_score_sources)
    workflow.add_node("defender", node_defender)
    workflow.add_node("ask_challenger", node_ask_challenger)
    workflow.add_node("search_challenger", node_adaptive_search)
    workflow.add_node("score_chal", node_score_sources)
    workflow.add_node("challenger", node_challenger)
    workflow.add_node("save_round", node_save_round)
    workflow.add_node("evaluator", node_evaluator)
    workflow.add_node("judge", node_judge)

    # Set entry point
    workflow.set_entry_point("direct_search_news")

    # Initial search -> score -> Defender's turn
    workflow.add_edge("direct_search_news", "score_initial")
    workflow.add_edge("score_initial", "ask_defender")
    
    # Defender Turn: Ask -> (Search -> Score) or Skip -> Speak
    workflow.add_conditional_edges(
        "ask_defender",
        has_search_queries,
        {
            "search": "search_defender",
            "skip": "defender"
        }
    )
    workflow.add_edge("search_defender", "score_def")
    workflow.add_edge("score_def", "defender")
    
    # Defender speaks -> Challenger's turn
    workflow.add_edge("defender", "ask_challenger")
    workflow.add_conditional_edges(
        "ask_challenger",
        has_search_queries,
        {
            "search": "search_challenger",
            "skip": "challenger"
        }
    )
    workflow.add_edge("search_challenger", "score_chal")
    workflow.add_edge("score_chal", "challenger")

    # End of round
    workflow.add_edge("challenger", "save_round")
    workflow.add_edge("save_round", "evaluator")

    # Continue or judge
    workflow.add_conditional_edges(
        "evaluator",
        should_continue_debate,
        {
            "continue": "ask_defender",
            "judge": "judge",
        }
    )

    workflow.add_edge("judge", END)

    # Compile
    app = workflow.compile()
    return app

