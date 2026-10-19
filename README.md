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
| `LANGFUSE_TRACING_ENVIRONMENT` | `development` (default); integration tests use `test`. Use e.g. `experiment` for real runs |
| `LANGFUSE_RELEASE` | Optional; defaults to the git commit of the code (`-dirty` if uncommitted changes) |

`openai:*` models are called through the OpenAI **Responses API** with native JSON-schema
structured output (see `version_b/agent.py` for why).

## Run the smoke test

```bash
uv run maintain-eval smoke --target tests/fixtures/sample_project
uv run maintain-eval smoke --target path/to/project --characteristic testability --run-id my-run-1
# group repeated runs (e.g. a stability check) into one Langfuse session:
uv run maintain-eval smoke --target path/to/project --session-id stability-2026-10-12
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
| Tags | `version:A`/`version:B`, `characteristic:<name>` | filter dashboards and tables |
| Metadata | `version`, `run_id`, `characteristic` | correlate with our own results |
| Session | `--session-id`, if given | group repeated runs for stability analysis (**Sessions** view) |
| Environment | `LANGFUSE_TRACING_ENVIRONMENT` | keep dev/test traces out of experiment data |
| Release | git commit of the code | compare code versions |
| Version | `PROMPT_VERSION` in `version_b/agent.py` | compare prompt iterations; bump it when the prompt changes |
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
npx langfuse-cli api observations list --session-id stability-2026-10-12 --is-root-observation
npx langfuse-cli api observations list --level ERROR --is-root-observation
```

## Project layout

```
src/maintain_eval/
  schemas.py            Characteristic, Verdict, Evidence, Finding
  config.py             settings from env / .env
  observability.py      Langfuse tracing: root observation, attributes, no-op without keys
  masking.py            secret redaction applied to traces before export
  cli.py                `maintain-eval` entry point
  version_a/            Analyzer protocol for static-analysis tools (stub)
  version_b/            DeepAgents agent with read-only file access
  evaluation/           TP/FP/FN/TN + unknown counting
tests/                  unit tests; fixtures/sample_project is the smoke-test target
.github/                CI, Dependabot, PR template, CODEOWNERS, main-branch ruleset
scripts/                apply_branch_protection.sh (run manually by a repo admin)
.claude/                shared Claude Code settings, rules and third-party skills (see CLAUDE.md)
GLOSSARY.md             domain terms (Characteristic, Verdict, Finding, ...); use exactly these
docs/agents/            how the Claude Code skills use our issue tracker (GitHub Issues)
```

## Contribution workflow

1. Branch from `main`: `feat/<topic>`, `fix/<topic>`, `chore/<topic>` (also `docs/`, `test/`, `ci/`).
2. Commit with [Conventional Commits](https://www.conventionalcommits.org/): `feat: ...`,
   `fix: ...`, `chore: ...`, `docs: ...`, `test: ...`, `ci: ...`.
3. Push and open a PR; fill in the template.
4. CI (`lint-typecheck-test`) must pass and the branch must be up to date with `main`.
5. At least one teammate approves; resolve all review conversations.
6. **Squash merge** (the only method allowed). Nobody pushes to `main` directly.

The repo owner can bypass these checks (e.g. to merge without an approval); everyone else,
Claude included, goes through them.

Never commit secrets: `.env` is git-ignored, only `.env.example` (no real values) is tracked.

### Using Claude Code

`CLAUDE.md`, `.claude/rules/` and `.claude/settings.json` are shared team setup; the skills in
`.claude/skills/` are third-party (see its README). Open the repo in Claude Code interactively
once and accept the trust prompt, otherwise the shared `allow` rules are ignored (the `deny`
rules always apply). Personal tweaks go in `.claude/settings.local.json` or `CLAUDE.local.md`,
both git-ignored.
