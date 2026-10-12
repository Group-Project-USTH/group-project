# Repo structure

Goal: a layout that is easy to navigate, scale and maintain.

## Layout

| Path | Holds |
|---|---|
| `src/maintain_eval/` | the only top-level package (src layout) |
| `tests/` | mirrors `src/maintain_eval/` |
| `scripts/` | one-off or ops scripts; never imported by the package |
| `docs/` | human docs: `architecture.md` and short ADRs for decisions costly to reverse |
| `data/` | datasets; large or generated files are git-ignored |
| `.github/` | CI, Dependabot, PR template, rulesets |

Don't pre-create domain docs (glossary, ADR folders): `/setup-matt-pocock-skills` decides
where they live.

## Organise by domain, not by technical layer

- `version_a/`: static-analysis tools only.
- `version_b/`: the agent.
- `evaluation/`: comparison against the answer key (confusion counts, stability, cost).
- `schemas.py`: the shared core types. `config.py`: all settings.
- A new capability gets its own package or module; never grow a catch-all.

## Dependency direction

```
cli ──> version_a, version_b, evaluation ──> adapters (observability, masking) ──> schemas, config
```

- `version_a` and `version_b` must not import each other.
- `evaluation` imports only `schemas`.
- Imports only point down; no cycles. If two packages need the same code, move it down
  (usually into `schemas`), never import sideways.

## Boundaries

- Each package exposes its public API in `__init__.py` (`__all__`); the rest is internal.
  `__init__.py` re-exports, it doesn't hold the implementation.
- One thin adapter per external system (SonarQube, LLM provider, Langfuse). Nothing else
  talks to that system directly.
- Settings are read only in `config.py`; `.env.example` documents them. No `os.environ`
  anywhere else in `src/`.

## Size and focus

One responsibility per file. Review any file over ~300 lines or function over ~50 lines.

## Known deviations

Existing code that predates these rules. Don't copy these patterns, and don't fix them as a
side effect of other work: each gets its own PR. Delete the line once it is fixed.

- `tests/` is flat; `test_agent_wiring.py`, `test_smoke_agent.py`, `test_version_a.py` don't
  mirror their source files. New tests go in the mirrored path.
- `version_a/__init__.py` holds the implementation instead of re-exporting it.
- `version_b/readonly_backend.py` vs `ReadOnlyFilesystemBackend`; `evaluation/confusion.py`
  vs `ConfusionCounts`.
- `AgentAnswer` clashes with "answer key"; `version` is overloaded in `observability.py`.

## Before adding something

1. Which package owns it? If none fits, does it deserve a new one?
2. Do its imports follow the direction above?
3. Is its name greppable and unique (see `naming.md`)?
4. Is there a test file mirroring it?
5. Does it need a new setting? Add it to `config.py` and `.env.example`.
