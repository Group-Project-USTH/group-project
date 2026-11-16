# 1. Deliver the evaluator as a Claude Code plugin

- **Status:** accepted
- **Date:** 2026-11-16
- **Evidence:** [docs/research/claude-code-maintainability-tool-pivot.md](../research/claude-code-maintainability-tool-pivot.md)

## Context

The repo was planned as a web chat product: a FastAPI backend serving a DeepAgents agent,
and a web frontend. Only `GET /health` and the agent exist; the frontend is not started.
The agent has one generic prompt for all five Characteristics and cannot read Measures, so
its Verdicts are pure LLM judgement.

The research found that:

- On the only expert-rated benchmark, a size threshold alone matched the expert consensus
  91% of the time, and LLM ratings of Python readability barely correlated with human
  ratings (r = 0.02). LLM Verdicts also drift between identical Runs and flip under
  framing.
- No study has tested whether an LLM given Measures and SIG-style Ratings gives Verdicts
  that agree with experts. That is the question this project can answer.
- SonarQube, CodeScene, SIG, Codacy and DeepSource already reach Claude Code, but none
  gives a pass/fail/unknown Verdict per Characteristic with Evidence backed by Measures.
- The PyPI name `maintainability-agent` belongs to another, similar project.

## Decision

1. **Delivery.** The evaluator becomes a Claude Code plugin: a stdio MCP server that
   returns Measures and Ratings, and a skill with one rubric per Characteristic. Claude
   Code is the LLM loop. A Stop hook, a read-only reviewer subagent and a CI recipe
   (`claude -p --json-schema`) are optional extras.
2. **Scope.** Full replacement. The course does not require DeepAgents or a web UI, so the
   DeepAgents agent, the FastAPI app and the frontend plan are removed, but only after the
   evaluation harness has recorded the agent's Verdicts as a baseline.
3. **Name.** The distribution, CLI command and plugin are renamed `maintainability-lens`
   (Python package `maintainability_lens`). It was free on PyPI on 2026-11-16.
4. **Plugin location.** The repo root is the plugin: `.claude-plugin/` holds both
   `marketplace.json` (one plugin, source `./`) and `plugin.json`, and the plugin's skills
   (later agents and hooks) live in `plugin/`. Claude Code copies only the plugin folder on
   install and plugin paths can't leave it, so this is what lets the MCP server run from the
   installed copy (`uvx --from ${CLAUDE_PLUGIN_ROOT}/backend`). `.claude/skills/` stays
   reserved for third-party skills. No top-level `bin/`, so the skill also loads outside
   Claude Code. Cost: `claude plugin validate --strict` warns that the root `CLAUDE.md` is
   not loaded as plugin context.
5. **Distribution.** Through this repo's marketplace only, versioned by `version` in
   `plugin.json`. The plugin and its MCP server always come from the same commit. No PyPI
   release for now.
6. **Langfuse.** Kept until the baseline Runs are recorded, then removed with the agent. The
   `evaluate-characteristic` trace name is retired at that point. The harness records cost
   per Run from `total_cost_usd`.
7. **Evaluation set.** Every team member rates the same set of about 30 Python files, per
   Characteristic. Agreement among the raters is reported next to the tool's agreement with
   their consensus.
8. **Thresholds.** The SIG 2007 risk bands and rating tables (Heitlager, Kuipers and Visser,
   "A Practical Model for Measuring Maintainability", QUATIC 2007), as summarised in the
   course material. Each threshold is a named constant whose why-comment cites that paper.

## Consequences

- Work follows seven phases of small PRs:
  1. Slim the core and build a walking skeleton: rename, keep the `measure` CLI from loading
     the agent, make the LLM stack an optional extra, add the MCP server and the plugin.
  2. Fill the Measure gaps: file- and project-level Measures, unit interfacing, volume,
     duplication, module coupling, and a production/test split.
  3. Rate: Risk profiles, System property Ratings, and the mapping onto Characteristics.
  4. Evaluate: the rated Python set, agreement and stability scoring, and baselines (size
     only, Ratings only, the DeepAgents agent, the Claude Code skill).
  5. Judge well: rubrics per Characteristic, Evidence first, user claims left out.
  6. Remove the agent, the API and Langfuse; rewrite README, CLAUDE.md, GLOSSARY and
     `repo-structure.md`.
  7. Publish: release versions and install docs.
- The rename comes first in phase 1, not last, so the plugin's `.mcp.json` never ships with
  the old CLI name.
- Until phase 6, README and CLAUDE.md still describe the web chat product; this ADR
  supersedes them where they disagree.
- Success is measured on the harness: Verdict accuracy against the raters' consensus must
  beat the size-only baseline; at least 90% of Characteristics get the same Verdict in five
  Runs; the share of `pass` Verdicts stays close to the raters'; the flip rate when the
  prompt claims the code passed static analysis is reported; 100% of cited Evidence exists
  and every pass or fail cites a Measure.
- **One-way door:** the name. Once the plugin is installed by others, renaming breaks their
  install. Everything else can be reverted.
- **Verified in phase 1:** `uvx` launches the server from an installed plugin copy
  (`claude mcp list` shows it connected, 6.5 s cold), and a headless Run of the skill
  returns a valid Finding.
