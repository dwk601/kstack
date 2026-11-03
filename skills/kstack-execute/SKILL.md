---
name: kstack-execute
description: Implement and verify reviewed tasks.
disable-model-invocation: true
---

# kstack-execute

Shared rules: read `../kstack/SKILL.md` first.

Use chat plan or reconstruct from request/code; inventory resources under kstack-finish as created. Stop before publishing.

## 1. Frame

Resolve base from request, project, then default branch. Record SHA; create `kstack/<job>`, baseline checks, resume without reset. Track task/agent/branch/base/head/verdict/evidence in chat; distinguish baseline failures.

## 2. Build and review

Dispatch ready tasks after dependencies integrate: `python3 "$MODELS" cmd workers`. Each worker owns an integration-based branch/worktree. Brief goal, files, acceptance, checks, base SHA, dependencies; workers implement/check/commit and return `task | SHA | files | checks + results | assumptions`.

Independent `reviewer`: `../kstack-review/SKILL.md` at frozen base/head, including scope/regressions for audit reuse. FAIL returns to worker, bounded by `execution.max_fails`. BLOCKED is not a strike: repair environment or mark partial. Missing worker reports get one fresh attempt after stopping old writer, then a gap. Skip blocked dependents; preserve work.

## 3. Integrate

Pause worker; serially rebase, rerun checks and fast-forward. Worker resolves conflicts; reviewer checks. Record reviewed final worker tip after rebase, evidence and integration SHA; unlock dependents.

Account for every started agent/task before freezing head. Prove `git merge-base --is-ancestor <worker-tip> <frozen-head>`, not PR-head equality. Retain advanced/unintegrated refs. Renew proof after rewrites or retain. Unfinished tasks mean partial.

## 4. Verification swarm

kstack-finish reuses this stage without builds. Supply request, exact base/head, acceptance, scenarios/pass conditions, commands and outcomes; infer missing scenarios from diff/repo.

Lanes use `git worktree add --detach <path> <sha>` at frozen head and `python3 "$MODELS" cmd verifiers --index <lane>`:

| Lane | Evidence |
|---|---|
| Audit | kstack-review |
| Gates | Full checks/lint/typecheck; coordinator may run |
| Live | kstack-verify changed user-visible behavior; compare a main scenario to base |
| Perf | kstack-perf speed targets without edits |

Follow `../kstack-finish/references/efficiency.md`. Return `base/head | PASS/FAIL/BLOCKED | commands + evidence`. Missing evidence gets one retry, then a gap; N/A needs reason. Base defects count only if copied, worsened or newly exposed.

Allow one swarm repair round through steps 2–3; kstack-finish uses `finish.max_fix_rounds`. Small repairs/rebases need one independent verifier to inspect diff, rerun gates and affected/failed scenarios, and justify reuse. New behavior/large diffs require full swarm within budget; exhaustion means partial.

## 5. Report

Report task/revision/check/verdict, lanes, findings and gaps. Completion needs acceptance, required lanes and shared cleanup safeguards/readback; distinguish delivery-resource and diagnostic cleanup.
