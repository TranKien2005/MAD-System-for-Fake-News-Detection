"""
MAD System for Fake News Detection — Entry Point

Usage:
    python main.py
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from config.settings import config
from graph.workflow import build_workflow, build_non_search_workflow
from graph.state import build_initial_state


def get_llm():
    """Create a single LLM instance from config."""
    api_key = os.getenv("NINEROUTER_API_KEY")
    base_url = os.getenv("NINEROUTER_BASE_URL")

    return ChatOpenAI(
        model=config.model.model_name,
        temperature=config.model.debate_temperature,
        api_key=api_key,
        base_url=base_url,
    )


def run_mad(
    news_text: str, 
    initial_context: str | None = None,
    debate_mode: str = "search",
    custom_output_instructions: str | None = None, 
    silent: bool = False
) -> dict:
    """
    Run the MAD System on a piece of news using a single unified model.
    """
    llm = get_llm()
    
    if debate_mode == "non_search":
        app = build_non_search_workflow(llm)
    else:
        app = build_workflow(llm)

    initial_state = build_initial_state(
        news_text=news_text,
        initial_context=initial_context,
        debate_mode=debate_mode,
        max_rounds=config.debate.max_rounds,
        custom_output_instructions=custom_output_instructions,
    )
    if not silent:
        print("=" * 60)
        print("🔎 MAD SYSTEM — FAKE NEWS DETECTION")
        print("=" * 60)
        print(f"\n📰 Tin tức cần kiểm tra:\n{news_text}")
        print(f"\n⚙️  Config: {config.debate.max_rounds} vòng tranh luận, Tavily Search: BẬT")
        print("=" * 60)

    # Run the workflow
    final_state = app.invoke(initial_state)

    # Print final verdict
    if not silent:
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

    for key, value in verdict.items():
        if isinstance(value, list):
            print(f"\n🎯 {key.replace('_', ' ').title()}:")
            for idx, item in enumerate(value, 1):
                print(f"   {idx}. {item}")
        else:
            print(f"→ {key.replace('_', ' ').title()}: {value}")

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
