# Maintainability evaluation

Evaluates the maintainability of code under test (ISO/IEC 25010) with two versions of one
pipeline and compares their verdicts against an answer key, for accuracy, stability and cost.

## Language

**Characteristic**:
One of the five ISO/IEC 25010 maintainability sub-characteristics: modularity, reusability,
analysability, modifiability, testability.
_Avoid_: sub-characteristic (in code), metric, criterion, quality attribute

**Verdict**:
`pass`, `fail` or `unknown` for one characteristic. `fail` is the positive class when scoring.
_Avoid_: result, answer, outcome, decision, label

**Evidence**:
A file and line range, with an optional snippet, that supports a verdict.
_Avoid_: citation, reference, proof, location

**Finding**:
One verdict for one characteristic, with its evidence, rationale and source (`agent` or
`tool:<name>`). An agent's pass or fail finding must cite evidence.
_Avoid_: result, assessment, issue, report

**Version A**:
The pipeline using static-analysis tools only (SonarQube, dependency checker, coverage tool).
_Avoid_: baseline, tools-only pipeline, pipeline A

**Version B**:
Version A's tools plus the DeepAgents agent, traced in Langfuse.
_Avoid_: agent version, AI pipeline, pipeline B

**Answer key**:
The reference verdicts a version's findings are scored against, built from Git history,
mutation testing, an expert-rated dataset and manual checks by two team members.
_Avoid_: ground truth, gold standard, oracle, expected results

**Run**:
One evaluation of one characteristic by one version, identified by a `run_id` and traced in
Langfuse. Repeated runs of the same input measure stability.
_Avoid_: job, execution, trial

## Version is ambiguous

"Version" alone means Version A or Version B. The agent prompt version is `PROMPT_VERSION`;
the version of our code is the Langfuse release.
