# maintain-eval

Does adding an AI agent to static-analysis tools give a more accurate evaluation of
software **maintainability**, and is the extra cost worth it? Code under test runs through
**Version A** (static analysis tools only) and **Version B** (the same tools plus a
[DeepAgents](https://docs.langchain.com/oss/python/deepagents/overview) agent). Their
Pass/Fail/Unknown verdicts on the five ISO/IEC 25010 sub-characteristics (modularity,
reusability, analysability, modifiability, testability) are compared against an answer key
for accuracy, stability and cost.

> Status: scaffold. Version A has only an interface; Version B is wired end-to-end with a
> minimal, untuned prompt.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) ≥ 0.12 (it installs Python 3.12 for you)
- An OpenAI-compatible LLM endpoint + API key (for the agent)
- Optional: a [Langfuse](https://langfuse.com) project (public + secret key) for tracing

## Setup

```bash
uv sync                 # creates .venv with Python 3.12 and all dependencies
cp .env.example .env    # then fill in the values (.env is git-ignored)
uv run pre-commit install   # optional: run ruff on every commit
```

### Configuration (`.env`)

| Variable | Purpose |
|---|---|
| `LLM_MODEL` | `provider:model` for LangChain's `init_chat_model`, e.g. `openai:cx/gpt-5.6-terra` |
| `OPENAI_API_KEY` | Key for the LLM endpoint |
| `OPENAI_BASE_URL` | Endpoint base URL; leave empty for api.openai.com, set it for a router/proxy |
| `LANGFUSE_ENABLED` | `false` turns tracing off even if keys are set (default `true`) |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | Langfuse project keys; if missing, tracing is skipped with a warning |
| `LANGFUSE_BASE_URL` | `https://cloud.langfuse.com` (EU), `https://us.cloud.langfuse.com` (US) or self-hosted |

`openai:*` models are called through the OpenAI **Responses API** with native JSON-schema
structured output (see `version_b/agent.py` for why).

## Run the smoke test

```bash
uv run maintain-eval smoke --target tests/fixtures/sample_project
uv run maintain-eval smoke --target path/to/project --characteristic testability --run-id my-run-1
```

It prints one `Finding` as JSON (verdict + file/line evidence), or `error: ...` and exit
code 1 if the agent's answer cannot be parsed or validated. It works without Langfuse keys.

The agent gets **read-only** access to `--target`: write/edit/delete tools are denied by a
DeepAgents permission rule *and* by a read-only backend. It is not an OS sandbox: it can read
everything under the target directory (including any `.env` there), so only point it at code
you are happy to send to the LLM provider.

## Lint, type-check, test

These are exactly the commands CI runs:

```bash
uv sync --locked
uv run ruff check
uv run ruff format --check     # `uv run ruff format` to fix
uv run mypy                    # strict, on src/
uv run pytest                  # unit tests + coverage; integration tests excluded
```

Real end-to-end test against your configured LLM (and Langfuse, if set):

```bash
uv run pytest -m integration --no-cov
```

## Finding traces in Langfuse

Every agent run is one trace named **`maintain-eval`** with:

- **Metadata**: `version` (`A`/`B`), `run_id`, `characteristic`
- **Tags**: `version:B`, `characteristic:<name>`
- **Session**: the `run_id`

In the Langfuse UI: **Tracing → Traces**, filter by tag (e.g. `version:B`) or search for the
`run_id` printed by the CLI; open a trace to see the metadata panel, every LLM call, tool call
(`ls`, `read_file`, …), token usage and latency. **Sessions** groups traces by `run_id`.
Token cost only appears if Langfuse knows the model's price; for router models, add a custom
model definition under **Settings → Models**.

## Project layout

```
src/maintain_eval/
  schemas.py            Characteristic, Verdict, Evidence, Finding
  config.py             settings from env / .env
  observability.py      Langfuse handler + run metadata, no-op without keys
  cli.py                `maintain-eval` entry point
  version_a/            Analyzer protocol for static-analysis tools (stub)
  version_b/            DeepAgents agent with read-only file access
  evaluation/           TP/FP/FN/TN + unknown counting
tests/                  unit tests; fixtures/sample_project is the smoke-test target
.github/                CI, Dependabot, PR template, CODEOWNERS, main-branch ruleset
scripts/                apply_branch_protection.sh (run manually by a repo admin)
```

## Contribution workflow

1. Branch from `main`: `feat/<topic>`, `fix/<topic>`, `chore/<topic>` (also `docs/`, `test/`, `ci/`).
2. Commit with [Conventional Commits](https://www.conventionalcommits.org/): `feat: ...`,
   `fix: ...`, `chore: ...`, `docs: ...`, `test: ...`, `ci: ...`.
3. Push and open a PR; fill in the template.
4. CI (`lint-typecheck-test`) must pass and the branch must be up to date with `main`.
5. At least one teammate approves; resolve all review conversations.
6. **Squash merge** (or rebase). Nobody pushes to `main` directly.

Never commit secrets: `.env` is git-ignored, only `.env.example` (no real values) is tracked.
