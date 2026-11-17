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

**Measure**:
One number computed from the code, such as the cyclomatic complexity of one function, with
the file and line range it applies to. Computed by our code, never by the LLM. What
SonarQube and other tools call a "metric" is a Measure here.
_Avoid_: metric, score, statistic

**System property**:
One of the SIG properties rated from Measures, as listed in the SIG/TÜV NORD criteria V18.0
(2026): duplication, unit size, unit complexity, unit interfacing, module coupling, component
independence, component entanglement. A unit is one function or method. Each System property
feeds one or more Characteristics. Volume (lines of code) is reported but not rated.
_Avoid_: factor, dimension, aspect

**Risk profile**:
For one System property, the share of production lines of code in each risk band (low,
moderate, high, very high). Each unit (or, for module coupling, each file) adds its lines of
code to the band its Measure falls in.
_Avoid_: distribution, histogram

**Rating**:
`++`, `+`, `o`, `-` or `--` for one System property or Characteristic, computed by our code
from Risk profiles and fixed thresholds, never by the LLM. A Verdict is decided with the
Rating in hand, not replaced by it. A System property without a published five-level table
gets no Rating, only a check against its source's 4-star limit. A Characteristic's Rating is
the average of its rated System properties, and is partial when some of them are not rated.
_Avoid_: score, grade, stars, rank

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
