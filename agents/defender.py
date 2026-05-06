"""Defender agent (structured JSON output)."""

import time
import logging
from langchain_core.messages import HumanMessage

from prompts.templates import (
    DEFENDER_PROMPT,
)
from agents.evaluator import parse_json_robust, format_knowledge_base
from utils.rate_limit import safe_invoke


def defend(state: dict, llm) -> dict:
    news_text = state["original_news"]
    current_round = state.get("current_round", 1)
    kb_text = format_knowledge_base(state.get("knowledge_base", []), state.get("source_scores", {}))
    registry = state.get("claims_registry", {})
    history = state.get("debate_history", [])
    executed = state.get("executed_queries", [])
    focused = state.get("focused_targets", {}).get("DEFENDER", {})

    all_registry_updates = dict(registry)

    # 1. Identify rebut targets (all opponent claims)
    rebut_targets = _build_targets_from_registry(all_registry_updates, "C")
    
    # 2. Identify defend targets (only own claims that were attacked in previous round)
    attacked_ids = set()
    if history:
        last_opp_claims = history[-1].get("challenger_claims", [])
        for c in last_opp_claims:
            for tid in c.get("target_claim_ids", []):
                if tid.startswith("D"):
                    attacked_ids.add(tid)
    
    defend_targets = [t for t in _build_targets_from_registry(all_registry_updates, "D") if t["claim_id"] in attacked_ids]
    
    # Unified prompt call for SPEAKING phase
    prompt = DEFENDER_PROMPT.format(
        phase="SPEAKING",
        round_number=current_round,
        original_news=news_text,
        full_history=str(history) if history else "(Chưa có lịch sử)",
        knowledge_base_with_scores=kb_text or "(Kho dữ liệu trống)",
        rebut_targets=_format_targets_for_llm(rebut_targets),
        defend_targets=_format_targets_for_llm(defend_targets),
        focused_targets=str(focused),
        executed_queries=str(executed)
    )
    
    response = safe_invoke(llm, [HumanMessage(content=prompt)])
    data = parse_json_robust(response.content)
    interactions = data.get("interactions", [])
    overall_summary = data.get("overall_summary", "").strip()
    
    processed, updated = _process_interactions(interactions, "D", current_round, all_registry_updates)

    # For UI compatibility and state persistence
    claim_contexts = {}
    for claim in processed:
        cid = claim.get("claim_id")
        source_ids = [e.get("source_id") for e in claim.get("evidence", []) if e.get("evidence_type") == "SOURCE"]
        if cid:
            claim_contexts[cid] = source_ids

    return {
        "current_defender_argument": overall_summary or _fallback_argument(processed),
        "current_defender_claims": processed,
        "claims_registry": updated,
        "claim_contexts": claim_contexts,
    }


def _process_interactions(interactions, prefix, round_num, registry):
    updated_registry = dict(registry)
    processed = []

    for interact in interactions:
        target_id = interact.get("target_id", "").strip()
        action_type = interact.get("action_type", "ASSERT").upper()
        text = interact.get("argument", "").strip()
        ev = interact.get("evidence", [])

        if not text:
            continue

        targets = [target_id] if target_id else []

        if action_type == "ASSERT" or not target_id:
            # Create new root claim in registry with simple ID (D1, D2...)
            count = sum(1 for k in updated_registry.keys() if k.startswith(prefix))
            new_id = f"{prefix}{count + 1}"
            entry = {
                "round": round_num,
                "side": prefix,
                "action_type": "ASSERT",
                "text": text,
                "evidence": ev,
                "target_claim_ids": []
            }
            updated_registry[new_id] = [entry]
            processed.append({**entry, "claim_id": new_id})
        else:
            # Append to existing thread (REBUT/DEFEND)
            # Use the target_id as the claim_id to maintain the thread
            if target_id in updated_registry:
                entry = {
                    "round": round_num,
                    "side": prefix,
                    "action_type": action_type,
                    "text": text,
                    "evidence": ev,
                    "target_claim_ids": targets
                }
                updated_registry[target_id].append(entry)
                processed.append({**entry, "claim_id": target_id})

    return processed, updated_registry


def _build_targets_from_registry(registry, prefix):
    """Build a list of targets with their full history."""
    targets = []
    for cid, history in registry.items():
        if cid.startswith(prefix):
            targets.append({
                "claim_id": cid,
                "history": history
            })
    return targets


def _format_targets_for_llm(targets):
    if not targets:
        return "(Không có)"
    lines = []
    for t in targets:
        cid = t["claim_id"]
        history = t["history"]
        lines.append(f"Claim {cid}:")
        for h in history:
            lines.append(f"  - R{h['round']} {h['side']} [{h['action_type']}]: {h['text']}")
    return "\n".join(lines)


def _fallback_argument(claims):
    return "\n".join([f"- {c.get('claim_id')}: {c.get('text')}" for c in claims])
