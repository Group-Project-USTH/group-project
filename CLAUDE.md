# CLAUDE.md

## Project

USTH group project: **adding an AI agent to static analysis for maintainability evaluation**
(ISO/IEC 25010). One pipeline, two versions, same code under test, compared against an
answer key: does the agent make the evaluation more accurate, and is the extra cost worth it?
Scoring: TP/FP/FN/TN with Fail as the positive class, Unknown counted separately, plus
stability over 3-5 repeated runs and cost per benefit.

## Commands

```bash
uv sync --locked                                   # install (Python 3.12, from uv.lock)
uv run ruff check                                  # lint
uv run ruff format --check                         # format check (`uv run ruff format` to fix)
uv run mypy                                        # type-check (strict, src/)
uv run pytest                                      # unit tests + coverage, integration excluded
uv run maintain-eval smoke --target tests/fixtures/sample_project   # real LLM, needs .env
uv run pytest -m integration --no-cov              # real LLM end-to-end, needs .env
```

CI runs the first five. Copy `.env.example` to `.env` for the LLM and Langfuse keys.

## Repo map

- `src/maintain_eval/`: the package (`version_a/`, `version_b/`, `evaluation/`, shared
  `schemas.py` and `config.py`, Langfuse adapter `observability.py` + `masking.py`, `cli.py`)
- `tests/`: unit tests; `tests/fixtures/sample_project/` is the smoke-test target
- `scripts/`: ops scripts run by hand (e.g. branch protection, admins only)
- `.github/`: CI workflow, Dependabot, PR template, CODEOWNERS, `main` ruleset
- `.claude/`: shared Claude Code settings, rules and skills

## Domain vocabulary

Use exactly the terms in @GLOSSARY.md (imported, so it loads every session) in code, docs,
issues and commits, never the synonyms it lists under _Avoid_. New or changed terms go
there, not here.

## Working rules

1. **Audit first, then write a short rationale, then change code.** Read the repo state and
   relevant code before proposing; for non-trivial changes, get the plan approved first.
2. **Never push to `main`**: always a branch and a PR (details in `.claude/rules/git-workflow.md`).
3. **Ask first** before destructive commands or any change to GitHub remote settings.
4. **No new dependency without saying why** it is needed; pin versions you actually ran.
5. **Verify by running things** and report real output; say plainly what is unverified.
6. Check current docs for `deepagents`, `langgraph`, `langchain` and `langfuse` before using
   their APIs: they change fast.
7. Never commit secrets: `.env` is git-ignored, `.env.example` holds no real values.

## Gotchas

- `pydantic-settings` reads `.env` but doesn't export it to `os.environ`; keys are passed
  explicitly (see `version_b/agent.py`, `observability.py`).
- The team's OpenAI-compatible router ignores `tool_choice` on `/chat/completions`, so
  `openai:*` models use the Responses API with `ProviderStrategy` structured output.
- The agent's file access is read-only but not sandboxed: it can read anything under the target.
- Trace name `evaluate-characteristic` is an API for dashboards: don't rename it casually.
  Bump `PROMPT_VERSION` when the agent prompt changes. Fetch current Langfuse docs before
  changing tracing.

## Rules and skills

- `.claude/rules/` (loaded automatically): `naming.md`, `repo-structure.md`, `git-workflow.md`,
  `comments.md`.
- `.claude/skills/`: Matt Pocock's engineering skills, third-party and updated deliberately,
  never automatically. Source, commit and update steps: `.claude/skills/README.md`.

## Agent skills

### Issue tracker

GitHub Issues for this repo, via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels: `needs-triage`, `needs-info`, `ready-for-agent`,
`ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` at the root, ADRs in `docs/adr/`. See `docs/agents/domain.md`.
