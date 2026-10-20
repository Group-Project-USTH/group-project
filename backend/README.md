# Backend

The Python side of the project: the maintainability agent (built on
[DeepAgents](https://docs.langchain.com/oss/python/deepagents/overview)), its
`maintainability-agent` CLI and the FastAPI app for the web chat product. What the project is and
how we work: [root README](../README.md).

> Status: scaffold. The agent is wired end-to-end with a minimal, untuned prompt.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) ≥ 0.12 (it installs Python 3.12 for you)
- An OpenAI-compatible LLM endpoint + API key (for the agent)
- Optional: a [Langfuse](https://langfuse.com) project (public + secret key) for tracing

## Setup

Run every command in this file from `backend/`.

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
| `LANGFUSE_BASE_URL` | `https://cloud.langfuse.com` (EU), `https://us.cloud.langfuse.com` (US) or self-hosted (v4.59.0 or later, needed by SDK v5) |
| `LANGFUSE_TRACING_ENVIRONMENT` | `development` (default); integration tests use `test`. Use e.g. `experiment` for real runs |
| `LANGFUSE_RELEASE` | Optional; defaults to the git commit of the code (`-dirty` if uncommitted changes) |

`openai:*` models are called through the OpenAI **Responses API** with native JSON-schema
structured output (see `agent/deep_agent.py` for why).

## Run the smoke test

```bash
uv run maintainability-agent smoke --target tests/fixtures/sample_project
uv run maintainability-agent smoke --target path/to/project --characteristic testability --run-id my-run-1
# group related runs into one Langfuse session:
uv run maintainability-agent smoke --target path/to/project --session-id repeat-2026-10-12
```

It prints one `Finding` as JSON (verdict + file/line evidence), or `error: ...` and exit
code 1 if the agent's answer cannot be parsed or validated. It works without Langfuse keys.

The agent gets **read-only** access to `--target`: write/edit/delete tools are denied by a
DeepAgents permission rule *and* by a read-only backend. It is not an OS sandbox: it can read
everything under the target directory (including any `.env` there), so only point it at code
you are happy to send to the LLM provider.

## Run the API

```bash
uv run uvicorn --factory maintainability_agent.api:create_app --reload   # http://127.0.0.1:8000
curl http://127.0.0.1:8000/health                              # {"status":"ok"}
```

Interactive API docs: http://127.0.0.1:8000/docs. Only `GET /health` exists so far; the chat
endpoints come next. `--reload` is for development only.

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

With Langfuse keys set, the CLI prints `trace=<url>` for every run. Each run is one trace:

```
[agent] evaluate-characteristic        input: target, characteristic, question · output: the Finding
  [chain] LangGraph                    DeepAgents graph
    [chain] model → [generation] decide-next-action   model id, tokens, reasoning summary
    [chain] tools → [tool] ls / read_file / ...       arguments and file contents read
```

| Attribute | Value | Use it to |
|---|---|---|
| Trace name | `evaluate-characteristic` | find all evaluation runs |
| Tags | `characteristic:<name>` | filter dashboards and tables |
| Metadata | `run_id`, `characteristic` | find a specific run |
| Session | `--session-id`, if given | group related runs (**Sessions** view) |
| Environment | `LANGFUSE_TRACING_ENVIRONMENT` | keep dev/test traces out of experiment data |
| Release | git commit of the code | compare code versions |
| Version | `PROMPT_VERSION` in `agent/deep_agent.py` | compare prompt iterations; bump it when the prompt changes |
| Level | `ERROR` + status message on failed runs | find runs with no valid answer |

Before export, likely secrets are redacted (`sk-…`/`pk-…` keys, AWS/GitHub tokens, private
keys, `*_API_KEY=`/`*_TOKEN=`/`*_SECRET=`/`*_PASSWORD=` values; see `masking.py`). This
protects Langfuse only: the LLM provider still sees what the agent reads.

**Cost**: token usage is recorded on every generation, but Langfuse only computes cost for
models it knows. For router models such as `cx/gpt-5.6-terra`, add a custom model definition
with your per-token prices in the Langfuse project settings.

Query traces from the terminal with the [Langfuse CLI](https://langfuse.com/docs/api-and-data-platform/features/cli):

```bash
set -a; . ./.env; set +a
npx langfuse-cli api observations list --session-id repeat-2026-10-12 --is-root-observation
npx langfuse-cli api observations list --level ERROR --is-root-observation
```

## Layout

```
src/maintainability_agent/
  schemas.py            Characteristic, Verdict, Evidence, Finding
  config.py             settings from env / .env
  observability.py      Langfuse tracing: root observation, attributes, no-op without keys
  masking.py            secret redaction applied to traces before export
  cli.py                `maintainability-agent` entry point
  agent/                DeepAgents agent with read-only file access
  api/                  FastAPI app: main.py (create_app()), routers/ (one per area: health)
tests/                  unit tests; fixtures/sample_project is the smoke-test target
```
