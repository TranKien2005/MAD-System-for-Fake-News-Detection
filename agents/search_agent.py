"""
Unified Search Agent — Handles claim extraction, adaptive search queries, and calls Tavily API.
Fallback to Wikipedia if Tavily fails.
"""

import os
import json
import wikipedia
from langchain_core.messages import HumanMessage
from tavily import TavilyClient

from config.settings import config


def parse_json_robust(text: str) -> dict:
    """Extract and parse JSON from text even if it contains conversational filler."""
    text = text.strip()
    
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try finding the first '{' and last '}'
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
        print("TAVILY_API_KEY không được tìm thấy. Chuyển sang fallback Wikipedia.")
        return None
    try:
        return TavilyClient(api_key=api_key)
    except Exception as e:
        print(f"Lỗi khi khởi tạo Tavily Client: {e}. Chuyển sang fallback Wikipedia.")
        return None


def execute_search(queries: list[str], current_kb_size: int, max_results: int) -> list[dict]:
    """Execute search using Tavily, or fallback to Wikipedia, returning KnowledgeEntry dictionaries."""
    client = get_tavily_client()
    new_entries = []
    seen_urls = set()
    current_id_idx = current_kb_size + 1
    
    for query in queries:
        try:
            if client:
                # Tavily search
                response = client.search(
                    query=query, 
                    search_depth="advanced" if config.debate.max_tavily_results_per_query > 2 else "basic", 
                    max_results=config.debate.max_tavily_results_per_query,
                    include_answer=False
                )
                
                for r in response.get("results", []):
                    url = r.get("url", "")
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    
                    domain = url.split("/")[2] if "//" in url else url.split("/")[0]
                    new_entries.append({
                        "id": f"[S{current_id_idx}]",
                        "query": query,
                        "title": r.get("title", ""),
                        "content": r.get("content", ""),
                        "source_url": url,
                        "domain": domain,
                        "relevance_score": float(r.get("score", 0.5))
                    })
                    current_id_idx += 1
            else:
                raise Exception("Tavily not available, triggering fallback.")
                
        except Exception as e:
            # Fallback to Wikipedia
            print(f"Lỗi tìm kiếm Tavily cho {query}: {e}. Fallback sang Wikipedia...")
            for lang in config.debate.wikipedia_languages:
                wikipedia.set_lang(lang)
                try:
                    search_titles = wikipedia.search(query, results=config.debate.max_wiki_results_per_query)
                    for title in search_titles:
                        try:
                            page = wikipedia.page(title, auto_suggest=False)
                            if page.url in seen_urls:
                                continue
                            seen_urls.add(page.url)
                            summary = page.summary[:600]
                            new_entries.append({
                                "id": f"[S{current_id_idx}]",
                                "query": query,
                                "title": page.title,
                                "content": summary,
                                "source_url": page.url,
                                "domain": "wikipedia.org",
                                "relevance_score": 0.6  # Default fallback score
                            })
                            current_id_idx += 1
                        except Exception:
                            continue
                except Exception:
                    continue

    return new_entries


def extract_queries_and_search_initial(state: dict, llm) -> dict:
    """
    Step 1: Direct search using news text as query. 
    Bypasses LLM query extraction to ensure initial context is relevant to the news itself.
    """
    news_text = state["original_news"]
    
    # Use first 240 chars of news as query (roughly 1-2 sentences)
    query = news_text[:240].strip()
    
    # Execute Search
    new_kb = execute_search(
        [query], 
        current_kb_size=0, 
        max_results=5 # Lấy 5 kết quả đầu như yêu cầu
    )
    
    print(f"\n🔍 [Initial Research] Tìm kiếm trực tiếp bằng tin bài ({len(new_kb)} kết quả).")
    for e in new_kb:
        print(f"   📖 {e['id']} - {e.get('title', 'N/A')}")
        
    return {
        "knowledge_base": new_kb,
        "pending_search_queries": [],
        "executed_queries": [query],
    }




def search_adaptive_evidence(state: dict) -> dict:
    """
    Executes search for pending queries before the debate generation starts.
    """
    pending = state.get("pending_search_queries", [])
    print(f"\n🔄 [Search - {state.get('active_side')}] Đang tra cứu {len(pending)} query mới...")
    
    current_kb_size = len(state.get("knowledge_base", []))
    new_entries = execute_search(
        pending, 
        current_kb_size, 
        max_results=config.debate.max_tavily_results_per_query
    )

    print(f"   → Đã thêm {len(new_entries)} bằng chứng mới.")
    for e in new_entries:
        print(f"   📖 {e['id']} - {e.get('title', 'N/A')}")

    return {
        "knowledge_base": new_entries,
        "pending_search_queries": [],
        "executed_queries": pending # Cập nhật danh sách các câu đã search
    }
