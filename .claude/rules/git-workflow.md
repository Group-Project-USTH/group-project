# Git workflow

- Branch from an up-to-date `main` (`feat/`, `fix/`, `chore/`, `docs/`, `test/`, `ci/`).
  Never commit or push to `main`.
- Small PRs: one topic each, reviewable in one sitting.
- Conventional Commits (`feat: …`, `fix: …`, `chore: …`, `docs: …`, `test: …`, `ci: …`);
  each commit should pass CI on its own. The PR title follows the same format.
- Fill in `.github/PULL_REQUEST_TEMPLATE.md`, including the exact commands you ran.
- Merge needs: CI `lint-typecheck-test` green, branch up to date with `main`, 1 approval,
  all review threads resolved. Squash merge.
- The repo owner (`mingming1509`) can bypass the `main` ruleset. That bypass is for the
  owner, not for Claude: even when running with the owner's `gh` login, never push to
  `main`, and merge a PR (including `gh pr merge --admin`) only when the user asks.
- Never force-push a shared branch; never rewrite `main`.
- Don't change GitHub settings (rulesets, secrets, repo options) without asking the user.
