# Project skills

The skills in this folder are **third-party**: Matt Pocock's engineering skills, copied
unmodified. They steer the agent, so they are updated deliberately (see below), never
automatically.

| | |
|---|---|
| Source | https://github.com/mattpocock/skills, folder `skills/engineering`, plus `grilling` and `writing-for-agents` from `skills/productivity` (called by `/grill-with-docs`, `/improve-codebase-architecture` and `/retro`) |
| Commit | `49dd158d1076134a641b33efb035946536778336` (2026-10-09) |
| Installed | 2026-10-12; `grilling` and `writing-for-agents` added 2026-10-19 |
| License | MIT, © 2026 Matt Pocock: see [`LICENSE`](LICENSE) |

Installed with (real copies, no symlinks; the generated `skills-lock.json` was deleted
because this file records the commit instead). Only the skills below are installed; see
[Not installed](#not-installed) for the rest of `skills/engineering`.

```bash
DO_NOT_TRACK=1 npx -y skills@1.7.2 add mattpocock/skills --agent claude-code --copy -y \
  --skill code-review codebase-design diagnosing-bugs domain-modeling grill-with-docs \
  grilling implement improve-codebase-architecture pr prototype research retro \
  setup-matt-pocock-skills tdd writing-for-agents
```

## Updating

1. On a `chore/` branch, list `skills/engineering` upstream
   (`gh api repos/mattpocock/skills/contents/skills/engineering`), check that skills we
   keep still find the skills they call (`grill-with-docs` → `grilling`, `retro` → `writing-for-agents`), and adjust the
   `--skill` list for added, removed or deprecated skills. Don't re-add the ones under
   [Not installed](#not-installed). Delete folders of skills that were removed upstream.
2. Re-run the command above from the repo root, then `rm skills-lock.json`.
3. Review `git diff .claude/skills` like any third-party code: look for new shell
   commands, network access, file access outside the repo, or new `allowed-tools`/`hooks`.
4. Update the commit, date and table in this file and open a PR.

## Skills

`/name` = only runs when you type it. Others Claude may also load on its own.

| Skill | What it is for |
|---|---|
| `code-review` | Review changes since a commit/branch on two axes: repo standards and the originating spec. **Replaces the built-in `/code-review`**; the built-in stays available as `/review`. |
| `codebase-design` | Vocabulary for designing deep modules, interfaces and seams. |
| `diagnosing-bugs` | Diagnosis loop for hard bugs and performance regressions. |
| `domain-modeling` | Build and sharpen the domain model: glossary and ADRs. |
| `/grill-with-docs` | Relentless interview to sharpen a plan, writing glossary and ADRs as it goes. Runs `grilling` + `domain-modeling`. |
| `grilling` | Relentless interview about a plan or decision, in rounds of numbered questions with recommended answers. |
| `/implement` | Implement a piece of work from a spec or tickets. |
| `/improve-codebase-architecture` | Find deepening opportunities and present them as an HTML report. |
| `pr` | The shape a pull request body should take. |
| `prototype` | Throwaway prototype to answer a design question. |
| `research` | Research a question against primary sources into a Markdown file. |
| `/retro` | Retrospective on a coding session. Uses `writing-for-agents`. |
| `/setup-matt-pocock-skills` | Configure issue tracker and domain-doc layout. Run once (done; see `docs/agents/`). |
| `tdd` | Test-driven development, red-green-refactor. |
| `writing-for-agents` | Style guide for documents agents read: skills, `CLAUDE.md`, rules. |

## Not installed

Removed on 2026-10-19 because the team doesn't use them:

- `to-spec`, `to-tickets`, `triage`, `wayfinder`: issue-tracker workflows (specs, tickets,
  triage labels, decision maps).
- `implement-spec`: builds what `/to-spec` and `/to-tickets` produce, so it has no input
  without them. `/implement` covers single issues or specs.
- `ask-matt`: a router that mostly points to the skills above.
- `wizard`: generates bash scripts for manual setup steps.

`agents/openai.yaml` files are metadata for OpenAI Codex; Claude Code ignores them.
