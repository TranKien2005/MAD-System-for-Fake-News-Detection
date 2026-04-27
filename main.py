"""
MAD System for Fake News Detection — Entry Point

Usage:
    python main.py
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from config.settings import config
from graph.workflow import build_workflow
from graph.state import build_initial_state


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

    initial_state = build_initial_state(
        news_text=news_text,
        max_rounds=config.debate.max_rounds,
    )
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

    winner = verdict.get("winner", "UNCERTAIN")
    margin = verdict.get("margin", "low")
    confidence = verdict.get("confidence", 50)

    if winner == "DEFENDER":
        emoji = "✅"
        label = "DEFENDER CHIẾM ƯU THẾ"
    elif winner == "CHALLENGER":
        emoji = "🚫"
        label = "CHALLENGER CHIẾM ƯU THẾ"
    else:
        emoji = "❓"
        label = "CHƯA THỂ KẾT LUẬN"

    print(f"\n{emoji} {label}")
    print(f"📊 Độ tự tin: {confidence}% | Biên độ: {margin}")

    points = verdict.get("top_3_decisive_points", [])
    if points:
        print("\n🎯 3 điểm quyết định:")
        for idx, p in enumerate(points[:3], start=1):
            print(f"   {idx}. {p}")

    print(f"\n📝 Giải thích:\n{verdict.get('final_reasoning', 'N/A')}")

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
