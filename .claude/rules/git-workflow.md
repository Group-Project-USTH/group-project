# Git workflow

- Branch from an up-to-date `main` (`feat/`, `fix/`, `chore/`, `docs/`, `test/`, `ci/`).
  Never commit or push to `main`. When a skill says "commit to the current branch" (e.g.
  `/implement`) and you are on `main`, create a branch first.
- Small PRs: one topic each, reviewable in one sitting.
- Conventional Commits (`feat: …`, `fix: …`, `chore: …`, `docs: …`, `test: …`, `ci: …`);
  each commit should pass CI on its own. The PR title follows the same format.
- Fill in `.github/PULL_REQUEST_TEMPLATE.md`, including the exact commands you ran. Its
  headings win over the `pr` skill's template; use that skill only for what goes inside
  them (diagrams or diff sketches in Summary, before/after in How tested).
- Merge needs: CI `lint-typecheck-test` green, branch up to date with `main`, 1 approval,
  all review threads resolved. Squash merge only.
- The repo owner (`mingming1509`) can bypass the `main` ruleset. That bypass is for the
  owner, not for Claude: even when running with the owner's `gh` login, never push to
  `main`, and merge a PR (including `gh pr merge --admin`) only when the user asks.
- Never force-push a shared branch; never rewrite `main`.
- Don't change GitHub settings (rulesets, secrets, repo options) without asking the user.
