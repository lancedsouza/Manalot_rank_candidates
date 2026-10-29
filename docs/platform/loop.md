# The loop (`ci/loop.sh`)

Keeps open PRs current with `main`, starts reviews and merges approved, green, non-risky PRs.

Run: `./ci/loop.sh --dry-run` (prints actions, changes nothing), then `./ci/loop.sh`. Needs `gh` (logged in), `git`, `python3`, `claude`, and the venv from `AGENTS.md`. Worktrees go in `../.loop-worktrees` (`LOOP_WORKTREES`). Safe to re-run: reviews are marked per head SHA, `needs-you` PRs are skipped.

Per PR: merge `origin/main` (never rebase or force-push) -> `./ci/check.sh` -> push. Conflicts go to `slice-owner` (30 turns); if unresolved or red, the merge is aborted and the PR gets `needs-you` plus a comment. Green CI and no review starts `reviewer` (and `security-reviewer` when `risky_paths` in `agents/roster.yaml` changed). Approved non-risky PRs get `gh pr merge --squash --auto`; risky PRs get `needs-you` and are never merged. Turns and cost are posted from `claude --output-format json` when present.

Not done here: pulling Ready issues and starting slice-owner runs (skip modules already In progress); the Needs you label must exist already.

## Owner settings (the loop does not change these)
- Create the `needs-you` label.
- Branch protection on `main`: require the CI check and "Require branches to be up to date before merging"; require one approving review; CODEOWNERS review for risky paths.
- Settings > General: "Allow auto-merge". Optional: a merge queue (then `--auto` enqueues).
