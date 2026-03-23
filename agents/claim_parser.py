"""
Claim Parser Agent — Extracts verifiable claims from news text.
"""

from langchain_core.messages import SystemMessage, HumanMessage

from prompts.templates import CLAIM_PARSER_PROMPT


def parse_claims(state: dict, llm) -> dict:
    """
    Extract claims from the original news text.
    
    Returns updated state with parsed claims list.
    """
    news_text = state["original_news"]

    prompt = CLAIM_PARSER_PROMPT.format(news_text=news_text)

    response = llm.invoke([
        HumanMessage(content=prompt)
    ])

    # Parse response into list of claims
    raw_claims = response.content.strip()
    claims = []
    for line in raw_claims.split("\n"):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith("-")):
            # Remove numbering like "1.", "2.", "- "
            clean = line.lstrip("0123456789.-) ").strip()
            if clean:
                claims.append(clean)

    # Fallback: if parsing fails, use the whole response
    if not claims:
        claims = [raw_claims]

    return {"claims": claims}
