---
name: kstack-execute
description: Execute a kstack plan. Workers build the tasks in parallel with per-task review, then a verification swarm proves the result. Use when the user invokes kstack-execute or after kstack-plan.
disable-model-invocation: true
---

# kstack execute

Shared rules: read `../kstack/SKILL.md` first.

Two fan-outs. Workers build the tasks, then a verification swarm that wrote none of the code proves the result. Input is the plan in this conversation. If it is gone, rebuild it from the request, the code, and existing branches. Never invent one. No push, PR, or deploy here.

There is no agent cap. Inside Herdr, give the job its own tab (`herdr tab create --label kstack-<job> --no-focus`, root pane in its JSON), start every agent of a fan-out at once, and split its panes (`herdr pane split <pane> --direction right|down --no-focus --cwd <worktree>`) in alternating directions so they stay usable. Outside Herdr, run the same agents one at a time in the same order.

## 1. Frame

- Done means every acceptance criterion is met on `kstack/<job>` and every verification lane passes, or the gap is reported.
- Record the base SHA. Create the integration branch `kstack/<job>` from it. Run the full checks on base and note failures. A task must not add new ones.
- Keep one state table only you edit (a scratch file outside the repo): task, worker, branch, head SHA, verdict, then one row per lane.

## 2. Build

- Start a worker for every ready task. A task is ready when its dependencies are merged into `kstack/<job>`.
- Each worker gets its own worktree and branch from `kstack/<job>`, and its model from `kstack-models cmd workers --index <task-number>`.
- Every brief stands alone: goal, owned files, acceptance criteria, check command, base SHA, dependency results, report format. Never send a bare "continue". Never run one task twice to pick a winner.
- Worker: implement, run the check, commit. Use `../kstack-debug/SKILL.md` for bugs, `../kstack-perf/SKILL.md` for speed, and `../kstack-verify/SKILL.md` for user-facing behavior. Report `task | SHA | files | check + result | assumptions`.
- On timeout, read the agent's output before resending.

## 3. Review each task

- As each worker reports, the `reviewer` reviews that SHA with `../kstack-review/SKILL.md` in code mode. The worker leaves the worktree untouched until the verdict.
- FAIL: the worker fixes every item and resubmits. After `max_fails` FAILs, block the task and skip its dependents.
- BLOCKED: fix the environment and review again. It is not a pass and not a strike.
- High-risk task: after PASS, the `security_reviewer` reviews the same SHA. Merge needs both.
- A worker that dies, or reports without a SHA and check result, gets one fresh restart with the full brief. A second miss is a gap. A gap is not a pass.

## 4. Integrate

- After PASS the worker is done and you own its branch. Merge passed tasks one at a time: rebase onto `kstack/<job>`, rerun the check, fast-forward. If the rebase changed code, review again. Then start the tasks that just became ready.
- When nothing is left to start, run the full checks on `kstack/<job>` and compare with base. Its head is the code-ready SHA.

## 5. Verification swarm

Fan out independent lanes at the code-ready SHA, each in its own detached worktree (`git worktree add --detach <path> <sha>`). Lanes never edit code. A lane's model comes from `kstack-models cmd verifiers --index <lane>`. The audit lanes take indexes 0 and 1, so they run on different models.

| Lane | How many | Does |
|---|---|---|
| Audit | 2 or more, each with its own focus | `../kstack-review/SKILL.md` audit mode on base..SHA |
| Gates | 1 | Full checks, lint, and typecheck at the SHA. Run it yourself; no agent needed |
| Live | One per user-visible behavior in the plan | `../kstack-verify/SKILL.md`: one scenario, saved evidence, pass rule. One lane runs the main scenario on base and head |
| Perf | Only when the plan has a speed target | `../kstack-perf/SKILL.md` on base and head |

Size the swarm to the change. Skip live lanes only when the project cannot run, and say so.

- Each lane reports PASS, FAIL, or BLOCKED with evidence and the SHA. Drop a report without the SHA and respawn that lane once. A second miss is a gap.
- Clean only when every lane passes. A defect base already has is recorded against base and does not gate the job.
- Every proven finding, however a lane labeled it, becomes a repair task through steps 2 to 4. One repair round. Then one verifier reruns the failed lanes at the new head. Run a full swarm again only for new behavior or a large new diff.

## 6. Report

Two tables: acceptance criterion, task, SHA, check result, verdict; and lane, SHA, verdict, evidence path. Then one line per open issue with evidence, then gaps, dropouts, blocked and skipped tasks, and checks not run. Keep unmerged work. Close only this job's agents, tab, and worktrees.
