---
name: kstack-execute
description: Implement and verify reviewed tasks.
disable-model-invocation: true
---

# kstack-execute

Shared rules: read `../kstack/SKILL.md` first.

Use chat plan or request/code; inventory resources under kstack-finish as created. Stop before publishing.

## 1. Frame

Base: request, project, then default branch. Record SHA; create `kstack/<job>`, baseline checks, resume without reset. In chat: task/agent/branch/base/head/verdict/evidence; distinguish baseline failures.

## 2. Build and review

Dispatch after dependencies integrate: `python3 "$MODELS" cmd workers`. Workers own integration-based branches/worktrees. Brief goal/files/acceptance/checks/base SHA/dependencies; workers implement/check/commit; return `task | SHA | files | checks + results | assumptions`.

Independent `reviewer`: `../kstack-review/SKILL.md` task review at frozen base/head. FAIL → worker, bounded by `execution.max_fails`. BLOCKED: no strike; fix environment or mark partial. No report: stop old writer; one fresh attempt, then gap. Skip blocked dependents; preserve work.

## 3. Integrate

Pause worker; serially rebase/check/fast-forward. Worker resolves conflicts; reviewer checks. Record reviewed final worker tip after rebase, evidence, integration SHA; unlock dependents.

Account for every started agent/task and known repair before freezing head. Prove `git merge-base --is-ancestor <worker-tip> <frozen-head>`, not PR-head equality. Retain advanced/unintegrated refs. Renew proof after rewrites or retain. Unfinished tasks: partial.

## 4. Verification swarm

kstack-finish reuses this stage, no builds. Supply request/exact base/head/acceptance/scenarios/pass conditions/commands/outcomes; infer scenarios from diff/repo.

At frozen head: `git worktree add --detach <path> <sha>`; `python3 "$MODELS" cmd verifiers --index <lane>`:

| Lane | Evidence |
|---|---|
| Audit | kstack-review |
| Gates | Full checks/lint/typecheck; coordinator may run |
| Live | kstack-verify every mapped feature plus changed behavior; compare a main scenario to base |
| Perf | kstack-perf speed targets without edits |
| Formal | Default: repo-framework property-based tests; TLA+/Lean only with existing tooling. Show each property fail on a deliberately broken variant (mutation), only in verifier's disposable worktree; revert before `../kstack-finish/scripts/kstack-git` remove-worktree, source unchanged. Never weaken properties; counterexamples are findings. No plan flags: N/A with reason. |

Follow `../kstack-finish/references/efficiency.md`. Return `base/head | PASS/FAIL/BLOCKED | commands + evidence`. Missing evidence: one retry, then gap; N/A needs reason. Base defects count only if copied/worsened/newly exposed.

Allow one swarm repair round through steps 2–3, batching all lanes' findings; kstack-finish uses `finish.max_fix_rounds`. Small repairs/rebases: one independent verifier inspects diff, reruns gates and affected/failed scenarios, justifies reuse per lane. New behavior/large diffs: full swarm within budget; exhaustion is partial.

## 5. Report

Report task/revision/check/verdict, lanes, findings/gaps. Completion needs acceptance, required lanes, shared cleanup safeguards/readback; separate delivery-resource/diagnostic cleanup.
