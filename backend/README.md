# Backend

The Python side of the project: the maintainability agent (built on
[DeepAgents](https://docs.langchain.com/oss/python/deepagents/overview)), its
`maintainability-lens` CLI and the FastAPI app for the web chat product. What the project is and
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

`uv sync` installs the `dev` and `agent` dependency groups. The `agent` group (DeepAgents,
LangChain, Langfuse, FastAPI) is not part of the package, so an install without the repo
gets only what `measure` needs:

```bash
uvx --from "git+https://github.com/Group-Project-USTH/group-project#subdirectory=backend" \
  maintainability-lens measure --target path/to/project
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

## Measure a project

```bash
uv run maintainability-lens measure --target tests/fixtures/sample_project
```

It prints the project's Measures as JSON, plus any `unparsed_files`. It needs no LLM or
Langfuse keys.

- **Per function** (with its file, line range and qualified name such as `Cart.add` or
  `outer.inner`): cyclomatic complexity (lizard's definition), cognitive complexity
  (complexipy), lines of code, and parameter count without `self`/`cls`. The units come from
  Python's `ast`, so both tools' numbers land on the same unit.
- **Per file** (`function` is `null`, lines 1 to the last): lines of code, skipping
  docstrings, comments and blank lines; and duplicated lines, the lines in any block of 6 or
  more lines that appears again anywhere in the project, ignoring indentation (SIG's
  definition); and fan-in, the number of production files that import it. Imports resolve
  the way Python does: a file's name is the chain of package folders (with `__init__.py`)
  above it plus its stem, so src layouts, scripts and a target that is itself a package
  all work.
- **Every Measure** has `is_test_code`: true for `test_*.py`, `*_test.py`, `conftest.py` and
  anything under a `test/` or `tests/` folder.

## Run the smoke test

```bash
uv run maintainability-lens smoke --target tests/fixtures/sample_project
uv run maintainability-lens smoke --target path/to/project --characteristic testability --run-id my-run-1
# group related runs into one Langfuse session:
uv run maintainability-lens smoke --target path/to/project --session-id repeat-2026-10-12
```

It prints one `Finding` as JSON (verdict + file/line evidence), or `error: ...` and exit
code 1 if the agent's answer cannot be parsed or validated. It works without Langfuse keys.

The agent gets **read-only** access to `--target`: write/edit/delete tools are denied by a
DeepAgents permission rule *and* by a read-only backend. It is not an OS sandbox: it can read
everything under the target directory (including any `.env` there), so only point it at code
you are happy to send to the LLM provider.

## Run the API

```bash
uv run uvicorn --factory maintainability_lens.api:create_app --reload   # http://127.0.0.1:8000
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

## Serve the Measures and Ratings over MCP

```bash
uv run maintainability-lens mcp
```

Starts an MCP server over stdio with two tools. Claude Code starts it through the plugin.

- `rate_project(target, file=None)`: a Rating (`++` to `--`) per Characteristic, averaged from its
  System properties, with `is_partial` and `missing` naming those not measured (component
  independence and entanglement). Also each System property's Rating with its threshold
  source, the Risk profiles, production and test lines of code, the duplicated percentage,
  and the production files with the most duplicated lines and the highest fan-in. Test code is
  left out of every Rating. Unit complexity and duplication use the Heitlager et al. 2007
  tables; unit size, unit interfacing and module coupling use limits calibrated on 100 Python
  projects (`docs/evaluation/rating-calibration.md`; ADR 0001, decision 8).
- `measure_project(target, function_limit=20, file=None)`: every Measure of the
  `function_limit` functions with the highest cyclomatic complexity, the number of functions
  measured, and `unparsed_files`.

With `file` (relative to `target`), both tools cover that one file: its Ratings come from its
own Measures, but its duplication and fan-in are still counted against the whole project.
Phase 4 uses this to rate each file of the Evaluation set.

## Record Findings on the Evaluation set

```bash
uv run maintainability-lens evaluate-set --approach size-only --checkouts ../.checkouts --output path/to/findings
```

Checks out each file's project at its pinned commit (reused on later runs), applies one
Approach to every file of `evaluation/evaluation_set.json`, and appends one line per file to
`<output>/<approach>.jsonl`: its Finding for each Characteristic, and the cost in USD when an
LLM gave them. Files already recorded are skipped, so an
interrupted run resumes. `--repetitions N` records each file N times, for stability.

- `size-only`: `pass` on every Characteristic when the file has at most 275 lines of code
  (Borg, Ezzouhri and Tornhill, ICSME 2024), otherwise `fail`.
- `ratings-only`: `pass` when the file's Characteristic Rating is `+` or `++`, `fail` below,
  `unknown` with no Rating.
- `claude-code-skill`: runs `claude -p` in the checkout with the plugin's evaluate skill and
  its MCP server, and nothing else from your setup: no user settings, plugins or claude.ai
  connectors, read-only tools only, structured output through `--json-schema`. Needs
  `--model`; `--max-budget-usd` (default 2) caps each file, `--plugin-dir` (default `..`)
  points at the repo root. Each line records the model and `total_cost_usd`.
- `deepagents-agent`: asks the DeepAgents agent about the file once per Characteristic
  (`PROMPT_VERSION` 1.1), with the model and keys from `.env`, traced in Langfuse under the
  session `evaluation-set`. Needs the `agent` dependency group; cost is not recorded here, it
  is in Langfuse.

A file whose Approach fails (an error, a timeout, an invalid answer) is reported and left
unrecorded, so the next run retries it; the command then exits with 1.

Keep tool Findings out of the repo until every Rater has submitted
(`docs/evaluation/rating-protocol.md`).

## Score the Approaches

```bash
uv run maintainability-lens score-evaluation --rater-verdicts path/to/rater_verdicts.json --findings path/to/findings [--json-output scores.json]
```

`rater_verdicts.json` is a list of `{rater, file_id, characteristic, verdict}`, with Raters
under pseudonyms. The command prints, as fixed in the rating protocol:

- Krippendorff's alpha (nominal) among Raters, per Characteristic and overall.
- Each Approach's accuracy against the Raters' strict-majority consensus (at least three
  Raters), per Characteristic and overall, averaged over repetitions. `unknown` matches only an
  `unknown` consensus, so an Approach that abstains loses accuracy.
- Each Rater's accuracy against the consensus of the others.
- Leniency: the Raters' and each Approach's share of `pass`.
- Stability, when an Approach has several repetitions: the share of file and Characteristic
  pairs with one Verdict in every repetition, and Krippendorff's alpha across repetitions.
- Total cost, when recorded.

## Layout

```
src/maintainability_lens/
  schemas.py            Characteristic, Verdict, Evidence, Finding, Measure
  config.py             settings from env / .env
  observability.py      Langfuse tracing: root observation, attributes, no-op without keys
  masking.py            secret redaction applied to traces before export
  cli.py                `maintainability-lens` entry point
  mcp_server.py         MCP server over stdio: the `rate_project` and `measure_project` tools
  agent/                DeepAgents agent with read-only file access
  measures/             per-function and per-file Measures, no LLM
  ratings/              Risk profiles and Ratings from the Measures, no LLM
  evaluation/           phase 4 harness: Evaluation set checkouts, Approaches, recorded Findings
  api/                  FastAPI app: main.py (create_app()), routers/ (one per area: health)
tests/                  unit tests; fixtures/sample_project is the smoke-test target
```
