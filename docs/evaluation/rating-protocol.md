# Rating protocol for the Evaluation set

Phase 4 of [ADR 0001](../adr/0001-deliver-as-claude-code-plugin.md) scores the tool's
Verdicts against Verdicts given by hand. This page is what each Rater follows. It is fixed
before anyone rates, so the analysis cannot be tuned to the data.

## What you rate

The Evaluation set is 30 Python files from six open-source projects, each at a pinned
commit, listed in [`backend/evaluation/evaluation_set.json`](../../backend/evaluation/evaluation_set.json).
For each file and each of the five Characteristics you give one Verdict: `pass`, `fail` or
`unknown`. That is 150 Verdicts in total. Plan for 10 to 15 minutes per file, about six
hours in all, split over a few sessions.

Open each file through the link in the rating form; it shows the file at the pinned commit.
You may browse the rest of that project at the same commit: its other modules, its tests,
who imports the file. Judge the file as it stands in its project.

## How to decide

For each Characteristic, ask: **if this file landed in your team's codebase, would you accept
it as it is on this Characteristic?**

- `pass`: yes, without rework.
- `fail`: no, it needs rework on this Characteristic before you would accept it.
- `unknown`: the file and its project don't give you enough to decide either way.

A one-line reason, with line numbers if you like, helps the analysis but is optional.

## The five Characteristics

Paraphrased from ISO/IEC 25010, with the questions to ask at file level.

| Characteristic | The degree to which... | Ask about this file |
|---|---|---|
| Modularity | the system is made of parts such that changing one has little impact on the others | Does it do one job? Are its dependencies on other modules few and explicit? |
| Reusability | a part can be used in more than one system, or to build other parts | Could its functions or classes be used elsewhere without dragging in unrelated code? |
| Analysability | you can find what a change would affect, diagnose a fault, or locate the code to change | Can you follow what each function does and find where to make a change? |
| Modifiability | the code can be changed without introducing defects or degrading quality | Could you change a behaviour here without breaking something unexpected? |
| Testability | test criteria can be set and tests run against them | Can its units be tested in isolation, without heavy setup or hidden state? |

## Stay blind

The comparison only works if your Verdicts are your own.

- Don't run the plugin, its MCP tools, a linter, a complexity tool or an LLM on these files.
- Don't read any Verdicts or analysis the harness writes to `backend/evaluation/`.
- Don't discuss the files with other Raters until everyone has submitted.
- Rate the files in the order the form gives.

## Your data

The form shows each Rater only their own Verdicts. When everyone has submitted, the Verdicts
are exported to the repo under pseudonyms (`rater-a`, `rater-b`, ...). Names stay out of
the repo.

## Analysis, fixed in advance

- **Agreement among Raters:** Krippendorff's alpha (nominal) over `pass`, `fail` and
  `unknown`, per Characteristic and overall.
- **Consensus:** for each file and Characteristic, the Verdict a strict majority of Raters
  gave. Without one, the pair has no consensus: it is reported, but left out of accuracy.
  At least three Raters are needed.
- **Tool accuracy:** the share of pairs with a consensus where the tool's Verdict matches it,
  per Characteristic, for each approach: size only, Ratings only, the DeepAgents agent and the
  Claude Code skill.
- **Human baseline:** each Rater's accuracy against the consensus of the other Raters. In
  Borg et al. (ICSME 2024), single experts matched the consensus about 70% of the time.
- **Leniency:** each approach's share of `pass` against the Raters' share.

## How the files were chosen

[`scripts/select_evaluation_set.py`](../../scripts/select_evaluation_set.py) checks out each
project at its commit, computes our Measures, and keeps production files that have 30 to 600
lines of code and at least two units. It then draws 10 files from each size band (30-149,
150-349, 350-600 lines of code), spread over the SIG 2007 complexity bands of each file's
worst unit (up to 10, 11-20, over 20), with at most six files per project, a fixed random
seed, and the order shuffled. Rerunning it gives the same 30 files:

```bash
uv run --project backend python scripts/select_evaluation_set.py <checkout-folder> backend/evaluation/evaluation_set.json
```

Only references (repository, commit and path) are stored, never copies. The projects are
under MIT, BSD-3-Clause, Apache-2.0, MPL-2.0 and the Unlicense.
