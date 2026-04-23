"""
MAD System for Fake News Detection — Entry Point

Usage:
    python main.py
"""

import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from config.settings import config
from graph.workflow import build_workflow


def create_llms():
    """Create LLM instances from config."""
    api_key = os.getenv("NINEROUTER_API_KEY")
    base_url = os.getenv("NINEROUTER_BASE_URL")

    llm_main = ChatOpenAI(
        model=config.model.main_model,
        temperature=config.model.debate_temperature,
        api_key=api_key,
        base_url=base_url,
        max_tokens=config.model.max_tokens,
    )
    llm_light = ChatOpenAI(
        model=config.model.light_model,
        temperature=config.model.parser_temperature,
        api_key=api_key,
        base_url=base_url,
        max_tokens=config.model.max_tokens,
    )
    return llm_main, llm_light


def run_mad(news_text: str) -> dict:
    """
    Run the MAD System on a piece of news.

    Args:
        news_text: The news article to verify.

    Returns:
        Final state dict containing verdict and debate history.
    """
    llm_main, llm_light = create_llms()
    app = build_workflow(llm_main, llm_light)

    initial_state = {
        "original_news": news_text,
        "claims": [],
        "knowledge_base": [],
        "search_results": [],
        "pending_search_queries": [],
        "current_round": 1,
        "max_rounds": config.debate.max_rounds,
        "debate_history": [],
        "current_defender_argument": "",
        "current_challenger_argument": "",
        "evaluator_rulings": [],
        "verdict": None,
    }

    print("=" * 60)
    print("🔎 MAD SYSTEM — FAKE NEWS DETECTION")
    print("=" * 60)
    print(f"\n📰 Tin tức cần kiểm tra:\n{news_text}")
    print(f"\n⚙️  Config: {config.debate.max_rounds} vòng tranh luận, "
          f"Wikipedia search: BẬT, "
          f"Languages: {config.debate.wikipedia_languages}")
    print("=" * 60)

    # Run the workflow
    final_state = app.invoke(initial_state)

    # Print final verdict
    _print_verdict(final_state)

    return final_state


def _print_verdict(state: dict):
    """Pretty print the final verdict."""
    verdict = state.get("verdict")
    if not verdict:
        print("\n❓ Không có kết quả phán quyết.")
        return

    print("\n" + "=" * 60)
    print("⚖️  KẾT QUẢ PHÁN QUYẾT")
    print("=" * 60)

    v = verdict.get("verdict", "UNCERTAIN")
    confidence = verdict.get("confidence", 50)

    if v == "LIKELY_REAL":
        emoji = "✅"
        label = "CÓ VẺ LÀ TIN THẬT"
    elif v == "LIKELY_FAKE":
        emoji = "🚫"
        label = "CÓ VẺ LÀ TIN GIẢ"
    else:
        emoji = "❓"
        label = "KHÔNG CHẮC CHẮN"

    print(f"\n{emoji} {label}")
    print(f"📊 Độ tin cậy: {confidence}%")
    print(f"\n📝 Giải thích:\n{verdict.get('reasoning', 'N/A')}")

    # Per-claim scores
    claim_scores = verdict.get("claim_scores", [])
    if claim_scores:
        print(f"\n📊 Điểm từng nhận định:")
        print(f"   {'ID':<6} {'Bên':<12} {'Credibility':>11} {'Reliability':>11} {'Relevance':>9} {'Score':>8}")
        print(f"   {'—'*57}")
        for cs in claim_scores:
            cid = cs.get("claim_id", "?")
            side = cs.get("side", "?")
            cred = cs.get("source_credibility", 0)
            rel = cs.get("reliability", 0)
            rev = cs.get("relevance", 0)
            score = cs.get("score", 0)
            print(f"   {cid:<6} {side:<12} {cred:>11.2f} {rel:>11.2f} {rev:>9.2f} {score:>8.3f}")

    # Total scores
    def_total = verdict.get("defender_total", 0)
    chal_total = verdict.get("challenger_total", 0)
    print(f"\n📊 Tổng điểm:")
    print(f"   Defender:   {def_total:.3f}")
    print(f"   Challenger: {chal_total:.3f}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    load_dotenv()

    # Example news for testing
    test_news = (
        "Theo nghiên cứu mới nhất của Đại học Harvard năm 2024, "
        "uống 3 ly cà phê mỗi ngày giúp giảm 50% nguy cơ ung thư gan. "
        "Nghiên cứu được thực hiện trên 10,000 người trong 5 năm "
        "và đã được WHO công nhận."
    )

    result = run_mad(test_news)
