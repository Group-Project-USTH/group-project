# Repo structure

Goal: a layout that is easy to navigate, scale and maintain.

## Layout

| Path | Holds |
|---|---|
| `backend/` | the Python project (own `pyproject.toml`, `uv.lock`, `.env`) |
| `backend/src/maintainability_lens/` | the only Python package (src layout) |
| `backend/tests/` | mirrors `backend/src/maintainability_lens/` |
| `.claude-plugin/` | `marketplace.json` and `plugin.json`: the repo root is the Claude Code plugin, so its MCP server runs from the installed copy's `backend/` |
| `plugin/` | the plugin's own skills (later agents and hooks); `.claude/skills/` stays for third-party skills |
| `frontend/` | the web chat UI (not started); its own toolchain, never imports the backend |
| `scripts/` | one-off or ops scripts for the repo; never imported by the package |
| `docs/` | skill config in `docs/agents/`; later `architecture.md`, ADRs in `docs/adr/`, research notes in `docs/research/` |
| `.github/` | CI, Dependabot, PR template, rulesets |

Domain terms live in `GLOSSARY.md` at the root. Create a doc file or folder only when it
gets real content: an ADR only when a decision costly to reverse is actually made, a
research note (from the `research` skill) as `docs/research/<topic>.md`. Don't
pre-create empty folders.

Backend paths below are relative to `backend/src/maintainability_lens/`. Repo-wide things
(docs, scripts, CI, the glossary) stay at the root; anything that belongs to one side goes
in `backend/` or `frontend/`.

## Organise by domain, not by technical layer

- `agent/`: the DeepAgents agent (`deep_agent.py`) and its read-only file backend
  (`read_only_filesystem_backend.py`).
- `measures/`: Measures computed from the code, never by the LLM. `measure_project()` in
  `project_measures.py` is the entry point; `python_units.py` lists the units (functions and
  methods) from `ast`; one module per tool (`function_measures.py` for lizard,
  `cognitive_complexity.py` for complexipy) attaches its numbers to those units;
  `unit_interfacing.py` turns each unit's parameter count into a Measure;
  `parsed_file.py` parses each file once and finds its code lines; `file_volume.py` counts
  them; `duplication.py` finds 6-line blocks repeated across files; `module_coupling.py`
  resolves imports to project files and counts each file's fan-in;
  `production_test_split.py` decides which files are test code; `file_scope.py` narrows a
  project's Measures to one file.
- `ratings/`: Risk profiles and Ratings computed from the Measures, never by the LLM.
  `risk_profiles.py` holds the risk bands, `system_property_ratings.py` the Rating tables and
  4-star limits, `characteristic_ratings.py` the mapping onto Characteristics; every
  threshold is a constant citing its source.
- `evaluation/`: the phase 4 harness. `evaluation_set.py` loads the Evaluation set and checks
  out each project at its pinned commit; one module per Approach (`size_only.py`,
  `ratings_only.py`, `claude_code_skill.py`, `deepagents_agent.py`) turns a file into
  Findings; `recorded_findings.py` appends them to JSONL;
  `approach_runs.py` runs an Approach over the set and skips what is already recorded.
- `mcp_server.py`: the MCP server (`maintainability-lens mcp`, stdio) that serves the
  Measures and Ratings to Claude Code. MCP only: the work happens in `measures/` and
  `ratings/`.
- `api/`: the FastAPI app, laid out as in FastAPI's
  [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) guide.
  HTTP only: the work happens in the packages it calls.
  - `main.py`: `create_app()` builds the app and includes every router.
  - `routers/`: one module per area (`health.py`, ...), each with its own
    `APIRouter(prefix="/<area>", tags=["<area>"])`. Import the module, not its `router`
    (`from maintainability_lens.api.routers import health`, then `health.router`), so the
    `router` names never collide.
  - `dependencies.py`: dependencies shared by several routers (settings, auth). Create it
    with the first one.
- `schemas.py`: the shared core types. `config.py`: all settings.
- A new capability gets its own package or module; never grow a catch-all.

## Dependency direction

```
cli, api, mcp_server ──> evaluation ──> agent ──> measures, ratings, adapters (observability, masking) ──> schemas, config
```

- Imports only point down; no cycles. If two packages need the same code, move it down
  (usually into `schemas`), never import sideways.

## Boundaries

- Each package exposes its public API in `__init__.py` (`__all__`); the rest is internal.
  `__init__.py` re-exports, it doesn't hold the implementation.
- One thin adapter per external system (LLM provider, Langfuse). Nothing else talks to that
  system directly.
- Settings are read only in `config.py`; `.env.example` documents them. No `os.environ`
  anywhere else in `backend/src/`.

## Size and focus

One responsibility per file. Review any file over ~300 lines or function over ~50 lines.

## Known deviations

Existing code that predates these rules. Don't copy these patterns, and don't fix them as a
side effect of other work: each gets its own PR. Delete the line once it is fixed.

None right now.

## Before adding something

1. Which package owns it? If none fits, does it deserve a new one?
2. Do its imports follow the direction above?
3. Is its name greppable and unique (see `naming.md`)?
4. Is there a test file mirroring it?
5. Does it need a new setting? Add it to `config.py` and `.env.example`.
