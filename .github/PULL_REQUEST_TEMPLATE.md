## Summary

<!-- One or two sentences: what does this PR do? -->

## What / why

<!-- What changed, and why it is needed. Link the issue/task if there is one. -->

## How tested

<!-- Commands you ran and what you observed, e.g.
`uv run pytest`, `uv run maintain-eval smoke --target tests/fixtures/sample_project` -->

## Merge danger

<!-- Door: one-way (hard to undo: data, settings, public APIs such as the trace name) or
two-way (a revert undoes it). Blast radius: what could break, and for whom. -->

## Checklist

- [ ] CI is green (ruff check, ruff format --check, mypy, pytest)
- [ ] Tests added or updated for the change
- [ ] Docs updated (README / CLAUDE.md) if behaviour or setup changed
- [ ] No secrets, API keys or `.env` contents in the diff or commit history
- [ ] PR title follows Conventional Commits (`feat: ...`, `fix: ...`, `chore: ...`)
