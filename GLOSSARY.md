# Maintainability evaluation

A DeepAgents agent that evaluates the maintainability of code under test (ISO/IEC 25010),
one characteristic at a time.

## Language

**Characteristic**:
One of the five ISO/IEC 25010 maintainability sub-characteristics: modularity, reusability,
analysability, modifiability, testability.
_Avoid_: sub-characteristic (in code), metric, criterion, quality attribute

**Verdict**:
`pass`, `fail` or `unknown` for one characteristic.
_Avoid_: result, answer, outcome, decision, label

**Evidence**:
A file and line range, with an optional snippet, that supports a verdict.
_Avoid_: citation, reference, proof, location

**Finding**:
One verdict for one characteristic, with its evidence and rationale. A pass or fail
finding must cite evidence.
_Avoid_: result, assessment, issue, report

**Run**:
One evaluation of one characteristic by the agent, identified by a `run_id` and traced in
Langfuse.
_Avoid_: job, execution, trial

## Version is ambiguous

Say which one: the agent prompt version is `PROMPT_VERSION`; the version of our code is the
Langfuse release.
