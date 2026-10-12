# Git workflow

- Branch from an up-to-date `main` (`feat/`, `fix/`, `chore/`, `docs/`, `test/`, `ci/`).
  Never commit or push to `main`.
- Small PRs: one topic each, reviewable in one sitting.
- Conventional Commits (`feat: …`, `fix: …`, `chore: …`, `docs: …`, `test: …`, `ci: …`);
  each commit should pass CI on its own. The PR title follows the same format.
- Fill in `.github/PULL_REQUEST_TEMPLATE.md`, including the exact commands you ran.
- Merge needs: CI `lint-typecheck-test` green, branch up to date with `main`, 1 approval,
  all review threads resolved. Squash merge.
- Never force-push a shared branch; never rewrite `main`.
- Don't change GitHub settings (rulesets, secrets, repo options) without asking the user.
