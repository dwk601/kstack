---
name: kstack
description: Plan, build, verify, and finish delivery of coding tasks.
disable-model-invocation: true
---

# kstack

All skills inherit these rules. This entrypoint routes requests:

| Request | Skills |
|---|---|
| Change code | Plan then Execute; stop before publishing |
| Ship | Finish |
| Explain | Understand |
| Diagnose / measure | Debug / Perf, read-only |
| Review / prove | Review / Verify |
| Prevent repeats / configure | Improve / Setup |

## Shared rules

- Standalone code-changing Debug/Perf/Improve uses Plan then Execute. Assigned workers follow their method without nested workflows or agents.
- One writer per branch/worktree. Independent reviewers/verifiers never edit source. Prefer a different model; disclose same-model fallback. Verifiers may share models.
- Never weaken checks. Unavailable required checks are BLOCKED; unmet acceptance means partial. No test-first mandate.
- Only Finish publishes, merges, deploys or cleans delivery resources. Read only the rules in `../kstack-finish/SKILL.md` for permissions, inventory and cleanup; do not start its workflow. Execute may clean disposable verifiers; preserve unmerged source.
- Keep instructions minimal. Define shared rules once; replace obsolete wording.

## No saved run artifacts

Keep ownership inventory in conversation/memory or stdout, never files inside or outside repo. No logs, notes, reports, plans, manifests, state files, redirect/tee, saved-report fallback, archive/cache relocation or leftover logs-path footer. Preserve application logs/config/docs, product files and user data; requested product/config/docs changes are allowed.

Limit output. Remove only exact tool-generated overflow logs using Finish's artifact checks; never sweep caches. Avoid captures. Unavoidable tests/screenshots use inventoried, owned TMPDIR scratch; unset/empty uses the platform fallback.

Before every settled return (success, failure, blocked, pending, timeout, pr-green, handoff), stop temporary processes by exact PID first. Capture results in conversation, delete exact owned scratch/disposable verifier worktrees under Finish's safety checks, then read back absence. Cleanup never waits for merge/delivery. Retain unmerged source branches/worktrees and unique code. Unsafe deletion means cleanup partial with exact blocker.

Resume from conversation plus actual Git/PR state, never saved logs.

## Dispatch and collect

For dispatch, set MODELS to absolute `../kstack-setup/scripts/kstack-models`; run `python3 "$MODELS" validate`. Use Setup if missing. Run printed commands in the assigned checkout.

Inside Herdr (`HERDR_ENV=1`):
1. `herdr pane split --current --direction right --cwd <path> --no-focus` (or down); use returned pane ID.
2. Run the command from `python3 "$MODELS" cmd <role> --herdr <name> --pane <id>`.
3. Dispatch ready agents with `herdr agent prompt <name> "<brief>"`, without --wait.
4. Collect via `herdr agent list` and `herdr agent read <name> --source recent-unwrapped --lines 120`. If none ready, `herdr agent wait <name> --timeout 120000`, then read.

Submission/idle is not completion; require assignment stdout. Inspect blocked/unknown/timeouts; never blindly resend or answer approvals. Retry collection/request stdout summary; still missing means verification gap, never report files.

Outside Herdr, never inspect/control its session. Run foreground agents sequentially via `python3 "$MODELS" cmd <role> --oneshot`, brief last. No hidden background agents.
