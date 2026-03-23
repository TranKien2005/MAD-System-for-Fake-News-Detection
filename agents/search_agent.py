"""
Search Agent — Searches for evidence related to claims.
When search is disabled, uses LLM to simulate search results.
"""

from langchain_core.messages import HumanMessage

from config.sources import get_credibility, get_credibility_label
from prompts.templates import SEARCH_AGENT_PROMPT


def search_evidence(state: dict, llm, enable_search: bool = False) -> dict:
    """
    Search for evidence related to claims.
    
    When enable_search=False: Uses LLM to simulate search results.
    When enable_search=True: Uses Tavily API (to be implemented).
    """
    claims = state.get("claims", [])
    pending_queries = state.get("pending_search_queries", [])

    # Determine what to search for
    if pending_queries:
        search_context = "Yêu cầu tìm kiếm cụ thể từ debater:\n" + "\n".join(
            f"- {q}" for q in pending_queries
        )
    else:
        search_context = ""

    if enable_search:
        # TODO: Implement real Tavily search
        return _simulated_search(state, llm, claims, search_context)
    else:
        return _simulated_search(state, llm, claims, search_context)


def _simulated_search(state: dict, llm, claims: list, additional_context: str) -> dict:
    """Use LLM to simulate search results when search is disabled."""
    claims_text = "\n".join(f"{i+1}. {c}" for i, c in enumerate(claims))

    prompt = SEARCH_AGENT_PROMPT.format(
        claims=claims_text,
        additional_context=additional_context
    )

    response = llm.invoke([
        HumanMessage(content=prompt)
    ])

    # Parse simulated results
    results = _parse_search_results(response.content)

    return {
        "search_results": results,
        "pending_search_queries": [],  # Clear pending queries
    }


def _parse_search_results(raw_text: str) -> list[dict]:
    """Parse search results from LLM response."""
    results = []

    for line in raw_text.strip().split("\n"):
        line = line.strip()
        if not line or not line.startswith("NGUỒN:"):
            continue

        try:
            parts = {}
            for segment in line.split("|"):
                segment = segment.strip()
                if ":" in segment:
                    key, value = segment.split(":", 1)
                    parts[key.strip()] = value.strip()

            domain = parts.get("DOMAIN", "unknown.com")
            credibility = get_credibility(domain)

            results.append({
                "url": f"https://{domain}",
                "title": parts.get("NGUỒN", "Unknown"),
                "content": parts.get("NỘI DUNG", ""),
                "domain": domain,
                "credibility_score": credibility,
                "credibility_label": get_credibility_label(credibility),
            })
        except (ValueError, KeyError):
            continue

    return results
