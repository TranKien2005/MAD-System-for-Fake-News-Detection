# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

MAD System for Fake News Detection is a Python fake-news/claim verification project built around Multi-Agent Debate (MAD). A single OpenAI-compatible LLM instance is used by multiple roles: query planning/search, Defender, Challenger, source scorer, and Judge. The system supports:

- `search` mode: retrieve external evidence before each debate round, score sources, then debate and judge.
- `non_search` mode: use caller-provided `initial_context` as source `[S1]` with trust score `1.0`; this is the mode used by the FEVER benchmark scripts.

The repository also contains Vietnamese project/report material (`main.tex`, slide generation files, figures, and presentation assets). Code comments and UI/report copy are largely Vietnamese; keep that style when editing user-facing text.

## Common commands

### Environment setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a root `.env` file before running the app or benchmarks:

```env
NINEROUTER_API_KEY=...
NINEROUTER_BASE_URL=...
NINEROUTER_MODEL=llama3
# Optional: enables Tavily in search mode; otherwise Wikipedia fallback is used
TAVILY_API_KEY=...
```

### Run the system

```powershell
# CLI example in main.py
python main.py

# Gradio demo UI
python app.py
```

`main.py` loads `.env` only in its `__main__` block. If calling `run_mad()` from another script, load environment variables first or ensure they are already set.

### Data preparation and benchmarks

```powershell
# Prepare binary SUPPORTS/REFUTES FEVER samples from data/raw/FEVER.jsonl
python scripts/prepare_fever.py --n 40

# Run FEVER non-search benchmark and write logs/reports under data/results/fever_logs/
python scripts/test_fever.py --file data/processed/fever_claims_binary.json --n 40
```

GossipCop and TruthfulQA scripts exist, but the README notes some extended evaluation scripts may need to be synchronized with the current `main.py` API (`get_llm()` and `run_mad()`) before use.

### Tests and linting

There is no committed pytest suite or lint/type-check configuration. `pytest` is not listed in `requirements.txt` and was not installed in the current environment. For quick syntax validation after Python edits, use:

```powershell
python -m compileall agents graph config prompts utils scripts main.py app.py
```

If tests are added later, document the exact commands here, including how to run a single test.

## Architecture

### Entry points

- `main.py` exposes `get_llm()` and `run_mad(...)`. `run_mad` selects the graph builder based on `debate_mode`, builds the initial `MADState`, invokes the compiled LangGraph workflow, prints a verdict unless `silent=True`, and returns the final state.
- `app.py` is a Gradio streaming demo. It constructs the same workflows, streams LangGraph node updates, and renders progress, sources, claims registry threads, and verdict HTML.
- `scripts/test_fever.py` imports `run_mad` and `get_llm`, compares a direct Base LLM score with MAD in `non_search` mode, and writes per-sample debate logs plus an analysis report.

### State and workflow orchestration

- `graph/state.py` defines `MADState`, reducers, and `build_initial_state()`. Important state collections are:
  - `knowledge_base`: evidence sources with IDs like `[S1]`.
  - `source_scores`: trust score map keyed by source ID.
  - `claims_registry`: threaded D*/C* claim history across rounds.
  - `debate_history`: saved round summaries consumed by later rounds and Judge.
  - `pending_search_requests`, `executed_queries`, `round_retrieval_plan`, and `round_search_results`: search planning/execution state.
- `graph/workflow.py` builds two LangGraph graphs:
  - Search workflow: `prepare_round -> search_defender + search_round -> score_sources -> defender -> challenger -> save_round`, looping until `current_round > max_rounds`, then `judge`.
  - Non-search workflow: `prepare -> defender -> challenger -> save_round`, looping until Judge. On round 1, `prepare` loads `initial_context` as `[S1]`.
- `node_save_round` appends round data, clears current round claims, increments `current_round`, and garbage-collects unused non-`[S1]` source content to reduce token usage.

### Agent roles

- `agents/search_agent.py` performs query planning via the Defender/Challenger prompts in `QUERY_PLANNING` phase. It executes Tavily searches when `TAVILY_API_KEY` is available, otherwise falls back to Wikipedia. It filters for relevance score `> 0.8`, keeps up to 3 results per query, deduplicates URLs, and appends evidence entries to `knowledge_base`.
- `agents/evaluator.py` contains shared JSON parsing, knowledge-base formatting, source scoring, and a round evaluator. `score_sources` is wired into the search workflow. `evaluate_round` exists but is not currently connected in the main workflow.
- `agents/defender.py` and `agents/challenger.py` use structured JSON prompt outputs in `SPEAKING` phase. They maintain claim IDs (`D1`, `D2`, `C1`, `C2`, ...), append `REBUT`/`DEFEND` interactions to existing registry threads, and return current argument summaries plus claim lists.
- `agents/judge.py` formats the full debate history and source-scored knowledge base, invokes the Judge prompt, and robustly parses the final verdict JSON. `truth_score` is required and is expected to be one of the discrete values described in the prompt.

### Configuration, prompts, and rate limits

- `config/settings.py` is the central runtime configuration. It reads `NINEROUTER_MODEL` from the environment and defines debate/search limits such as `max_rounds`, Wikipedia languages, Tavily/Wikipedia results per query, and `max_calls_per_minute`.
- `prompts/templates.py` contains the strict JSON contracts for Defender, Challenger, Source Scorer, Evaluator, and Judge. When changing prompt output fields, update the corresponding parsers and UI renderers.
- `utils/rate_limit.py` wraps LLM calls with `safe_invoke`, a global proactive `RateLimiter`, and retry/backoff handling for 429/rate-limit/reset-after errors.

## Development notes

- The code assumes an OpenAI-compatible provider through `langchain_openai.ChatOpenAI` using `NINEROUTER_API_KEY`, `NINEROUTER_BASE_URL`, and `NINEROUTER_MODEL`.
- Source IDs include brackets (`[S1]`) throughout the code and prompts. Preserve that convention when adding evidence, source scores, or citations.
- Claim IDs use side prefixes (`D*` for Defender, `C*` for Challenger). Round 1 uses `ASSERT`; later rounds are expected to use `REBUT` or `DEFEND` against target claims.
- The README is the canonical user-facing project overview and includes current caveats: Gradio UI may need synchronization if workflow signatures change, and some older design docs/scripts may not match the latest code.
