---
name: kstack-execute
description: Build reviewed tasks, integrate, and verify the result.
disable-model-invocation: true
---

# kstack execute

Shared rules: read `../kstack/SKILL.md` first.

Use chat plan or reconstruct from request/code; inventory resources under Finish as created.

## 1. Frame

Resolve base from request, project, then default branch. Record SHA; create `kstack/<job>`, run baseline checks. Resume without reset. Track task/agent/branch/base/head/verdict/evidence in chat; separate baseline failures.

## 2. Build

Dispatch all ready tasks after dependencies integrate; no worker cap. Each owns a branch/worktree from integration and uses `python3 "$MODELS" cmd workers`.

Brief goal, files, acceptance, check, base SHA, dependencies and report format. No bare "continue". Workers implement/check/commit using Debug, Perf or Verify as appropriate. Return `task | SHA | files | check + result | assumptions`.

Missing reports get one fresh attempt after the old writer stops; another miss is a gap. Skip dependents and preserve work.

## 3. Review each task

Independent `reviewer` uses `../kstack-review/SKILL.md` at frozen base/head. Include scope/regression audit for one-task final-lane reuse. FAIL returns to worker; block after `execution.max_fails` and skip dependents. BLOCKED is not a strike; retry after environment repair, otherwise partial. Reviewers never fix.

## 4. Integrate

Pause worker; serially rebase, rerun task checks and fast-forward. Worker resolves conflicts; reviewer checks. Record reviewed final worker tip after rebase, review/check evidence and integration SHA; unlock dependents.

Account for every started agent and task as integrated, blocked or skipped before freezing head. Prove `git merge-base --is-ancestor <worker-tip> <frozen-head>`, not PR-head equality. Retain advanced/unintegrated refs. Renew proof after rewrites or retain. Unfinished tasks mean partial.

## 5. Verification swarm

Finish also uses this without rebuilding. Supply request, exact base/head, acceptance, scenarios/pass conditions, commands and prior outcomes. Infer missing scenarios from diff/repo; never invent PASS.

Independent lanes use `git worktree add --detach <path> <sha>` at frozen head and `python3 "$MODELS" cmd verifiers --index <lane>`:

| Lane | Evidence |
|---|---|
| Audit | Two focused Review contexts |
| Gates | Full checks/lint/typecheck once at head; coordinator may run |
| Live | Verify every changed user-visible behavior; compare one main scenario to base |
| Perf | Measure speed targets without editing |

Reuse one-task review as one audit only at matching base/head and scope. Gates require identical SHA, commands and environment; audits need not repeat unrelated suites.

Return `base SHA | head SHA | PASS/FAIL/BLOCKED | commands | evidence`. Missing evidence gets one retry then gap. N/A needs reason. Existing defects belong to base unless copied, worsened or newly exposed.

Execute repairs through steps 2–4 with one swarm repair round, then stops partial. Finish uses its own `finish.max_fix_rounds`. Small repairs/rebases need one independent verifier to inspect diff, rerun gates and affected/failed scenarios, and justify reuse. New behavior/large diffs require full swarm within budget.

## 6. Report

Chat task/SHA/check/verdict, lanes, findings and checks not run. Complete needs acceptance, required lanes and shared scratch cleanup under Finish safety/readback. Clean idle disposable verifiers; may stop own idle agents. Preserve unmerged delivery branch/worktree. Separate delivery-resource/diagnostic cleanup status.
