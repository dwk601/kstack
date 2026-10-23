---
name: kstack
description: Route coding tasks through planning, implementation, verification and delivery.
disable-model-invocation: true
---

# kstack

All skills inherit these rules. Resolve sibling skills at `../<skill-name>/SKILL.md`:

| Request | Skill |
|---|---|
| Change | kstack-plan → kstack-execute; stop before publishing |
| Ship | kstack-finish |
| Explain | kstack-understand |
| Diagnose / measure | kstack-debug / kstack-perf, read-only |
| Review / prove | kstack-review / kstack-verify |
| Prevent repeats / configure | kstack-improve / kstack-setup |

## Shared rules

- Complete requested scope without reasking; stop after acceptance/checks or a named blocker/budget. Report unrelated improvements instead of implementing them.
- Prefer targeted edits and repo-sized tests. Run real checks; syntax/failed startup is insufficient. Never weaken checks: unavailable required checks are BLOCKED; unmet acceptance is partial.
- Code changes use kstack-plan → kstack-execute. Assigned workers skip nested workflows/agents. One writer per branch/worktree; reviewers/verifiers leave source unchanged.
- Only kstack-finish publishes/merges/deploys. Read `../kstack-finish/SKILL.md` for inventory; use its cleanup reference for resource deletion, without starting delivery.
- Batch independent calls. Update at start/milestones; finish with results/evidence/blockers. Distinguish measured facts/inference/guesses.

## No saved run artifacts

Keep inventory/results in conversation/stdout, never files inside or outside repo. No saved logs/notes/reports/plans/state, redirect/tee, archive relocation or leftover logs-path footer. Preserve product files, application logs/config/docs and user data; requested changes remain allowed.

Limit output. Delete exact owned overflow logs only under cleanup safeguards, never sweep caches. Avoid captures; unavoidable data uses inventoried owned TMPDIR scratch (unset/empty: platform fallback).

Before every settled return: stop exact owned temporary PIDs, capture results, delete safe owned scratch/disposable verifiers, read back absence. This never waits for merge/delivery. Retain unmerged source/unique code; unsafe cleanup is partial with exact blocker. Resume from conversation plus actual Git/PR state, not saved logs.

## Dispatch

Set MODELS to absolute `../kstack-setup/scripts/kstack-models`; run `python3 "$MODELS" validate`, using kstack-setup if missing. Run printed commands in assigned checkouts.

Inside Herdr (`HERDR_ENV=1`):
1. Split: `herdr pane split --current --direction right --cwd <path> --no-focus`.
2. Launch: `python3 "$MODELS" cmd <role> --herdr <name> --pane <returned-id>`.
3. Dispatch: `herdr agent prompt <name> "<brief>"`, without --wait; continue independent work.
4. Collect: `herdr agent list`, then `herdr agent read <name> --source recent-unwrapped --lines 120`. If none ready, `herdr agent wait <name> --timeout 120000`, then read.

Idle/submission isn't completion: require assignment stdout. Inspect blockers/timeouts; retry collection, not blind resends/approvals. Missing results are verification gaps, never report files.

Outside Herdr, leave its sessions alone. Run foreground agents sequentially via `python3 "$MODELS" cmd <role> --oneshot`, brief last; no hidden background agents.
