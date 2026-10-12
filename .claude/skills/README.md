# Project skills

The skills in this folder are **third-party**: Matt Pocock's engineering skills, copied
unmodified. They steer the agent, so they are updated deliberately (see below), never
automatically.

| | |
|---|---|
| Source | https://github.com/mattpocock/skills, folder `skills/engineering` |
| Commit | `49dd158d1076134a641b33efb035946536778336` (2026-10-09) |
| Installed | 2026-10-12 |
| License | MIT, © 2026 Matt Pocock: see [`LICENSE`](LICENSE) |

Installed with (real copies, no symlinks; the generated `skills-lock.json` was deleted
because this file records the commit instead):

```bash
DO_NOT_TRACK=1 npx -y skills@1.7.2 add mattpocock/skills --agent claude-code --copy -y \
  --skill ask-matt code-review codebase-design diagnosing-bugs domain-modeling \
  grill-with-docs implement implement-spec improve-codebase-architecture pr prototype \
  research retro setup-matt-pocock-skills tdd to-spec to-tickets triage wayfinder wizard
```

## Updating

1. On a `chore/` branch, list `skills/engineering` upstream
   (`gh api repos/mattpocock/skills/contents/skills/engineering`) and adjust the
   `--skill` list for added, removed or deprecated skills. Delete folders of skills that
   were removed upstream.
2. Re-run the command above from the repo root, then `rm skills-lock.json`.
3. Review `git diff .claude/skills` like any third-party code: look for new shell
   commands, network access, file access outside the repo, or new `allowed-tools`/`hooks`.
4. Update the commit, date and table in this file and open a PR.

## Skills

`/name` = only runs when you type it. Others Claude may also load on its own.

| Skill | What it is for |
|---|---|
| `/ask-matt` | Ask which skill or flow fits your situation. |
| `code-review` | Review changes since a commit/branch on two axes: repo standards and the originating spec. **Replaces the built-in `/code-review`**; the built-in stays available as `/review`. |
| `codebase-design` | Vocabulary for designing deep modules, interfaces and seams. |
| `diagnosing-bugs` | Diagnosis loop for hard bugs and performance regressions. |
| `domain-modeling` | Build and sharpen the domain model: glossary and ADRs. |
| `/grill-with-docs` | Relentless interview to sharpen a plan, writing glossary and ADRs as it goes. |
| `/implement` | Implement a piece of work from a spec or tickets. |
| `/implement-spec` | Implement a whole spec from `/to-spec` + `/to-tickets` (parallel sub-agents). |
| `/improve-codebase-architecture` | Find deepening opportunities and present them as an HTML report. |
| `pr` | The shape a pull request body should take. |
| `prototype` | Throwaway prototype to answer a design question. |
| `research` | Research a question against primary sources into a Markdown file. |
| `/retro` | Retrospective on a coding session. |
| `/setup-matt-pocock-skills` | Configure issue tracker, triage labels and domain-doc layout. Run once. |
| `tdd` | Test-driven development, red-green-refactor. |
| `/to-spec` | Turn the conversation into a spec on the issue tracker. |
| `/to-tickets` | Break a plan or spec into tracer-bullet tickets. |
| `/triage` | Move issues through triage states and write agent-ready briefs. |
| `/wayfinder` | Plan a large piece of work as a map of decision tickets. |
| `wizard` | Generate an interactive bash script for steps only a human can do. Its scripts write `.env` and set GitHub secrets when *a person* runs them. |

`agents/openai.yaml` files are metadata for OpenAI Codex; Claude Code ignores them.
