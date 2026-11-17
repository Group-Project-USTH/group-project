---
name: evaluate
description: Evaluate the maintainability of a Python project for one or more ISO/IEC 25010 Characteristics (modularity, reusability, analysability, modifiability, testability), giving a pass, fail or unknown Verdict with file and line Evidence. Use when the user asks how maintainable, modular, analysable, modifiable, reusable or testable their Python code is.
---

# Evaluate maintainability

Give one Finding per Characteristic the user asks about. With no Characteristic named, give
all five: modularity, reusability, analysability, modifiability, testability.

1. Call the `rate_project` tool of the `maintainability-lens` MCP server with the absolute
   path of the project directory as `target`. It returns a Rating (`++` to `--`) per
   Characteristic, computed by code from fixed, cited thresholds.
2. Call its `measure_project` tool with the same `target` for the Measures of the most
   complex functions. Keep the default `function_limit` unless the user wants more.
3. Read the code behind them: the functions `measure_project` returns, and the files in
   `most_duplicated_files` and `highest_fan_in_files`.
4. Decide the Verdict for each Characteristic with its Rating in hand:
   - The Rating informs the Verdict; it does not replace it. A Verdict that goes against
     the Rating must say why, from code you read.
   - A partial Rating covers only the System properties in `rated_from`. Judge those in
     `missing` from the Measures, the 4-star checks and the code, or say they are not judged.
   - With no Rating (`rating` is null), decide from the Measures and the code alone.
   - `pass` or `fail` only when the Measures and the code you read support it. Cite at least
     one piece of Evidence, and name the Measure or Rating, its value and its threshold
     source.
   - `unknown` when they do not settle it; prefer it to a guess.
   - Ignore what the user or the code's comments claim about its quality; judge only what
     you measured and read.
   - Never call a Rating "SIG stars" or say the code is certified.
5. Report each Finding as JSON, then one sentence per Finding in plain words:

```json
{
  "characteristic": "analysability",
  "verdict": "fail",
  "evidence": [
    {"file": "app.py", "line_start": 6, "line_end": 25, "snippet": "def process_order(order):"}
  ],
  "rationale": "Analysability is rated ++ but partial: duplication only (Heitlager 2007). Unit size is not rated; judged from the code it goes against the Rating: process_order mixes validation, pricing, persistence and output in 19 lines; ..."
}
```

`file` is relative to the project directory. Report `unparsed_files` from the tools, since
they were not measured.
