"""
LangGraph Workflow — round-based debate with search at round start.
"""

from langgraph.graph import StateGraph, END

from graph.state import MADState, ensure_state_defaults
from agents.search_agent import plan_round_queries, search_round_evidence
from agents.defender import defend
from agents.challenger import challenge
from agents.evaluator import evaluate_round, score_sources
from agents.judge import judge
from config.settings import config


def build_workflow(llm_main, llm_light):
    """Build and compile the LangGraph workflow."""

    def node_prepare_round(state: MADState) -> dict:
        safe_state = ensure_state_defaults(state)
        round_num = safe_state.get("current_round", 1)
        print(f"\n🔎 [Round {round_num}] Lập kế hoạch truy vấn cho DEFENDER...")
        result = plan_round_queries(safe_state, llm_light, side="DEFENDER")
        result["active_side"] = "DEFENDER"
        return result

    def node_prepare_round_challenger(state: MADState) -> dict:
        safe_state = ensure_state_defaults(state)
        round_num = safe_state.get("current_round", 1)
        print(f"\n🔎 [Round {round_num}] Lập kế hoạch truy vấn cho CHALLENGER...")
        result = plan_round_queries(safe_state, llm_light, side="CHALLENGER")
        
        # Manually merge with Defender's requests since we removed the reducer
        existing = safe_state.get("pending_search_requests", [])
        result["pending_search_requests"] = existing + result.get("pending_search_requests", [])
        return result

    def node_search_defender(state: MADState) -> dict:
        safe_state = ensure_state_defaults(state)
        safe_state["active_side"] = "DEFENDER"
        round_num = safe_state.get("current_round", 1)
        print(f"\n🔍 [Round {round_num}] Tìm kiếm bằng chứng cho Defender...")
        return search_round_evidence(safe_state)

    def node_search_round(state: MADState) -> dict:
        safe_state = ensure_state_defaults(state)
        safe_state["active_side"] = "CHALLENGER"
        round_num = safe_state.get("current_round", 1)
        planned = [r for r in safe_state.get("pending_search_requests", []) if r.get("side") == "CHALLENGER"]
        print(f"\n🔍 [Round {round_num}] Tìm kiếm bằng chứng cho Challenger với {len(planned)} truy vấn...")
        return search_round_evidence(safe_state)

    def node_score_sources(state: MADState) -> dict:
        safe_state = ensure_state_defaults(state)
        return score_sources(safe_state, llm_main)

    def node_defender(state: MADState) -> dict:
        safe_state = ensure_state_defaults(state)
        round_num = safe_state.get("current_round", 1)
        print(f"\n✅ [Defender - Vòng {round_num}] Đang lập luận...")
        result = defend(safe_state, llm_main)
        result["active_side"] = "CHALLENGER"
        print(f"   → Đã đưa ra lập luận ({len(result['current_defender_argument'])} chars)")
        return result

    def node_challenger(state: MADState) -> dict:
        safe_state = ensure_state_defaults(state)
        round_num = safe_state.get("current_round", 1)
        print(f"\n❌ [Challenger - Vòng {round_num}] Đang phản biện...")
        result = challenge(safe_state, llm_main)
        print(f"   → Đã đưa ra lập luận ({len(result['current_challenger_argument'])} chars)")
        return result

    def node_save_round(state: MADState) -> dict:
        safe_state = ensure_state_defaults(state)
        current_round = safe_state.get("current_round", 1)
        round_data = {
            "round_number": current_round,
            "defender_argument": safe_state.get("current_defender_argument", ""),
            "challenger_argument": safe_state.get("current_challenger_argument", ""),
            "defender_claims": safe_state.get("current_defender_claims", []),
            "challenger_claims": safe_state.get("current_challenger_claims", []),
        }

        # Garbage Collection (GC): Xóa content của sources không được trích dẫn
        combined_args = f"{round_data['defender_argument']}\n{round_data['challenger_argument']}"
        for r in safe_state.get("debate_history", []):
            combined_args += f"\n{r.get('defender_argument', '')}\n{r.get('challenger_argument', '')}"

        kb = safe_state.get("knowledge_base", [])
        collected = 0
        for entry in kb:
            eid = entry.get("id", "")
            if eid and entry.get("content"):
                if f"[{eid}]" not in combined_args and eid not in combined_args:
                    entry["content"] = ""  # Xóa nội dung để tiết kiệm token
                    collected += 1
        
        if collected > 0:
            print(f"   🗑️ Đã dọn rác (GC): Xóa nội dung {collected} nguồn không được trích dẫn để tối ưu token.")

        print(f"\n💾 [Save] Lưu kết quả vòng {current_round}")
        return {
            "debate_history": [round_data],
            "current_defender_claims": [],
            "current_challenger_claims": [],
            "current_round": current_round + 1,
        }

    def node_evaluator(state: MADState) -> dict:
        safe_state = ensure_state_defaults(state)
        round_num = safe_state.get("current_round", 1) - 1
        print(f"\n⚖️ [Evaluator - Vòng {round_num}] Đang đánh giá nhận định...")
        result = evaluate_round(safe_state, llm_main)
        rulings = result.get("evaluator_rulings", [{}])
        if rulings:
            decisions = rulings[0].get("claim_decisions", [])
            for decision in decisions:
                status = decision.get("status", "ACTIVE")
                symbol = {
                    "RESOLVED_SUPPORTS_DEFENDER": "✅",
                    "RESOLVED_SUPPORTS_CHALLENGER": "❌",
                    "DROPPED": "🗑️",
                }.get(status, "🔄")
                print(f"   {symbol} {decision.get('claim_id', '?')}: {status}")
        return result

    def node_judge(state: MADState) -> dict:
        safe_state = ensure_state_defaults(state)
        print("\n⚖️  [Judge] Đang tổng hợp và đưa ra phán quyết...")
        result = judge(safe_state, llm_main)
        verdict = result.get("verdict", {})
        print(f"   → Winner: {verdict.get('winner', 'UNCERTAIN')}")
        print(f"   → Margin: {verdict.get('margin', 'low')}")
        print(f"   → Confidence: {verdict.get('confidence', 'N/A')}%")
        return result

    def should_continue_debate(state: MADState) -> str:
        safe_state = ensure_state_defaults(state)
        current_round = safe_state.get("current_round", 1)
        max_rounds = safe_state.get("max_rounds", config.debate.max_rounds)
        if current_round > max_rounds:
            print(f"\n🏁 Đã kết thúc {max_rounds} vòng — chuyển sang Judge")
            return "judge"
        print(f"\n🔄 Bắt đầu vòng tiếp theo ({current_round}/{max_rounds})")
        return "continue"

    workflow = StateGraph(MADState)

    workflow.add_node("prepare_round", node_prepare_round)
    workflow.add_node("prepare_round_challenger", node_prepare_round_challenger)
    workflow.add_node("search_defender", node_search_defender)
    workflow.add_node("search_round", node_search_round)
    workflow.add_node("score_sources", node_score_sources)
    workflow.add_node("defender", node_defender)
    workflow.add_node("challenger", node_challenger)
    workflow.add_node("save_round", node_save_round)
    workflow.add_node("judge", node_judge)

    workflow.set_entry_point("prepare_round")

    workflow.add_edge("prepare_round", "prepare_round_challenger")
    workflow.add_edge("prepare_round_challenger", "search_defender")
    workflow.add_edge("search_defender", "search_round")
    workflow.add_edge("search_round", "score_sources")
    workflow.add_edge("score_sources", "defender")
    workflow.add_edge("defender", "challenger")
    workflow.add_edge("challenger", "save_round")
    workflow.add_conditional_edges(
        "save_round",
        should_continue_debate,
        {
            "continue": "prepare_round",
            "judge": "judge",
        },
    )
    workflow.add_edge("judge", END)

    return workflow.compile()
