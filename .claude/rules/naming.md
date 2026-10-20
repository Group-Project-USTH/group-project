# Naming

Why: when something breaks, anyone should find the right file with one grep or a quick
glance at the file tree.

## Names say what the thing is

- Full descriptive words, no cryptic abbreviations: `characteristic` not `chr`, `evidence`
  not `ev`. Allowed: universally known ones (`id`, `url`, `llm`, `cli`, `config`).
- One concept, one word. Use the terms in `GLOSSARY.md` everywhere, never a
  synonym: a `Verdict` is never a `result`, `answer` or `outcome`.

## Files

- `snake_case.py`, named after the main thing inside: `confusion_counts.py`, not `utils.py`.
- Banned: `utils.py`, `helpers.py`, `common.py`, `misc.py`, `stuff.py`, `manager.py`,
  `base2.py`. Needing one of these means the file does too much: split it.
- Prefer basenames that are unique across the repo (not five `agent.py`), so search results
  and editor tabs are unambiguous. Exceptions: `__init__.py`, `cli.py`, test files that
  mirror their source file.

## Code

| Kind | Rule | Good | Bad |
|---|---|---|---|
| Function | verb, `snake_case` | `count_confusion_cells` | `confusion` |
| Class | noun, `PascalCase` | `Finding` | `HandleFinding` |
| Boolean | reads as a question | `is_unknown`, `has_evidence` | `unknown_flag` |
| Collection | plural | `findings` | `finding_list` |
| Quantity | unit in the name | `timeout_seconds`, `cost_usd` | `timeout` |
| Constant | `UPPER_SNAKE_CASE` | `PROMPT_VERSION` | `promptVersion` |

No single-letter names, except trivial loop indices or math-like local scopes.

## Tests

- `backend/tests/` mirrors `backend/src/maintainability_agent/`; the test file for `x.py` is `test_x.py`.
- Test functions state the behaviour: `test_pass_without_evidence_is_rejected`, not `test_finding_2`.

## Branches

`feat/…`, `fix/…`, `chore/…`, `docs/…` (also `test/…`, `ci/…`): short, lowercase,
hyphenated, e.g. `feat/sonarqube-analyzer`.

Formatting and import order are enforced by `ruff`; don't restate them.
