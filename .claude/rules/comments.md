# Let the code speak

Why: readers, human or agent, read the code itself. Comments repeat it, drift out of date,
and cost attention.

- Don't write comments or docstrings in code you write or change, even where the
  surrounding code has them.
- Put the intent in the code instead: precise names, types, small focused functions, named
  constants instead of magic values, and tests that show the expected behaviour.
- If code seems to need a comment to be understood, rewrite the code until it doesn't.
- One exception: a short comment explaining **why**, when the reason lives outside the code
  and nothing in the code can show it: an external constraint (a CI job name that a
  ruleset requires), a workaround for a third-party quirk (the LLM router), or a value fixed
  by a spec. Never a comment that says *what* the code does.
- Leave existing comments alone unless asked; removing them is separate work.
