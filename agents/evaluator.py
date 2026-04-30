"""Evaluator and source-credibility utilities."""

import json
import time
import logging
from typing import Any

from langchain_core.messages import HumanMessage

from prompts.templates import EVALUATOR_PROMPT, SOURCE_SCORER_PROMPT


def _safe_invoke(llm, messages, max_retries=3, delay=2):
    for i in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            if "429" in str(e) and i < max_retries - 1:
                logging.warning(f"Rate limit hit. Retrying in {delay}s... (Attempt {i+1}/{max_retries})")
                time.sleep(delay)
                delay *= 2
                continue
            raise e
    return None


def parse_json_robust(text: Any) -> dict:
    if isinstance(text, list):
        text = "".join([c.get("text", "") for c in text if isinstance(c, dict)])
    else:
        text = str(text)
        
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if len(lines) > 2:
            text = "\n".join(lines[1:-1])

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return {}


def score_sources(state: dict, llm) -> dict:
    kb = state.get("knowledge_base", [])
    scores = state.get("source_scores", {})

    new_sources_list = [entry for entry in kb if entry["id"] not in scores]
    if not new_sources_list:
        return {"source_scores": {}}

    new_sources_text = "\n".join(
        [
            f"📖 {s['id']} {s['title']} (Domain: {s['domain']})\n   {s['content'][:300]}..."
            for s in new_sources_list
        ]
    )

    prompt = SOURCE_SCORER_PROMPT.format(
        original_news=state["original_news"],
        new_sources=new_sources_text,
    )

    response = _safe_invoke(llm, [HumanMessage(content=prompt)])
    data = parse_json_robust(response.content)

    new_scores = {}
    for item in data.get("assessments", []):
        sid = item.get("source_id")
        score = float(item.get("trust_score", 0.0))
        if sid:
            new_scores[sid] = score

    for s in new_sources_list:
        if s["id"] not in new_scores:
            new_scores[s["id"]] = 0.0

    return {"source_scores": new_scores}


def evaluate_round(state: dict, llm) -> dict:
    current_round = state.get("current_round", 1) - 1

    kb_text = format_knowledge_base(state.get("knowledge_base", []), state.get("source_scores", {}))
    prev_rulings = state.get("evaluator_rulings", [])
    prev_text = _format_previous_rulings(prev_rulings)

    defender_claims = state.get("current_defender_claims", [])
    challenger_claims = state.get("current_challenger_claims", [])

    prompt = EVALUATOR_PROMPT.format(
        original_news=state["original_news"],
        knowledge_base_with_scores=kb_text,
        previous_evaluator_rulings=prev_text,
        round_number=current_round,
        defender_argument=_format_claims_for_eval(defender_claims, "D"),
        challenger_argument=_format_claims_for_eval(challenger_claims, "C"),
    )

    seeded = _seed_claim_decisions(defender_claims, challenger_claims)

    response = _safe_invoke(llm, [HumanMessage(content=prompt)])
    ruling = parse_json_robust(response.content)
    ruling["round_number"] = current_round

    normalized = []
    raw_decisions = ruling.get("claim_decisions", [])
    if not raw_decisions:
        raw_decisions = seeded

    for idx, decision in enumerate(raw_decisions):
        normalized.append(
            {
                "claim_id": decision.get("claim_id", "?"),
                "status": decision.get("status", "ACTIVE"),
                "admissibility": decision.get("admissibility", "PASS"),
                "relevance": decision.get("relevance", "MEDIUM"),
                "stance_check": decision.get("stance_check", "PASS"),
                "evidence_check": decision.get("evidence_check", "PASS"),
                "closure_reason": decision.get("closure_reason", ""),
                "guidance": decision.get("guidance", ""),
                "turn_index": idx,
            }
        )

    if not normalized:
        for idx, decision in enumerate(seeded):
            normalized.append(
                {
                    "claim_id": decision.get("claim_id", "?"),
                    "status": decision.get("status", "ACTIVE"),
                    "admissibility": decision.get("admissibility", "PASS"),
                    "relevance": decision.get("relevance", "MEDIUM"),
                    "stance_check": decision.get("stance_check", "PASS"),
                    "evidence_check": decision.get("evidence_check", "PASS"),
                    "closure_reason": decision.get("closure_reason", ""),
                    "guidance": decision.get("guidance", ""),
                    "turn_index": idx,
                }
            )

    ruling["claim_decisions"] = normalized
    return {"evaluator_rulings": [ruling]}


def _seed_claim_decisions(defender_claims: list, challenger_claims: list) -> list[dict]:
    seeded = []
    for claim in defender_claims + challenger_claims:
        cid = claim.get("claim_id", "?")
        targets = claim.get("target_claim_ids", [])
        action = claim.get("action_type", "ASSERT")
        evidence = claim.get("evidence", [])

        stance_ok = str(cid).startswith("D") or str(cid).startswith("C")
        has_source = any(e.get("evidence_type") == "SOURCE" and e.get("source_id") for e in evidence)
        has_common_knowledge = any(e.get("evidence_type") == "COMMON_KNOWLEDGE" for e in evidence)

        status = "ACTIVE"
        admissibility = "PASS"
        relevance = "HIGH"
        evidence_check = "PASS"
        stance_check = "PASS" if stance_ok else "FAIL"
        closure_reason = ""

        if not stance_ok:
            status = "DROPPED"
            admissibility = "FAIL"
            closure_reason = "Sai định dạng claim_id theo phe"

        if not has_source and not has_common_knowledge:
            status = "DROPPED"
            admissibility = "FAIL"
            evidence_check = "FAIL"
            closure_reason = "Không có evidence hợp lệ (cần SOURCE hoặc COMMON_KNOWLEDGE)"

        if action in ("REBUT", "DEFEND") and not has_source:
            status = "DROPPED"
            admissibility = "FAIL"
            evidence_check = "FAIL"
            closure_reason = "Vòng phản biện/bảo vệ bắt buộc phải có SOURCE; COMMON_KNOWLEDGE không đủ"

        if action in ("REBUT", "DEFEND") and not targets:
            status = "DROPPED"
            admissibility = "FAIL"
            closure_reason = "REBUT/DEFEND phải có target_claim_ids"

        seeded.append(
            {
                "claim_id": cid,
                "status": status,
                "admissibility": admissibility,
                "relevance": relevance,
                "stance_check": stance_check,
                "evidence_check": evidence_check,
                "closure_reason": closure_reason,
                "guidance": "Tăng bằng chứng mới và nhắm đúng claim đối phương nếu phản biện.",
            }
        )
    return seeded


def _format_claims_for_eval(claims: list, prefix: str) -> str:
    if not claims:
        return f"(Không có claim {prefix})"

    lines = []
    for c in claims:
        cid = c.get('claim_id', '?')
        atype = c.get('action_type', 'ASSERT')
        targets = c.get('target_claim_ids', [])
        txt = c.get('text', '')
        ev = c.get('evidence', [])
        
        lines.append(
            f"{cid} [{atype}] -> {targets}\n"
            f"Text: {txt}\n"
            f"Evidence: {ev}"
        )
    return "\n\n".join(lines)


def format_evaluator_summary(evaluator_rulings: list[dict]) -> str:
    if not evaluator_rulings:
        return "(Chưa có đánh giá từ Evaluator)"

    lines = []
    for ruling in evaluator_rulings:
        r_num = ruling.get("round_number", "?")
        lines.append(f"\n⚖️ THẨM ĐỊNH SAU VÒNG {r_num}:")
        for d in ruling.get("claim_decisions", []):
            lines.append(
                f"- {d.get('claim_id', '?')}: {d.get('status', 'ACTIVE')} "
                f"(admissibility={d.get('admissibility', 'PASS')}, relevance={d.get('relevance', 'MEDIUM')})"
            )
            if d.get("closure_reason"):
                lines.append(f"  -> closure_reason: {d.get('closure_reason')}")
            if d.get("guidance"):
                lines.append(f"  -> guidance: {d.get('guidance')}")

        summary = ruling.get("round_summary", "")
        if summary:
            lines.append(f"  📝 Tóm tắt: {summary}")

    return "\n".join(lines)


def format_knowledge_base(knowledge_base: list, source_scores: dict | None = None) -> str:
    if not knowledge_base:
        return "(Không có dữ liệu từ Knowledge Base)"

    if source_scores is None:
        source_scores = {}

    lines = []
    for entry in knowledge_base:
        tid = entry.get("id", "[S?]")
        title = entry.get("title", "N/A")
        content = entry.get("content", "")
        domain = entry.get("domain", "")
        relevance = entry.get("relevance_score", 0.5)
        trust = source_scores.get(tid, "Chưa giám định")

        lines.append(f"📖 {tid} {title} (Trust: {trust} | Domain: {domain} | Relevance: {relevance:.2f})")
        lines.append(f"   {content[:400]}")
        lines.append("")
    return "\n".join(lines)


def _format_previous_rulings(rulings: list) -> str:
    if not rulings:
        return "(Chưa có đánh giá trước đó)"
    return format_evaluator_summary(rulings)
