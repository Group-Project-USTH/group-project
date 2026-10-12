# CLAUDE.md

## Project

USTH group project (ICT / Cyber Security): **adding an AI agent to static analysis for
maintainability evaluation**. Maintainability per ISO/IEC 25010 (measurement: ISO/IEC 25023)
with five sub-characteristics: modularity, reusability, analysability, modifiability,
testability.

Research question: does adding an AI agent to static-analysis tools give a more accurate
evaluation, and is the extra cost worth it?

Pipeline: code under test → **Version A** (static tools only: SonarQube, dependency checker,
coverage tool) and **Version B** (same tools + DeepAgents agent) in parallel → compare against
the answer key per sub-characteristic → report accuracy, cost, worth.

- Version B answers **Pass / Fail / Unknown** per sub-characteristic and MUST cite file + line.
- Answer key: Git history, mutation testing, an expert-rated dataset, manual checks by two
  team members.
- Scoring: FAIL = positive. TP/FP/FN/TN, FP = false fail, FN = false pass; **Unknown counted
  separately**. Also compare stability (same answer over 3-5 repeated runs) and cost per benefit.
- Every agent run must be traceable in Langfuse by `version`, `run_id`, `characteristic`.

## Commands

```bash
uv sync --locked
uv run ruff check && uv run ruff format --check && uv run mypy && uv run pytest
uv run maintain-eval smoke --target tests/fixtures/sample_project
uv run pytest -m integration --no-cov   # real LLM, needs .env
```

## Working rules

1. **Audit first (read-only).** Inspect repo state, existing config and tool versions before
   proposing changes.
2. **Written rationale before code.** Propose the plan (files, key decisions, one-line why
   each) and wait for approval before writing files.
3. **PRs only.** Work on a feature branch (`feat/`, `fix/`, `chore/`...), Conventional Commits,
   never commit or push to `main`; don't change GitHub settings without asking.
4. **Verify by running things** and report real output; say plainly what is unverified.
5. Check current docs for `deepagents`, `langgraph`, `langchain`, `langfuse` before using
   their APIs; they change fast. Pin versions you actually ran.
6. Never commit secrets (`.env` is git-ignored). Don't add dependencies that aren't needed.

## Gotchas

- `pydantic-settings` reads `.env` but does not export to `os.environ`; pass keys explicitly
  (see `version_b/agent.py`, `observability.py`).
- The team's OpenAI-compatible router ignores `tool_choice` on `/chat/completions`; that is
  why `openai:*` models use the Responses API with `ProviderStrategy` structured output.
- The agent's file access is read-only but not sandboxed: it can read anything under the target.
- Tracing conventions live in `observability.py` (trace name `evaluate-characteristic` is an
  API for dashboards: don't rename casually). Bump `PROMPT_VERSION` when the agent prompt
  changes. Use the Langfuse skill and fetch current docs before changing tracing.
