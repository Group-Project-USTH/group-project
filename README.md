# maintainability-lens

A [DeepAgents](https://docs.langchain.com/oss/python/deepagents/overview) agent that
evaluates software **maintainability**. For each of the five ISO/IEC 25010
sub-characteristics (modularity, reusability, analysability, modifiability, testability) it
reads the code and returns a Pass/Fail/Unknown verdict, citing the files and lines behind it.

It is growing into a web chat product: a FastAPI backend serving the agent and a web
frontend.

## Use it in Claude Code

Needs [uv](https://docs.astral.sh/uv/) on your `PATH`. In your shell:

```bash
claude plugin marketplace add Group-Project-USTH/group-project
claude plugin install maintainability-lens@maintainability-lens
```

Then ask Claude about a Python project's maintainability, or run
`/maintainability-lens:evaluate`. The plugin's MCP server computes the Measures and a Rating
per Characteristic from fixed, cited thresholds; the skill reads the code and gives a Verdict
per Characteristic with that Rating in hand. Unit complexity and duplication use published
tables; unit size, unit interfacing and module coupling use tables calibrated on 100 Python
projects. Modularity and testability are partial until components are measured; see
`docs/adr/0001-deliver-as-claude-code-plugin.md`, decision 8.

## Layout

```
backend/        Python 3.12 (uv): the agent, the `maintainability-lens` CLI and the FastAPI app.
                Setup, configuration, tests, tracing: backend/README.md
frontend/       the web chat UI (not started yet)
.claude-plugin/ the Claude Code marketplace and plugin manifests; the repo root is the plugin
plugin/         the plugin's skills
docs/agents/    how the Claude Code skills use our issue tracker (GitHub Issues)
docs/evaluation/ the protocol Raters follow for the phase 4 Evaluation set, and the Rating calibration
scripts/        apply_branch_protection.sh (run manually by a repo admin), select_evaluation_set.py,
                select_calibration_set.py, calibrate_rating_thresholds.py
.github/        CI, Dependabot, PR template, CODEOWNERS, main-branch ruleset
.claude/        shared Claude Code settings, rules and third-party skills (see CLAUDE.md)
GLOSSARY.md     domain terms (Characteristic, Verdict, Finding, ...); use exactly these
```

## Contribution workflow

1. Branch from `main`: `feat/<topic>`, `fix/<topic>`, `chore/<topic>` (also `docs/`, `test/`, `ci/`).
2. Commit with [Conventional Commits](https://www.conventionalcommits.org/): `feat: ...`,
   `fix: ...`, `chore: ...`, `docs: ...`, `test: ...`, `ci: ...`.
3. Push and open a PR; fill in the template.
4. CI (`lint-typecheck-test`) must pass and the branch must be up to date with `main`.
5. At least one teammate approves; resolve all review conversations.
6. **Squash merge** (the only method allowed). Nobody pushes to `main` directly.

The repo owner can bypass these checks inside a PR (e.g. to merge without an approval), but
cannot push to `main` directly; everyone else, Claude included, goes through them.

Never commit secrets: `.env` is git-ignored, only `.env.example` (no real values) is tracked.

### Using Claude Code

`CLAUDE.md`, `.claude/rules/` and `.claude/settings.json` are shared team setup; the skills in
`.claude/skills/` are third-party (see its README). Open the repo in Claude Code interactively
once and accept the trust prompt, otherwise the shared `allow` rules are ignored (the `deny`
rules always apply). Personal tweaks go in `.claude/settings.local.json` or `CLAUDE.local.md`,
both git-ignored.
