---
name: kstack
description: Route coding tasks through planning, implementation, verification and delivery.
disable-model-invocation: true
---

# kstack

All skills inherit these rules; siblings: `../<skill-name>/SKILL.md`:

| Request | Skill |
|---|---|
| Change | kstack-plan → kstack-execute; stop before publishing |
| Ship | kstack-finish |
| Explain | kstack-understand |
| Diagnose / measure | kstack-debug / kstack-perf, read-only |
| Review / prove | kstack-review / kstack-verify |
| Prevent repeats / configure | kstack-improve / kstack-setup |

## Shared rules

- Complete scope without reasking; stop at acceptance/checks or named blocker/budget. Only report unrelated improvements.
- Use targeted edits/repo-sized tests. Real checks, not syntax/failed startup. Never weaken checks: missing required checks are BLOCKED; unmet acceptance is partial.
- Assigned workers skip nested workflows/agents. One writer per branch/worktree; reviewers/verifiers leave source unchanged.
- Only kstack-finish publishes/merges/deploys. Inventory/deletion: read `../kstack-finish/SKILL.md` and its cleanup reference; do not start delivery.
- Batch independent calls; update at start/milestones. Return results/evidence/blockers; label facts/inference/guesses. Hand off unresolved findings/evidence, not reasoning/transcripts.
- User corrections or machine-checkable review FAILs: report as kstack-improve candidates; do not implement them.

## No saved run artifacts

Keep inventory/results in conversation/stdout, never files inside or outside repo. No saved logs/notes/reports/plans/state, redirect/tee, archive relocation or leftover logs-path footer. Preserve product files, application logs/config/docs and user data; requested changes remain allowed.

Limit output. Delete exact owned overflow logs under cleanup safeguards; never sweep caches. Avoid captures; unavoidable data: inventoried owned TMPDIR scratch (unset/empty: platform fallback).

Before every settled return: stop exact owned temporary PIDs, capture results, delete safe owned scratch/disposable verifiers, read back absence. This never waits for merge/delivery. Retain unmerged source/unique code; unsafe cleanup is partial with exact blocker. Resume from conversation plus actual Git/PR state, not saved logs.

kstack-plan, kstack-execute and kstack-finish coordinators read `references/dispatch.md` before starting agents.
