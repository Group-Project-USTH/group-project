#!/usr/bin/env bash
# Apply .github/rulesets/main.json to the repository's default branch (main).
#
# NOT run automatically. Requires `gh` authenticated as a repo admin.
#
# Usage:
#   scripts/apply_branch_protection.sh [OWNER/REPO] [--dry-run]   (any order)
#
# What it changes on GitHub:
#   1. Creates (or updates, if one with the same name exists) the repository
#      ruleset "main-branch-protection": PR required with 1 approval, stale
#      approvals dismissed, conversations resolved, required status check
#      `lint-typecheck-test` (GitHub Actions, branch up to date), linear
#      history, no force-push, no deletion, squash merges only.
#   2. Repo merge settings: allow squash merges only,
#      delete head branches after merge.
#
# Rulesets need a public repo, or a paid plan (Pro/Team) for private repos.
set -euo pipefail

DRY_RUN=0
REPO=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -*) echo "Unknown option: $arg" >&2; exit 2 ;;
    *)
      if [[ -n "$REPO" ]]; then
        echo "Only one OWNER/REPO allowed, got '$REPO' and '$arg'" >&2
        exit 2
      fi
      REPO="$arg"
      ;;
  esac
done
REPO="${REPO:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
RULESET_FILE="$(cd "$(dirname "$0")/.." && pwd)/.github/rulesets/main.json"
RULESET_NAME="$(jq -r .name "$RULESET_FILE")"

existing_id="$(gh api "repos/$REPO/rulesets" --jq ".[] | select(.name == \"$RULESET_NAME\") | .id")"

if [[ -n "$existing_id" ]]; then
  method=PUT
  endpoint="repos/$REPO/rulesets/$existing_id"
else
  method=POST
  endpoint="repos/$REPO/rulesets"
fi

echo "Repository:   $REPO"
echo "Ruleset:      $RULESET_NAME ($([[ -n "$existing_id" ]] && echo "update id $existing_id" || echo "create"))"
echo "Request:      $method $endpoint"
echo "Merge config: allow_merge_commit=false allow_squash_merge=true allow_rebase_merge=false delete_branch_on_merge=true"

if [[ "$DRY_RUN" == 1 ]]; then
  echo "Dry run: nothing changed."
  exit 0
fi

gh api --method "$method" "$endpoint" --input "$RULESET_FILE" \
  --jq '"Ruleset applied: id=\(.id) enforcement=\(.enforcement) rules=\([.rules[].type] | join(","))"'

gh api --method PATCH "repos/$REPO" \
  -F allow_merge_commit=false \
  -F allow_squash_merge=true \
  -F allow_rebase_merge=false \
  -F delete_branch_on_merge=true \
  --jq '"Merge settings: merge_commit=\(.allow_merge_commit) squash=\(.allow_squash_merge) rebase=\(.allow_rebase_merge) delete_branch_on_merge=\(.delete_branch_on_merge)"'
