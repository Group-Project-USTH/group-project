# Let the code speak

Why: readers, human or agent, read the code itself. Comments repeat it, drift out of date,
and cost attention.

- Don't write comments or docstrings in code you write or change.
- Put the intent in the code instead: precise names, types, small focused functions, named
  constants instead of magic values, and tests that show the expected behaviour.
- If code seems to need a comment to be understood, rewrite the code until it doesn't.
- Leave existing comments alone unless asked; removing them is separate work.
