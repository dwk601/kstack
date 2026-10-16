---
name: kstack-execute
description: Execute a kstack plan as a swarm with one worker and one independent reviewer per task. Use when the user invokes kstack-execute or after kstack-plan.
disable-model-invocation: true
---

# kstack execute

Input: the plan in this conversation. If it is gone, rebuild it from the request, the code, and existing branches. Never invent one. No push, PR, or deploy here.

## Start

1. Record the base SHA. Create the integration branch `kstack/<job>` from it. Run the full checks on base and note failures. Base failures are not task failures, but a task must not add new ones.
2. Keep one state table you alone edit (a scratch file outside the repo is fine): task, status, worker, branch, head SHA, verdict.

## Swarm

- A task is ready when its dependencies are merged into the integration branch.
- Run up to `max_workers` ready tasks at once. Each gets its own worktree and branch from the integration branch, a worker (`kstack-models cmd workers --index <task-number>`), and a reviewer. Refill as tasks finish. Never run one task twice to pick a winner.
- Every brief is complete: task, owned files, acceptance, check command, dependency results, latest findings. Never send a bare "continue".
- On timeout, read the agent's output before resending.

Worker: implement, run the check, commit. Report `task | SHA | files | check + result | assumptions`. Use `../kstack-debug/SKILL.md` for bugs and `../kstack-perf/SKILL.md` for speed work.

Reviewer: review that SHA with `../kstack-review/SKILL.md`. The worker leaves the worktree untouched until the verdict.

- FAIL: the worker fixes every item and resubmits. After `max_fails` FAILs, block the task and skip its dependents.
- BLOCKED: fix the environment and review again. It is not a pass and not a strike.
- High-risk task: after PASS, `security_reviewer` reviews the same SHA. Merge needs both.

## Integrate

One task at a time: rebase onto the integration branch, rerun its check, fast-forward. If the rebase changed the code, review again. Then unlock dependents.

## Close

1. Run the full checks on the integration branch. Compare with base.
2. With more than one task, `integration_reviewer` reviews the combined diff in integration mode. Its findings become tasks through the same worker and reviewer flow. One repair round, rerun checks, stop.
3. Prove user-facing behavior with `../kstack-verify/SKILL.md` when the project can run.
4. Report each acceptance criterion: task, SHA, check result, verdict. Then blocked and skipped tasks, and checks not run. Keep unmerged work.
