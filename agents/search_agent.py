"""
Round-level Search Agent.
- Plans multilingual queries once at start of each round.
- Executes search and keeps top-2 sources per (query, language).
- Uses Tavily when available, falls back to Wikipedia.
"""

import json
import os
import time
import logging
from typing import Any
from typing import Any

import wikipedia
from langchain_core.messages import HumanMessage
from tavily import TavilyClient

from config.settings import config
from prompts.templates import DEFENDER_QUERY_PLANNER_PROMPT, CHALLENGER_QUERY_PLANNER_PROMPT


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
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return {}


def get_tavily_client():
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return None
    try:
        return TavilyClient(api_key=api_key)
    except Exception:
        return None


def plan_round_queries(state: dict, llm, side: str) -> dict:
    """Plan search queries for a specific side at the start of a round."""
    news_text = state["original_news"]
    current_round = state.get("current_round", 1)
    executed = state.get("executed_queries", [])
    focused_targets = state.get("focused_targets", {}).get(side, {})

    planner_prompt = DEFENDER_QUERY_PLANNER_PROMPT if side == "DEFENDER" else CHALLENGER_QUERY_PLANNER_PROMPT
    intent_default = "support_defender" if side == "DEFENDER" else "support_challenger"

    prompt = planner_prompt.format(
        original_news=news_text,
        current_round=current_round,
        focused_targets=str(focused_targets),
        executed_queries=str(executed),
    )

    response = _safe_invoke(llm, [HumanMessage(content=prompt)])
    data = parse_json_robust(response.content) if response else {}

    planned_intents = data.get("planned_queries", [])
    
    target_ids = []
    for bucket in (focused_targets.get("rebut_targets", []), focused_targets.get("defend_targets", [])):
        for t in bucket:
            cid = t.get("claim_id")
            if isinstance(cid, str) and cid:
                target_ids.append(cid)

    planned = []
    for intent_obj in planned_intents:
        if not isinstance(intent_obj, dict): continue
        t_ids = intent_obj.get("target_claim_ids", [])
        if current_round >= 2 and not t_ids:
            continue
            
        loc_queries = intent_obj.get("localized_queries", [])
        for lq in loc_queries:
            if not isinstance(lq, dict): continue
            q = lq.get("query", "")
            lang = lq.get("language", "en")
            if q.strip():
                planned.append({
                    "query": q,
                    "language": lang,
                    "intent": intent_default,
                    "target_claim_ids": t_ids,
                })

    if not planned:
        base_query = news_text[:240].strip()
        langs = ["vi", "en"]
        if current_round >= 2 and target_ids:
            for cid in target_ids[:2]:
                for lang in langs:
                    planned.append({
                        "query": f"{cid} {base_query}",
                        "language": lang,
                        "intent": intent_default,
                        "target_claim_ids": [cid],
                    })
        else:
            for lang in langs:
                planned.append({
                    "query": base_query,
                    "language": lang,
                    "intent": intent_default,
                    "target_claim_ids": [],
                })

    if current_round >= 2 and not any(p.get("target_claim_ids") for p in planned):
        opponent_prefix = "C" if side == "DEFENDER" else "D"
        debate_history = state.get("debate_history", [])
        if debate_history:
            last = debate_history[-1]
            key = "challenger_claims" if opponent_prefix == "C" else "defender_claims"
            opp_claims = last.get(key, [])
            if opp_claims:
                fallback_cid = opp_claims[-1].get("claim_id", "")
                if isinstance(fallback_cid, str) and fallback_cid.startswith(opponent_prefix):
                    for p in planned:
                        if not p.get("target_claim_ids"):
                            p["target_claim_ids"] = [fallback_cid]

    if current_round >= 2:
        planned = [p for p in planned if p.get("target_claim_ids")]

    normalized = []
    seen = set()
    executed_seen = set()
    for eq in executed:
        label = str(eq).strip().lower()
        if not label: continue
        if label.startswith("[") and "] " in label:
            lang = label[1:label.index("]")].strip()
            q = label[label.index("]") + 1 :].strip()
            executed_seen.add((q, lang))
            
    pending = state.get("pending_search_requests", [])
    for p in pending:
        q = str(p.get("query", "")).strip().lower()
        lang = str(p.get("language", "auto")).strip().lower()
        if q:
            executed_seen.add((q, lang))

    for item in planned:
        query = str(item.get("query", "")).strip()
        language = str(item.get("language", "auto")).strip().lower() or "auto"
        if not query: continue
        key = (query.lower(), language)
        if key in seen or key in executed_seen: continue
        seen.add(key)
        target_claim_ids = item.get("target_claim_ids", [])
        
        normalized.append({
            "query": query,
            "language": language,
            "intent": intent_default,
            "target_claim_ids": target_claim_ids,
            "side": side,
            "target_claim_id": target_claim_ids[0] if target_claim_ids else "",
            "reason": f"{side.lower()}-planning",
        })

    normalized = normalized[:4]

    pending_requests = []
    for idx, item in enumerate(normalized, start=1):
        pending_requests.append({
            "request_id": f"R{current_round}-{side}-{idx}",
            **item,
        })

    return {
        "round_retrieval_plan": [{"round": current_round, "side": side, "planned_queries": normalized}],
        "pending_search_requests": pending_requests,
    }


def _tavily_search_top3(client: TavilyClient, query: str) -> list[dict]:
    response = client.search(
        query=query,
        search_depth="basic",
        max_results=5, # Get more to filter by score
        include_answer=False,
    )
    return response.get("results", [])


def _wikipedia_search_top3(query: str, language: str) -> list[dict]:
    wikipedia.set_lang(language)
    results = []
    try:
        titles = wikipedia.search(query, results=3)
    except Exception:
        return []

    for title in titles[:3]:
        try:
            page = wikipedia.page(title, auto_suggest=False)
            results.append({
                "title": page.title,
                "content": page.summary[:600],
                "url": page.url,
                "score": 0.85, # Wikipedia is generally high relevance
            })
        except Exception:
            continue
    return results


def _build_entry(
    current_id_idx: int,
    query: str,
    query_language: str,
    title: str,
    content: str,
    source_url: str,
    relevance_score: float,
    retrieval_provider: str,
    retrieval_language: str,
    rank: int,
) -> dict:
    domain = source_url.split("/")[2] if "//" in source_url else source_url.split("/")[0]
    return {
        "id": f"[S{current_id_idx}]",
        "query": query,
        "query_language": query_language,
        "title": title,
        "content": content,
        "source_url": source_url,
        "domain": domain,
        "relevance_score": relevance_score,
        "retrieval_provider": retrieval_provider,
        "retrieval_language": retrieval_language,
        "rank_within_query_language": rank,
    }


def search_round_evidence(state: dict) -> dict:
    """Execute planned queries and keep top-3 sources per query with score > 0.8."""
    active_side = state.get("active_side", "DEFENDER")
    requests = state.get("pending_search_requests", [])
    planned = [r for r in requests if r.get("side") == active_side]
    remaining_requests = [r for r in requests if r.get("side") != active_side]
    
    current_round = state.get("current_round", 1)
    current_kb_size = len(state.get("knowledge_base", []))
    current_id_idx = current_kb_size + 1

    client = get_tavily_client()
    seen_urls = {entry.get("source_url", "") for entry in state.get("knowledge_base", [])}
    new_entries = []
    round_results = []
    executed_labels = []

    for item in planned:
        query = item.get("query", "")
        language = item.get("language", "auto")
        retrieval_language = "en" if language == "auto" else language

        provider_results = []
        provider = "tavily"
        try:
            if client:
                provider_results = _tavily_search_top3(client, query)
            else:
                raise RuntimeError()
        except Exception:
            provider = "wikipedia"
            provider_results = _wikipedia_search_top3(query, retrieval_language)

        kept = []
        rank = 1
        # Filter results: Relevance > 0.8 and Max 3 results
        for r in provider_results:
            score = float(r.get("score", 0.5))
            if score <= 0.8: # Threshold 0.8
                continue
                
            url = r.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            
            entry = _build_entry(
                current_id_idx=current_id_idx,
                query=query,
                query_language=language,
                title=r.get("title", ""),
                content=r.get("content", ""),
                source_url=url,
                relevance_score=score,
                retrieval_provider=provider,
                retrieval_language=retrieval_language,
                rank=rank,
            )
            rank += 1
            current_id_idx += 1
            new_entries.append(entry)
            kept.append(entry["id"])
            if len(kept) >= 3: # Max 3 per query
                break

        round_results.append({
            "round": current_round,
            "query": query,
            "language": language,
            "provider": provider,
            "source_ids": kept,
            "side": active_side,
        })
        executed_labels.append(f"[{language}] {query}")

    return {
        "knowledge_base": new_entries,
        "round_search_results": round_results,
        "executed_queries": executed_labels,
    }


def _format_debate_history(debate_history: list) -> str:
    if not debate_history:
        return "(Chưa có lịch sử tranh luận)"

    lines = []
    for r in debate_history:
        lines.append(f"Vòng {r.get('round_number', '?')}")
        lines.append(f"DEFENDER: {r.get('defender_argument', '')[:280]}")
        lines.append(f"CHALLENGER: {r.get('challenger_argument', '')[:280]}")
    return "\n".join(lines)
