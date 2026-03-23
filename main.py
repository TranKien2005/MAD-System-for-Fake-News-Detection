"""
MAD System for Fake News Detection — Entry Point

Usage:
    python main.py
"""

import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from config.settings import config
from graph.workflow import build_workflow


def create_llms():
    """Create LLM instances from config."""
    llm_main = ChatGroq(
        model=config.model.main_model,
        temperature=config.model.debate_temperature,
    )
    llm_light = ChatGroq(
        model=config.model.light_model,
        temperature=config.model.parser_temperature,
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
        "search_results": [],
        "pending_search_queries": [],
        "current_round": 1,
        "max_rounds": config.debate.max_rounds,
        "debate_history": [],
        "current_defender_argument": "",
        "current_challenger_argument": "",
        "verdict": None,
    }

    print("=" * 60)
    print("🔎 MAD SYSTEM — FAKE NEWS DETECTION")
    print("=" * 60)
    print(f"\n📰 Tin tức cần kiểm tra:\n{news_text}")
    print(f"\n⚙️  Config: {config.debate.max_rounds} vòng tranh luận, "
          f"search={'BẬT' if config.debate.enable_search else 'TẮT (simulated)'}")
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

    # Verdict emoji and color
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

    # Key evidence
    key_evidence = verdict.get("key_evidence", [])
    if key_evidence:
        print(f"\n🔑 Bằng chứng chính:")
        for i, e in enumerate(key_evidence, 1):
            print(f"   {i}. {e}")

    # Scores
    def_score = verdict.get("defender_score", {})
    chal_score = verdict.get("challenger_score", {})
    if def_score and chal_score:
        print(f"\n📊 Điểm đánh giá:")
        print(f"   {'Tiêu chí':<25} {'Defender':>10} {'Challenger':>10}")
        print(f"   {'—'*45}")
        for key in ["evidence_quality", "rebuttal_effectiveness",
                     "unrefuted_points", "consistency", "faithfulness"]:
            label = key.replace("_", " ").title()
            d = def_score.get(key, "N/A")
            c = chal_score.get(key, "N/A")
            print(f"   {label:<25} {str(d):>10} {str(c):>10}")

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
