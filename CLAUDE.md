# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview
- This is a Python LangGraph-based multi-agent debate system for fake-news assessment.
- There are two entry points:
  - CLI run: `main.py`
  - Gradio dashboard: `app.py`

## Environment and setup
- Create/activate virtualenv and install dependencies:
  - `python -m venv .venv`
  - `source .venv/Scripts/activate` (Git Bash on Windows)
  - `pip install -r requirements.txt`
- Required environment variables (used by code):
  - `NINEROUTER_API_KEY`
  - `NINEROUTER_BASE_URL`
  - `TAVILY_API_KEY` (optional but recommended; otherwise search falls back to Wikipedia)
- Note: `.env.example` currently documents `GROQ_API_KEY`, but runtime code in `main.py`/`app.py` reads `NINEROUTER_*` keys.

## Common commands
- Run CLI example flow:
  - `python main.py`
- Run Gradio UI:
  - `python app.py`
- Quick import sanity check:
  - `python -c "from graph.workflow import build_workflow; print('ok')"`

## Testing/linting status
- No project test suite, lint config, or formatter config was found in this repository (no local `tests/`, `pytest.ini`, `pyproject.toml`, or `package.json` outside `.venv`).
- If adding tests, prefer creating a project-level `tests/` directory and using `pytest`.

## Architecture (big picture)

### Core orchestration
- The workflow is defined in `graph/workflow.py` via a LangGraph `StateGraph(MADState)`.
- Shared workflow state schema is in `graph/state.py` (`MADState`, `KnowledgeEntry`, `DebateRound`) with reducers for list/dict accumulation.
- Global runtime knobs are centralized in `config/settings.py` (`config.model`, `config.debate`).

### Agent pipeline
The graph executes this sequence:
1. `direct_search_news` (initial evidence retrieval from original news text)
2. `score_initial` (trust scoring for newly discovered sources)
3. Repeated debate rounds:
   - `ask_defender` -> optional `search_defender` -> `score_def` -> `defender`
   - `ask_challenger` -> optional `search_challenger` -> `score_chal` -> `challenger`
   - `save_round` -> `evaluator`
4. Conditional exit (`current_round > max_rounds`) to `judge`

### Agent responsibilities
- `agents/search_agent.py`
  - Executes adaptive search from pending queries.
  - Uses Tavily when available; falls back to Wikipedia (`vi`/`en`) on failure or missing key.
  - Produces normalized knowledge entries (`[S1]`, `[S2]`, ...).
- `agents/defender.py`
  - Generates pro-authenticity arguments.
  - Split phases: `defend_ask` (query planning) and `defend` (argument generation).
- `agents/challenger.py`
  - Generates skepticism/counter arguments.
  - Split phases: `challenge_ask` and `challenge`.
- `agents/evaluator.py`
  - Scores source trust (`score_sources`) for newly added KB entries.
  - Evaluates each round (`evaluate_round`) and emits structured point rulings.
- `agents/judge.py`
  - Consumes full debate + evaluator history and produces final verdict JSON.

### Prompt layer
- All system prompts live in `prompts/templates.py`.
- Prompt design is role-locked and round-aware (round 1 initialization vs round N rebuttal/evaluation/judgment).
- JSON output contracts in prompts are relied on by robust parsers in agent modules.

### UI/CLI integration
- `main.py` runs one-shot CLI analysis with printed progress and verdict summary.
- `app.py` streams node updates into a 3-column Gradio dashboard:
  - Knowledge/research view
  - Debate transcript view
  - Evaluator/judge analysis view

## Important implementation notes
- `main.py` initializes fields (`claims`, `search_results`) that are not part of `MADState`; keep state keys aligned when refactoring.
- Search quality and token budget are heavily controlled by `config/settings.py` and prompt constraints; tune there first before changing graph topology.
- The repository includes historical design notes in `SYSTEM_DESIGN.md`; current executable behavior should be treated as source of truth.