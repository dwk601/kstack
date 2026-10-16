---
name: kstack-execute
description: Execute a kstack plan as a swarm, one worker and one independent reviewer per task, then one report. Use when the user invokes kstack-execute or after kstack-plan.
disable-model-invocation: true
---

# kstack execute

Shared rules: read `../kstack/SKILL.md` first.

A swarm: fan out one worker per task, drain them, return one report. Input is the plan in this conversation. If it is gone, rebuild it from the request, the code, and existing branches. Never invent one. No push, PR, or deploy here.

## 1. Frame

- Done means every acceptance criterion is met on the integration branch, or reported as blocked or a gap.
- Record the base SHA. Create the integration branch `kstack/<job>` from it. Run the full checks on base and note failures. A task must not add new ones.
- Keep one state table only you edit (a scratch file outside the repo): task, worker, branch, head SHA, verdict.

## 2. Fan out

- Start a worker for every ready task at once. A task is ready when its dependencies are merged into `kstack/<job>`. There is no worker cap.
- Each worker gets its own worktree and branch from `kstack/<job>`, and its model from `kstack-models cmd workers --index <task-number>`.
- Every brief stands alone: goal, owned files, acceptance criteria, check command, base SHA, dependency results, report format. Never send a bare "continue". Never run one task twice to pick a winner.
- Worker: implement, run the check, commit. Use `../kstack-debug/SKILL.md` for bugs, `../kstack-perf/SKILL.md` for speed, and `../kstack-verify/SKILL.md` for user-facing behavior. Report `task | SHA | files | check + result | assumptions`.
- On timeout, read the agent's output before resending.

## 3. Review each result

- As each worker reports, a reviewer reviews that SHA with `../kstack-review/SKILL.md`. The worker leaves the worktree untouched until the verdict.
- FAIL: the worker fixes every item and resubmits. After `max_fails` FAILs, block the task and skip its dependents.
- BLOCKED: fix the environment and review again. It is not a pass and not a strike.
- High-risk task: after PASS, `security_reviewer` reviews the same SHA. Merge needs both.
- A worker that dies, or reports without a SHA and check result, gets one fresh restart with the full brief. A second miss is a gap. A gap is not a pass.

## 4. Aggregate

- Merge passed tasks one at a time: rebase onto `kstack/<job>`, rerun the check, fast-forward. If the rebase changed code, review again. Then fan out the tasks that just became ready.
- When nothing is left to start, run the full checks on `kstack/<job>` and compare with base.
- With more than one task, `integration_reviewer` reviews the combined diff in integration mode. Its findings become tasks through the same flow. One repair round, rerun checks, stop.

## 5. Report

One table: acceptance criterion, task, SHA, check result, verdict. Then one line per open issue with evidence, then gaps, dropouts, blocked and skipped tasks, and checks not run. Keep unmerged work. Close only this job's agents and worktrees.
