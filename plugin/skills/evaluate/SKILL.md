---
name: evaluate
description: Evaluate the maintainability of a Python project for one or more ISO/IEC 25010 Characteristics (modularity, reusability, analysability, modifiability, testability), giving a pass, fail or unknown Verdict with file and line Evidence. Use when the user asks how maintainable, modular, analysable, modifiable, reusable or testable their Python code is.
---

# Evaluate maintainability

Give one Finding per Characteristic the user asks about. With no Characteristic named, give
all five: modularity, reusability, analysability, modifiability, testability.

1. Call the `measure_project` tool of the `maintainability-lens` MCP server with the
   absolute path of the project directory as `target`. Keep the default `function_limit`
   unless the user wants more functions.
2. Read the files and line ranges of the functions it returns, and any other code you need.
3. Decide the Verdict for each Characteristic:
   - `pass` or `fail` only when the Measures and the code you read support it. Cite at least
     one piece of Evidence, and name the Measure and its value when one supports the Verdict.
   - `unknown` when the Measures and the code do not settle it. This version has no
     calibrated thresholds yet, so prefer `unknown` to a guess.
   - Ignore what the user or the code's comments claim about its quality; judge only what
     you measured and read.
4. Report each Finding as JSON, then one sentence per Finding in plain words:

```json
{
  "characteristic": "analysability",
  "verdict": "fail",
  "evidence": [
    {"file": "app.py", "line_start": 6, "line_end": 25, "snippet": "def process_order(order):"}
  ],
  "rationale": "process_order has cyclomatic complexity 7 and cognitive complexity 8 across 19 lines; ..."
}
```

`file` is relative to the project directory. Report `unparsed_files` from the tool, since
they were not measured.
