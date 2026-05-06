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


def node_initialize_context(state: MADState) -> dict:
    """Populate KB with initial context as S1 (Trust: 1.0) if in non_search mode."""
    safe_state = ensure_state_defaults(state)
    if safe_state.get("debate_mode") == "non_search" and safe_state.get("initial_context"):
        entry = {
            "id": "[S1]",
            "query": "initial_context",
            "query_language": "auto",
            "title": "Bối cảnh cung cấp",
            "content": safe_state["initial_context"],
            "source_url": "user_provided",
            "domain": "internal",
            "relevance_score": 1.0,
            "retrieval_provider": "user",
            "retrieval_language": "auto",
            "rank_within_query_language": 1,
        }
        print(f"   ℹ️ [System] Đã nạp bối cảnh ban đầu làm nguồn [S1] (Trust: 1.0)")
        return {
            "knowledge_base": [entry],
            "source_scores": {"[S1]": 1.0}
        }
    return {}


def node_prepare_round(state: MADState, llm_light) -> dict:
    safe_state = ensure_state_defaults(state)
    round_num = safe_state.get("current_round", 1)
    
    print(f"\n🔎 [Round {round_num}] Lập kế hoạch truy vấn cho cả hai phe...")
    
    # Lập kế hoạch cho Defender
    def_res = plan_round_queries(safe_state, llm_light, side="DEFENDER")
    # Lập kế hoạch cho Challenger
    cha_res = plan_round_queries(safe_state, llm_light, side="CHALLENGER")
    
    # Gộp các yêu cầu tìm kiếm
    all_pending = def_res.get("pending_search_requests", []) + cha_res.get("pending_search_requests", [])
    
    return {
        "pending_search_requests": all_pending,
        "active_side": "DEFENDER" # Default
    }


def node_search_defender(state: MADState) -> dict:
    safe_state = ensure_state_defaults(state)
    safe_state["active_side"] = "DEFENDER"
    round_num = safe_state.get("current_round", 1)
    planned = [r for r in safe_state.get("pending_search_requests", []) if r.get("side") == "DEFENDER"]
    print(f"\n🔍 [Round {round_num}] Tìm kiếm bằng chứng cho Defender với {len(planned)} truy vấn...")
    return search_round_evidence(safe_state)


def node_search_round(state: MADState) -> dict:
    safe_state = ensure_state_defaults(state)
    safe_state["active_side"] = "CHALLENGER"
    round_num = safe_state.get("current_round", 1)
    planned = [r for r in safe_state.get("pending_search_requests", []) if r.get("side") == "CHALLENGER"]
    print(f"\n🔍 [Round {round_num}] Tìm kiếm bằng chứng cho Challenger với {len(planned)} truy vấn...")
    return search_round_evidence(safe_state)


def node_score_sources(state: MADState, llm_main) -> dict:
    safe_state = ensure_state_defaults(state)
    result = score_sources(safe_state, llm_main)
    # Dọn dẹp danh sách chờ sau khi đã tìm kiếm xong
    result["pending_search_requests"] = []
    result["pending_search_queries"] = []
    return result


def node_defender(state: MADState, llm_main) -> dict:
    safe_state = ensure_state_defaults(state)
    round_num = safe_state.get("current_round", 1)
    print(f"\n✅ [Defender - Vòng {round_num}] Đang lập luận...")
    result = defend(safe_state, llm_main)
    result["active_side"] = "CHALLENGER"
    print(f"   → Đã đưa ra lập luận ({len(result['current_defender_argument'])} chars)")
    return result


def node_challenger(state: MADState, llm_main) -> dict:
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
        # TUYỆT ĐỐI KHÔNG xóa nội dung của nguồn bối cảnh ban đầu [S1]
        if eid == "[S1]":
            continue
            
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


def node_evaluator(state: MADState, llm_main) -> dict:
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


def node_judge(state: MADState, llm_main) -> dict:
    safe_state = ensure_state_defaults(state)
    print("\n⚖️  [Judge] Đang tổng hợp và đưa ra phán quyết...")
    result = judge(safe_state, llm_main)
    verdict = result.get("verdict", {})
    for key, value in verdict.items():
        if not isinstance(value, (list, dict)):
            print(f"   → {key.title()}: {value}")
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


def build_workflow(llm):
    """
    Build the standard LangGraph workflow with search using a single LLM.
    """
    workflow = StateGraph(MADState)

    # Add nodes using the unified LLM
    workflow.add_node("prepare_round", lambda s: node_prepare_round(s, llm))
    workflow.add_node("search_defender", node_search_defender)
    workflow.add_node("search_round", node_search_round)
    workflow.add_node("score_sources", lambda s: node_score_sources(s, llm))
    workflow.add_node("defender", lambda s: node_defender(s, llm))
    workflow.add_node("challenger", lambda s: node_challenger(s, llm))
    workflow.add_node("save_round", node_save_round)
    workflow.add_node("judge", lambda s: node_judge(s, llm))

    # Define edges
    workflow.set_entry_point("prepare_round")
    workflow.add_edge("prepare_round", "search_defender")
    workflow.add_edge("prepare_round", "search_round")
    
    workflow.add_edge("search_defender", "score_sources")
    workflow.add_edge("search_round", "score_sources")
    
    workflow.add_edge("score_sources", "defender")
    workflow.add_edge("defender", "challenger")
    workflow.add_edge("challenger", "save_round")
    
    workflow.add_conditional_edges(
        "save_round",
        should_continue_debate,
        {
            "continue": "prepare_round",
            "judge": "judge"
        }
    )
    workflow.add_edge("judge", END)

    return workflow.compile()


def build_non_search_workflow(llm):
    """
    Build a simplified workflow without search using a single LLM.
    """
    def node_prepare(state: MADState) -> dict:
        safe_state = ensure_state_defaults(state)
        round_num = safe_state.get("current_round", 1)
        if round_num == 1:
            return node_initialize_context(safe_state)
        return {}

    workflow = StateGraph(MADState)
    
    workflow.add_node("prepare", node_prepare)
    workflow.add_node("defender", lambda s: node_defender(s, llm))
    workflow.add_node("challenger", lambda s: node_challenger(s, llm))
    workflow.add_node("save_round", node_save_round)
    workflow.add_node("judge", lambda s: node_judge(s, llm))

    workflow.set_entry_point("prepare")
    workflow.add_edge("prepare", "defender")
    workflow.add_edge("defender", "challenger")
    workflow.add_edge("challenger", "save_round")
    
    workflow.add_conditional_edges(
        "save_round",
        should_continue_debate,
        {
            "continue": "defender",
            "judge": "judge"
        }
    )
    workflow.add_edge("judge", END)

    return workflow.compile()
