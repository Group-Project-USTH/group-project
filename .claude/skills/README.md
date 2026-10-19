# Project skills

The skills in this folder are **third-party**: a small selection of Matt Pocock's
engineering skills, copied unmodified. They steer the agent, so they are updated
deliberately (see below), never automatically.

We keep only skills for **coding, system design, debugging, research and pull requests**.

| | |
|---|---|
| Source | https://github.com/mattpocock/skills, folder `skills/engineering` |
| Commit | `49dd158d1076134a641b33efb035946536778336` (2026-10-09) |
| Installed | 2026-10-12; trimmed to 7 skills on 2026-10-19 |
| License | MIT, © 2026 Matt Pocock: see [`LICENSE`](LICENSE) |

Installed with (real copies, no symlinks; the generated `skills-lock.json` was deleted
because this file records the commit instead):

```bash
DO_NOT_TRACK=1 npx -y skills@1.7.2 add mattpocock/skills --agent claude-code --copy -y \
  --skill code-review codebase-design diagnosing-bugs implement pr research tdd
```

## Skills

`/name` = only runs when you type it. Others Claude may also load on its own.

| Skill | Area | What it is for |
|---|---|---|
| `/implement` | coding | Implement a piece of work from an issue or spec, using `tdd` and finishing with `code-review`. |
| `tdd` | coding | Test-driven development, red-green-refactor. Uses `codebase-design` for interface questions. |
| `code-review` | coding, PRs | Review changes since a commit/branch on two axes: repo standards and the originating issue/spec. **Replaces the built-in `/code-review`**; the built-in stays available as `/review`. |
| `codebase-design` | system design | Vocabulary for deep modules, interfaces and seams, plus "design it twice". |
| `diagnosing-bugs` | debugging | Diagnosis loop for hard bugs and performance regressions. |
| `research` | research | Research a question against primary sources into a Markdown file. |
| `pr` | PRs | The shape a pull request body should take. |

These skills only call each other (`implement` → `tdd`, `code-review`; `tdd` →
`codebase-design`). `code-review` and `implement` read the issue tracker set in
`CLAUDE.md` (`docs/agents/issue-tracker.md`).

## Updating

1. On a `chore/` branch, list `skills/engineering` upstream
   (`gh api repos/mattpocock/skills/contents/skills/engineering`).
2. Re-run the command above from the repo root, then `rm skills-lock.json`. Only add a
   skill if it fits the five areas above, and check that every skill it calls
   ("call the Skill tool with ...") is installed too.
3. Review `git diff .claude/skills` like any third-party code: look for new shell
   commands, network access, file access outside the repo, or new `allowed-tools`/`hooks`.
4. Update the commit, date and table in this file and open a PR.

## Not installed

Left out on purpose; don't re-add them on update:

- Planning and interviews: `ask-matt`, `grill-with-docs`, `grilling`, `wayfinder`.
- Domain docs: `domain-modeling` (our terms live in `GLOSSARY.md`, edited by hand).
- Issue workflows: `to-spec`, `to-tickets`, `triage`, `implement-spec`.
- Other: `improve-codebase-architecture` (needs `grilling` and `domain-modeling`),
  `prototype`, `retro`, `wizard`, `setup-matt-pocock-skills` (its one-time config is in
  `docs/agents/issue-tracker.md`).

`agents/openai.yaml` files are metadata for OpenAI Codex; Claude Code ignores them.
