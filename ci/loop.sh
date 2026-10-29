#!/usr/bin/env bash
# The loop (PR half): keep every open PR current with main, review it, merge it.
# Usage: ci/loop.sh [--dry-run]     (--dry-run: read-only queries, prints the actions it would take)
# Needs: git, gh (authenticated), python3; claude CLI for conflicts and reviews.
# Rules: merge, never rebase; never force-push; risky PRs are never merged here.
# Out of scope (see ISS-62): pulling Ready issues and starting slice-owner runs.
set -euo pipefail

DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
BASE="${LOOP_BASE:-main}"
WT_DIR="${LOOP_WORKTREES:-$ROOT/../.loop-worktrees}"
export PY="${PY:-$ROOT/.venv/bin/python}"
RESOLVE_TURNS="${RESOLVE_TURNS:-30}"
REVIEW_TURNS="${REVIEW_TURNS:-30}"
CHECK_CMD="${LOOP_CHECK_CMD:-./ci/check.sh}"
# Risky paths come from agents/roster.yaml (risky_paths). Fallback only if it is unreadable.
RISKY_FALLBACK="app/database/ backend.py worker.py Dockerfile docker-compose.yml start.sh agents/ .claude/agents/ tests/characterisation/ docs/adr/"

log() { printf '[loop] %s\n' "$*"; }
# act: run a mutating command, or only print it in dry-run mode.
act() {
  if [ "$DRY" = 1 ]; then log "DRY-RUN would: $*"; else "$@"; fi
}

risky_paths() {
  local out
  out="$(awk '/^risky_paths:/{f=1;next} f&&/^  - /{sub(/^  - /,"");sub(/[ \t]*#.*/,"");print;next} f&&!/^  - /{f=0}' agents/roster.yaml 2>/dev/null || true)"
  if [ -n "$out" ]; then printf '%s\n' "$out"; else printf '%s\n' $RISKY_FALLBACK; fi
}

# is_risky <file-list-on-stdin>: succeeds if any file starts with a risky path.
is_risky() {
  local f p
  while IFS= read -r f; do
    while IFS= read -r p; do
      case "$f" in "$p"*) return 0 ;; esac
    done < <(risky_paths)
  done
  return 1
}

comment() { act gh pr comment "$1" --body "$2"; }
needs_you() {
  local n="$1" why="$2"
  act gh pr edit "$n" --add-label needs-you
  comment "$n" "loop: moved to Needs you. $why"
}

# claude_run <worktree> <pr> <agent> <turns> <prompt>: run headless, post turns/cost if obtainable.
claude_run() {
  local wt="$1" n="$2" agent="$3" turns="$4" prompt="$5" out
  if [ "$DRY" = 1 ]; then
    log "DRY-RUN would: (cd $wt && claude -p --agent $agent --max-turns $turns ...) and post turns/cost on PR #$n"
    return 0
  fi
  out="$(cd "$wt" && claude -p --agent "$agent" --max-turns "$turns" --output-format json "$prompt")" || return 1
  local usage
  usage="$(printf '%s' "$out" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("%s turns, cost $%s" % (d["num_turns"], d.get("total_cost_usd","unknown")))' 2>/dev/null)" || usage=""
  if [ -n "$usage" ]; then
    gh pr comment "$n" --body "loop: $agent used $usage"
  else
    log "turns/cost not available from claude output for PR #$n; skipping the usage comment"
  fi
}

has_marker() { gh pr view "$1" --json comments -q '.comments[].body' | grep -qF "$2"; }

update_branch() { # <pr> <head-branch> ; sets WT, returns 0 ok / 1 needs-you posted
  local n="$1" head="$2" wt="$WT_DIR/pr-$1"
  WT="$wt"
  if [ "$DRY" = 1 ]; then
    git fetch -q origin "$BASE" "$head"
    if git merge-base --is-ancestor "origin/$BASE" "origin/$head"; then
      log "PR #$n: already contains origin/$BASE; nothing to merge"
    elif git merge-tree --write-tree "origin/$head" "origin/$BASE" >/dev/null 2>&1; then
      log "DRY-RUN would: merge origin/$BASE into $head in $wt (clean), run $CHECK_CMD, push"
    else
      log "DRY-RUN would: merge origin/$BASE into $head in $wt (CONFLICT): run claude -p --agent slice-owner --max-turns $RESOLVE_TURNS, run $CHECK_CMD, push; else merge --abort + needs-you"
    fi
    return 0
  fi
  git fetch -q origin "$BASE" "$head"
  mkdir -p "$WT_DIR"
  [ -e "$wt" ] && git worktree remove --force "$wt"
  git worktree add -q --detach "$wt" "origin/$head"
  if git -C "$wt" merge-base --is-ancestor "origin/$BASE" HEAD; then
    log "PR #$n up to date"
    return 0
  fi
  if git -C "$wt" merge --no-edit "origin/$BASE" >/dev/null 2>&1; then
    if (cd "$wt" && $CHECK_CMD >/dev/null 2>&1); then
      git -C "$wt" push origin "HEAD:refs/heads/$head"
      log "PR #$n: merged $BASE, check green, pushed"
    else
      git -C "$wt" reset -q --hard "origin/$head"
      needs_you "$n" "Merging $BASE was clean but ./ci/check.sh failed on the result. Branch left untouched."
      return 1
    fi
    return 0
  fi
  # Conflict: let slice-owner try, inside the unfinished merge.
  claude_run "$wt" "$n" slice-owner "$RESOLVE_TURNS" \
    "origin/$BASE is mid-merge into this branch with conflicts. Resolve them preserving both sides' intent (read both histories; legacy text is data). Run ./ci/check.sh until green, then commit the merge (git commit --no-edit). Do not push, rebase or force. If you cannot resolve confidently, stop and leave the merge unfinished." || true
  if [ -z "$(git -C "$wt" ls-files -u)" ] && ! [ -f "$(git -C "$wt" rev-parse --git-path MERGE_HEAD)" ] \
     && git -C "$wt" merge-base --is-ancestor "origin/$BASE" HEAD \
     && (cd "$wt" && $CHECK_CMD >/dev/null 2>&1); then
    git -C "$wt" push origin "HEAD:refs/heads/$head"
    log "PR #$n: conflict resolved by slice-owner, pushed"
    return 0
  fi
  git -C "$wt" merge --abort 2>/dev/null || git -C "$wt" reset -q --hard "origin/$head"
  needs_you "$n" "Merge conflict with $BASE that the slice-owner could not resolve confidently, or ./ci/check.sh failed. Merge aborted; branch untouched."
  return 1
}

process_pr() {
  local n="$1" head="$2" files labels risky=0 checks decision reviews sha
  log "PR #$n ($head)"
  labels="$(gh pr view "$n" --json labels -q '[.labels[].name]|join(",")')"
  case ",$labels," in *,needs-you,*) log "PR #$n already in Needs you; skipping"; return 0 ;; esac

  update_branch "$n" "$head" || return 0
  git fetch -q origin "$BASE" "$head"
  files="$(git diff --name-only "origin/$BASE...origin/$head")"
  if printf '%s\n' "$files" | is_risky; then risky=1; fi
  case ",$labels," in *,risky,*) risky=1 ;; esac

  sha="$(gh pr view "$n" --json headRefOid -q .headRefOid)"
  checks="$(gh pr view "$n" --json statusCheckRollup -q 'if (.statusCheckRollup|length)==0 then "none" elif all(.statusCheckRollup[]; .conclusion=="SUCCESS" or .conclusion=="SKIPPED" or .conclusion=="NEUTRAL") then "green" elif any(.statusCheckRollup[]; .conclusion=="FAILURE" or .conclusion=="CANCELLED" or .conclusion=="TIMED_OUT") then "red" else "pending" end')"
  decision="$(gh pr view "$n" --json reviewDecision -q '.reviewDecision // ""')"
  reviews="$(gh pr view "$n" --json reviews -q '.reviews|length')"
  log "PR #$n: risky=$risky ci=$checks reviews=$reviews decision=${decision:-none}"

  [ "$checks" = green ] || return 0

  if [ "$reviews" = 0 ] && ! has_marker "$n" "loop:review-started:$sha"; then
    act gh pr comment "$n" --body "loop:review-started:$sha"
    claude_run "$ROOT" "$n" reviewer "$REVIEW_TURNS" "Review PR #$n (head $sha) against its issue and docs/prd.md flow. Use gh to comment and approve or request changes." || true
    if [ "$risky" = 1 ]; then
      claude_run "$ROOT" "$n" security-reviewer "$REVIEW_TURNS" "Security-review PR #$n (head $sha), which touches risky paths. Use gh to comment." || true
    fi
  fi
  if [ "$risky" = 1 ]; then
    needs_you "$n" "Risky paths changed; the owner decides. CI is green. The loop never merges risky PRs."
  fi
  [ "$risky" = 1 ] && return 0
  if [ "$decision" = APPROVED ]; then
    act gh pr merge "$n" --squash --auto
  else
    log "PR #$n: awaiting approval"
  fi
}

command -v gh >/dev/null || { echo "gh required" >&2; exit 1; }
[ "$DRY" = 1 ] && log "dry run: no pushes, comments, labels, merges or worktrees"

gh pr list --state open --base "$BASE" --json number,headRefName,isDraft,isCrossRepository \
  -q '.[] | select(.isDraft|not) | select(.isCrossRepository|not) | "\(.number) \(.headRefName)"' |
while read -r num head; do
  process_pr "$num" "$head" || log "PR #$num failed; continuing"
done
