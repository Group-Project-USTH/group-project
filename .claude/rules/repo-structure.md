# Repo structure

Goal: a layout that is easy to navigate, scale and maintain.

## Layout

| Path | Holds |
|---|---|
| `backend/` | the Python project (own `pyproject.toml`, `uv.lock`, `.env`) |
| `backend/src/maintain_eval/` | the only Python package (src layout) |
| `backend/tests/` | mirrors `backend/src/maintain_eval/` |
| `frontend/` | the web chat UI (not started); its own toolchain, never imports the backend |
| `scripts/` | one-off or ops scripts for the repo; never imported by the package |
| `docs/` | skill config in `docs/agents/`; later `architecture.md`, ADRs in `docs/adr/`, research notes in `docs/research/` |
| `backend/data/` | datasets (not created yet); large or generated files are git-ignored |
| `.github/` | CI, Dependabot, PR template, rulesets |

Domain terms live in `GLOSSARY.md` at the root. Create a doc file or folder only when it
gets real content: an ADR only when a decision costly to reverse is actually made, a
research note (from the `research` skill) as `docs/research/<topic>.md`. Don't
pre-create empty folders.

Backend paths below are relative to `backend/src/maintain_eval/`. Repo-wide things (docs,
scripts, CI, the glossary) stay at the root; anything that belongs to one side goes in
`backend/` or `frontend/`.

## Organise by domain, not by technical layer

- `agent/`: the DeepAgents agent (`deep_agent.py`) and its read-only file backend.
- `api/`: the FastAPI app, one router module per area (`health.py`, ...); `create_app()` in
  `app_factory.py`. HTTP only: the work happens in the packages it calls.
- `schemas.py`: the shared core types. `config.py`: all settings.
- A new capability gets its own package or module; never grow a catch-all.

## Dependency direction

```
cli, api ──> agent ──> adapters (observability, masking) ──> schemas, config
```

- Imports only point down; no cycles. If two packages need the same code, move it down
  (usually into `schemas`), never import sideways.

## Boundaries

- Each package exposes its public API in `__init__.py` (`__all__`); the rest is internal.
  `__init__.py` re-exports, it doesn't hold the implementation.
- One thin adapter per external system (SonarQube, LLM provider, Langfuse). Nothing else
  talks to that system directly.
- Settings are read only in `config.py`; `.env.example` documents them. No `os.environ`
  anywhere else in `backend/src/`.

## Size and focus

One responsibility per file. Review any file over ~300 lines or function over ~50 lines.

## Known deviations

Existing code that predates these rules. Don't copy these patterns, and don't fix them as a
side effect of other work: each gets its own PR. Delete the line once it is fixed.

- `backend/tests/` is flat; `test_agent_wiring.py` and `test_smoke_agent.py` don't mirror
  their source files. New tests go in the mirrored path.
- `agent/readonly_backend.py` vs `ReadOnlyFilesystemBackend`.

## Before adding something

1. Which package owns it? If none fits, does it deserve a new one?
2. Do its imports follow the direction above?
3. Is its name greppable and unique (see `naming.md`)?
4. Is there a test file mirroring it?
5. Does it need a new setting? Add it to `config.py` and `.env.example`.
